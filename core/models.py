import uuid
import qrcode
from io import BytesIO

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.files import File


# =========================
# Custom User
# =========================

class CustomUser(AbstractUser):

    ROLE_CHOICES = (
        ('vendor', 'Vendor'),
        ('investor', 'Investor'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15)
    aadhaar_pan = models.CharField(max_length=20)

    def __str__(self):
        return self.username


# =========================
# Vendor Profile
# =========================

class VendorProfile(models.Model):

    vendor = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False)

    document_uploaded = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)

    qr_code = models.ImageField(upload_to="qr_codes/", blank=True)

    def save(self, *args, **kwargs):

        # Generate QR only once
        if not self.qr_code:

            qr_data = f"Vendor:{self.vendor.username}|ID:{self.unique_id}"

            qr = qrcode.make(qr_data)

            buffer = BytesIO()
            qr.save(buffer, format="PNG")

            self.qr_code.save(
                f"{self.vendor.username}_qr.png",
                File(buffer),
                save=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vendor.username} Profile"


# =========================
# Vendor Documents
# =========================

class VendorDocument(models.Model):

    vendor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    file = models.FileField(upload_to="vendor_docs/")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


import uuid
from io import BytesIO
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.files import File

# You may need reportlab for PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

class Investment(models.Model):
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="investments"
    )
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_investments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    return_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    terms = models.TextField(
        default="Minimum investment ₹5000, guaranteed return 5% for 1 year"
    )
    date_invested = models.DateTimeField(default=timezone.now)
    agreement_pdf = models.FileField(upload_to="investment_agreements/", blank=True)

    def __str__(self):
        return f"{self.investor.username} → {self.vendor.username} : ₹{self.amount}"

    def save(self, *args, **kwargs):
        # Save first to get a primary key
        super().save(*args, **kwargs)

        if not self.agreement_pdf:
            # Generate PDF agreement
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(width/2, height-100, "Investment Agreement")

            p.setFont("Helvetica", 12)
            text = f"""
Investor: {self.investor.username}
Vendor: {self.vendor.username}
Amount Invested: ₹{self.amount}
Return: {self.return_percent}%
Terms: {self.terms}
Date: {self.date_invested.strftime('%d-%m-%Y')}
"""
            p.drawString(50, height-150, text)
            p.showPage()
            p.save()

            buffer.seek(0)
            self.agreement_pdf.save(
                f"investment_{self.id}.pdf",
                File(buffer),
                save=False
            )
            super().save(update_fields=["agreement_pdf"])
