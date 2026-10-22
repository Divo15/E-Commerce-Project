import hashlib
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import AccountRequestLimit


class VerificationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = 'shali.accounts.email-verification'

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}:{user.email}:{user.password}:{user.is_active}:{user.email_verification_pending}:{timestamp}'


verification_tokens = VerificationTokenGenerator()


def allow_request(request, action, *, limit=5, minutes=60):
    # Ignore client-supplied forwarding headers; this identity is set by the server.
    ip = request.META.get('REMOTE_ADDR', '')
    email = request.POST.get('email', request.POST.get('username', '')).strip().casefold()
    now = timezone.now()
    keys = [hashlib.sha256(f'{action}:ip:{ip}'.encode()).hexdigest()]
    if email:
        keys.append(hashlib.sha256(f'{action}:email:{email}'.encode()).hexdigest())
    with transaction.atomic():
        for key in keys:
            row, _ = AccountRequestLimit.objects.get_or_create(key=key, defaults={'started_at': now})
            AccountRequestLimit.objects.filter(pk=row.pk, started_at__lte=now - timedelta(minutes=minutes)).update(started_at=now, count=0)
            if not AccountRequestLimit.objects.filter(pk=row.pk, count__lt=limit).update(count=F('count') + 1):
                return False
    return True


def send_verification(request, user):
    path = reverse('accounts:verify_email', args=[urlsafe_base64_encode(force_bytes(user.pk)), verification_tokens.make_token(user)])
    origin = settings.ACCOUNT_PUBLIC_ORIGIN.rstrip('/')
    link = origin + path if origin else request.build_absolute_uri(path)
    send_mail('Verify your Shali Collections email', render_to_string('accounts/verification_email.txt', {'user': user, 'link': link}), settings.DEFAULT_FROM_EMAIL, [user.email])
