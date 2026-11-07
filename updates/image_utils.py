from io import BytesIO
from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_IMAGE_SIDE = 1600


def prepare_image(uploaded_file):
    if uploaded_file.size > MAX_IMAGE_SIZE:
        raise ValidationError('รูปภาพต้องมีขนาดไม่เกิน 10 MB')

    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as source:
            image = ImageOps.exif_transpose(source)
            image.load()
            image = image.convert('RGB')
            image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValidationError('ไฟล์นี้ไม่ใช่รูปภาพที่รองรับ') from None
    finally:
        uploaded_file.seek(0)

    return f'{uuid4().hex}.jpg', ContentFile(output.getvalue())