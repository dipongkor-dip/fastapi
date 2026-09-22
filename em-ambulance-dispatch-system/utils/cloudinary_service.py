import cloudinary.uploader


def upload_payment_receipt(pdf_file, payment_id: int):
    result = cloudinary.uploader.upload(
        pdf_file,
        resource_type="raw",
        public_id=f"payment_receipts/payment_{payment_id}",
        format="pdf",
    )

    return result["secure_url"]
