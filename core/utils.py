import qrcode
from django.core.files import File
from io import BytesIO


def generate_qr(profile, url):
    qr = qrcode.make(url)

    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    profile.qr_code.save(
        f"{profile.unique_id}.png",
        File(buffer),
        save=False
    )
