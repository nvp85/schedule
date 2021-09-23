from django.utils import timezone
import pytz
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied


def make_utc(dt):
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt.astimezone(pytz.utc)


def get_invite_or_403(uuid):
    from .models import Invitation
    invite = get_object_or_404(Invitation, uuid=uuid)
    if not invite.is_active:
        raise PermissionDenied("Sorry, the invitation is expired!")
    return invite
