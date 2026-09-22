from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy.orm import Session
import requests

from database import get_db
from enums import PaymentStatus, PaymentMethod, TripStatus
from models import Users, Trip, Payment, AmbulanceRequest
from utils.auth import user_dependency
from utils.sslcommerz import initiate_payment
from utils.payment_receipt import create_payment_receipt
from utils.cloudinary_service import upload_payment_receipt
from utils.email_sending import send_email
from config import settings
from utils.auth import admin_dependency

router = APIRouter()
db_dependency = Annotated[Session, Depends(get_db)]


def validate_payment(val_id: str):
    base_url = settings.sslcommerz_base_url.rstrip("/")
    base_url = base_url.removesuffix("/gwprocess/v4/api.php")
    url = f"{base_url}/validator/api/validationserverAPI.php"

    params = {
        "val_id": val_id,
        "store_id": settings.sslcommerz_store_id,
        "store_passwd": settings.sslcommerz_store_password,
        "format": "json",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


@router.post("/create/{id}", summary="Create a payment for a trip")
def create_payment(
    db: db_dependency,
    current_user: user_dependency,
    id: int = Path(
        description="The ID of the trip for which the payment is being created"
    ),
):
    # 1. Get trip
    trip = db.query(Trip).filter(Trip.id == id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    # 2. Make sure this passenger owns the trip
    if trip.passenger_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot pay for this trip",
        )

    # 3. Check trip status
    if trip.status not in [
        TripStatus.ONGOING,
        TripStatus.COMPLETED,
    ]:
        raise HTTPException(
            status_code=400,
            detail=("Payment is only available " "for ongoing or completed trips"),
        )

    # 4. Reuse the one payment row allowed for each trip
    existing_payment = db.query(Payment).filter(Payment.trip_id == trip.id).first()

    if existing_payment:
        if existing_payment.status == PaymentStatus.SUCCESS:
            raise HTTPException(
                status_code=400, detail="This trip has already been paid"
            )

        if existing_payment.status == PaymentStatus.PENDING:
            raise HTTPException(
                status_code=409,
                detail="A payment is already in progress for this trip",
            )

    # 5. Get passenger
    passenger = db.query(Users).filter(Users.id == current_user.id).first()

    if not passenger:
        raise HTTPException(
            status_code=404,
            detail="Passenger not found",
        )

    # 6. Create unique transaction ID
    transaction_id = f"TRIP-{trip.id}-" f"{int(datetime.now().timestamp())}"

    # 7. Create a payment or retry a previous failed/cancelled payment
    if existing_payment:
        payment = existing_payment
        payment.passenger_id = passenger.id
        payment.amount = trip.fare
        payment.payment_method = PaymentMethod.SSLCOMMERZ
        payment.status = PaymentStatus.PENDING
        payment.transaction_id = transaction_id
        payment.ssl_session_key = None
    else:
        payment = Payment(
            trip_id=trip.id,
            passenger_id=passenger.id,
            amount=trip.fare,
            payment_method=PaymentMethod.SSLCOMMERZ,
            status=PaymentStatus.PENDING,
            transaction_id=transaction_id,
        )
        db.add(payment)

    db.commit()
    db.refresh(payment)

    # 8. Initialize SSLCommerz
    try:
        ssl_response = initiate_payment(
            transaction_id=transaction_id,
            amount=trip.fare,
            customer_name=(f"{passenger.firstname} " f"{passenger.lastname}"),
            customer_email=passenger.email,
        )
    except Exception:
        payment.status = PaymentStatus.FAILED

        db.commit()

        raise HTTPException(
            status_code=500,
            detail="Failed to initialize payment",
        )

    # 9. Check SSLCommerz response
    if ssl_response.get("status") != "SUCCESS":
        payment.status = PaymentStatus.FAILED

        db.commit()

        raise HTTPException(
            status_code=400,
            detail=(
                "SSLCommerz payment initialization failed: "
                f"{ssl_response.get('failedreason', 'Unknown gateway error')}"
            ),
        )

    # 10. Save session key
    payment.ssl_session_key = ssl_response.get("sessionkey")

    db.commit()

    return {
        "message": "Payment initialized successfully",
        "payment_id": payment.id,
        "transaction_id": payment.transaction_id,
        "payment_url": ssl_response.get("GatewayPageURL"),
    }


@router.post("/success")
async def payment_success(
    request: Request,
    db: db_dependency,
):
    form_data = await request.form()

    val_id = form_data.get("val_id")
    tran_id = form_data.get("tran_id")

    if not val_id or not tran_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment response",
        )

    payment = db.query(Payment).filter(Payment.transaction_id == tran_id).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    # Validate with SSLCommerz
    validation = validate_payment(val_id)

    if validation.get("status") != "VALID":
        payment.status = PaymentStatus.FAILED

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Payment validation failed",
        )

    # Verify transaction ID
    if validation.get("tran_id") != payment.transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID mismatch",
        )

    # Verify amount using exact currency precision.
    try:
        validated_amount = Decimal(str(validation.get("amount", "0"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        payment_amount = Decimal(str(payment.amount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, TypeError, ValueError):
        payment.status = PaymentStatus.FAILED

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid payment amount",
        )

    if validated_amount != payment_amount:
        payment.status = PaymentStatus.FAILED

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Payment amount mismatch",
        )

    # Prevent duplicate processing
    if payment.status == PaymentStatus.SUCCESS:
        return {"message": "Payment already processed"}

    # Get passenger
    passenger = db.query(Users).filter(Users.id == payment.passenger_id).first()

    if not passenger:
        raise HTTPException(
            status_code=404,
            detail="Passenger not found",
        )

    # Get trip
    trip = db.query(Trip).filter(Trip.id == payment.trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    # Get request
    ambulance_request = (
        db.query(AmbulanceRequest)
        .filter(AmbulanceRequest.id == trip.request_id)
        .first()
    )

    if not ambulance_request:
        raise HTTPException(
            status_code=404,
            detail="Ambulance request not found",
        )

    # Update payment
    payment.status = PaymentStatus.SUCCESS
    payment.paid_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(payment)

    # Generate PDF
    pdf_file = create_payment_receipt(
        payment=payment,
        trip=trip,
        request=ambulance_request,
        passenger=passenger,
    )

    # Upload PDF to Cloudinary
    pdf_url = upload_payment_receipt(
        pdf_file=pdf_file,
        payment_id=payment.id,
    )

    # Save Cloudinary URL
    payment.receipt_url = pdf_url

    db.commit()

    # Get PDF bytes for email
    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()

    # Send email
    email_body = f"""
Hello {passenger.firstname},

Your ambulance trip payment was successful.

Payment ID: {payment.id}
Transaction ID: {payment.transaction_id}
Trip ID: {trip.id}
Amount: {payment.amount:.2f} BDT

Your payment receipt is attached to this email.

Regards,
Ambulance Management System
"""

    try:
        send_email(
            recipient_email=passenger.email,
            subject="Ambulance Payment Successful",
            body=email_body,
            attachment=pdf_bytes,
            attachment_name=(f"payment_receipt_{payment.id}.pdf"),
        )
    except Exception as e:
        print(
            "Payment receipt email error:",
            repr(e),
        )

    return {
        "message": "Payment successful",
        "payment_id": payment.id,
        "transaction_id": payment.transaction_id,
        "amount": payment.amount,
        "receipt_url": payment.receipt_url,
    }


@router.post("/cancel")
async def payment_cancel(
    request: Request,
    db: db_dependency,
):
    form_data = await request.form()

    tran_id = form_data.get("tran_id")

    if not tran_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID is required",
        )

    payment = db.query(Payment).filter(Payment.transaction_id == tran_id).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.status == PaymentStatus.SUCCESS:
        return {"message": "Payment has already been completed"}

    payment.status = PaymentStatus.CANCELLED

    db.commit()

    return {
        "message": "Payment cancelled",
        "payment_id": payment.id,
        "transaction_id": payment.transaction_id,
    }


@router.post("/fail")
async def payment_fail(
    request: Request,
    db: db_dependency,
):
    form_data = await request.form()

    tran_id = form_data.get("tran_id")

    if not tran_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID is required",
        )

    payment = db.query(Payment).filter(Payment.transaction_id == tran_id).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.status == PaymentStatus.SUCCESS:
        return {"message": "Payment already completed"}

    payment.status = PaymentStatus.FAILED

    db.commit()

    return {
        "message": "Payment failed",
        "payment_id": payment.id,
        "transaction_id": payment.transaction_id,
    }


@router.get("/all")
def get_all_payments(
    db: db_dependency,
    _: admin_dependency,
):
    payments = db.query(Payment).all()

    return {
        "message": "Payments retrieved successfully",
        "payments": payments,
    }
