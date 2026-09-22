import requests

from config import settings


def initiate_payment(
    transaction_id: str,
    amount: float,
    customer_name: str,
    customer_email: str,
):
    base_url = settings.sslcommerz_base_url.rstrip("/")
    if base_url.endswith("/gwprocess/v4/api.php"):
        url = base_url
    else:
        url = f"{base_url}/gwprocess/v4/api.php"

    payload = {
        "store_id": settings.sslcommerz_store_id,
        "store_passwd": settings.sslcommerz_store_password,
        "total_amount": amount,
        "currency": "BDT",
        "tran_id": transaction_id,
        "success_url": (f"{settings.backend_url}/api/v1/payments/success"),
        "fail_url": (f"{settings.backend_url}/api/v1/payments/fail"),
        "cancel_url": (f"{settings.backend_url}/api/v1/payments/cancel"),
        "cus_name": customer_name,
        "cus_email": customer_email,
        "shipping_method": "NO",
        "product_name": "Ambulance Service",
        "product_category": "Ambulance",
        "product_profile": "general",
    }
    # "ipn_url": (f"{settings.backend_url}/api/v1/payments/ipn"),

    response = requests.post(
        url,
        data=payload,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()
