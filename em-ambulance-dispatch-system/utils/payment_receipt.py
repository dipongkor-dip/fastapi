from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def create_payment_receipt(
    payment,
    trip,
    request,
    passenger,
):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "Ambulance Management System",
            styles["Title"],
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Payment Receipt",
            styles["Heading2"],
        )
    )

    elements.append(Spacer(1, 15))

    data = [
        ["Payment ID", str(payment.id)],
        ["Transaction ID", payment.transaction_id or ""],
        ["Trip ID", str(trip.id)],
        ["Passenger", passenger.username],
        ["Email", passenger.email],
        ["Pickup", request.pickup_location],
        ["Destination", request.destination],
        ["Amount", f"{payment.amount:.2f} BDT"],
        ["Payment Status", payment.status.value],
        ["Payment Method", payment.payment_method.value],
    ]

    table = Table(
        data,
        colWidths=[150, 300],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(table)

    elements.append(Spacer(1, 30))

    elements.append(
        Paragraph(
            "Thank you for using our Ambulance Management System.",
            styles["Normal"],
        )
    )

    document.build(elements)

    buffer.seek(0)

    return buffer
