from django.utils import timezone
import pytz


def make_utc(dt):
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt.astimezone(pytz.utc)

