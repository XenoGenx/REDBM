from datetime import date, datetime

from django import template
from django.utils import timezone


register = template.Library()
MONTHS = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']


@register.filter
def thai_date(value):
    if isinstance(value, datetime):
        value = timezone.localtime(value).date()
    if not isinstance(value, date):
        return ''
    return f'{value.day} {MONTHS[value.month - 1]} {value.year + 543}'