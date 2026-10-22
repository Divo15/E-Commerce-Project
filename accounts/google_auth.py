"""Google authorization-code sign-in. Google passwords/tokens are never stored."""
import base64
import hashlib
import json
import logging
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

import requests
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.id_token import verify_oauth2_token

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from carts.services import merge_guest_cart
from .forms import CustomerDetailsForm
from .lifecycle import allow_request
from .models import Account

logger = logging.getLogger(__name__)
# Google's verifier supports a bounded tolerance for clocks a few seconds apart.
TOKEN_CLOCK_SKEW_SECONDS = 30


def failure_reason(error, stage):
    if stage == 'token_exchange' and isinstance(error, requests.HTTPError):
        try:
            provider_error = error.response.json().get('error')
            if provider_error in {'invalid_client', 'invalid_grant', 'invalid_request', 'unauthorized_client'}:
                return provider_error
        except (ValueError, AttributeError, TypeError):
            pass
    if stage == 'token_verification':
        message = str(error)
        if message.startswith('Token used too early'):
            return 'token_issued_in_future'
        if message.startswith('Token expired'):
            return 'token_expired'
    if stage == 'account_resolution':
        if isinstance(error, IntegrityError):
            return 'account_data_conflict'
        if str(error) == 'This store account is inactive. Please contact the store.':
            return 'account_inactive'
        if str(error) == 'Sign in to your existing store account first, then connect Google from Your account.':
            return 'account_link_required'
    return 'rejected'


def credentials():
    config = {}
    try:
        path = Path(settings.GOOGLE_OAUTH_CONFIG_FILE)
        if path.is_file():
            payload = json.loads(path.read_text(encoding='utf-8'))
            config = payload.get('web', {})
            if not isinstance(config, dict):
                config = {}
    except (OSError, ValueError, AttributeError):
        pass
    return (settings.GOOGLE_CLIENT_ID or config.get('client_id', ''), settings.GOOGLE_CLIENT_SECRET or config.get('client_secret', ''))


def google_context(request):
    client_id, client_secret = credentials()
    return {'google_signin_enabled': bool(client_id and client_secret)}


def failure(request, message, status=400):
    return render(request, 'accounts/message.html', {'title': 'Google sign-in could not finish', 'body': message}, status=status)


def safe_next(request, value):
    if value and url_has_allowed_host_and_scheme(value, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return value
    return reverse('accounts:account')


def callback_uri(request):
    origin = settings.ACCOUNT_PUBLIC_ORIGIN.rstrip('/')
    if origin and urlsplit(origin).netloc == request.get_host():
        return origin + reverse('accounts:google_callback')
    return request.build_absolute_uri(reverse('accounts:google_callback'))


@never_cache
@require_POST
def start(request):
    client_id, client_secret = credentials()
    if not client_id or not client_secret:
        return failure(request, 'Google sign-in is not available yet. Please try again once the store has connected it.', status=503)
    if not allow_request(request, 'google-signin', limit=30, minutes=15):
        return failure(request, 'Too many sign-in attempts. Please wait and try again.', status=429)
    verifier = secrets.token_urlsafe(64)
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    uri = callback_uri(request)
    request.session['google_signin'] = {
        'state': state, 'nonce': nonce, 'verifier': verifier,
        'started': time.time(), 'redirect_uri': uri,
        'next': safe_next(request, request.POST.get('next', '')),
        'link_user_id': request.user.pk if request.user.is_authenticated else None,
    }
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    return redirect('https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
        'client_id': client_id, 'redirect_uri': uri, 'response_type': 'code',
        'scope': 'openid email profile', 'state': state, 'nonce': nonce,
        'code_challenge': challenge, 'code_challenge_method': 'S256', 'prompt': 'select_account',
    }))


def google_request(url, method='GET', body=None, headers=None, **kwargs):
    kwargs.pop('timeout', None)
    return Request()(url=url, method=method, body=body, headers=headers, timeout=10, **kwargs)


@transaction.atomic
def account_for_claims(claims, linking_user_id):
    subject = claims.get('sub')
    email = claims.get('email', '').strip().lower()
    if not isinstance(subject, str) or not subject or len(subject) > 255 or claims.get('email_verified') is not True or len(email) > 100:
        raise ValueError('Google did not provide a verified account identity.')
    validate_email(email)
    user = Account.objects.select_for_update().filter(google_subject=subject).first()
    if user:
        if not user.is_active or (linking_user_id and user.pk != linking_user_id):
            raise ValueError('This Google account cannot sign in to this store account.')
        return user
    user = Account.objects.select_for_update().filter(email__iexact=email).first()
    authoritative = email.endswith('@gmail.com') or bool(claims.get('hd'))
    if user:
        if linking_user_id and user.pk != linking_user_id:
            raise ValueError('Sign in with the Google account matching your store account.')
        if user.google_subject:
            raise ValueError('This store account is already connected to another Google identity.')
        if not authoritative and linking_user_id != user.pk:
            raise ValueError('Sign in to your existing store account first, then connect Google from Your account.')
        if not user.is_active and not user.email_verification_pending:
            raise ValueError('This store account is inactive. Please contact the store.')
        if user.email_verification_pending:
            # An unverified signup must not retain a password set by someone else.
            user.set_unusable_password()
    else:
        if linking_user_id:
            raise ValueError('Sign in with the Google account matching your store account.')
        user = Account(email=email, username=f'customer_{uuid4().hex}', first_name=str(claims.get('given_name') or claims.get('name') or '')[:50], last_name=str(claims.get('family_name') or '')[:50])
        user.set_unusable_password()
    user.google_subject = subject
    user.is_active = True
    user.email_verification_pending = False
    user.email_verified_at = timezone.now() if authoritative else user.email_verified_at
    user.save()
    return user


@never_cache
@require_GET
def callback(request):
    attempt = request.session.pop('google_signin', None)
    # Consume before exchanging the one-time authorization code; never echo tokens.
    if not attempt or not secrets.compare_digest(str(request.GET.get('state', '')), str(attempt.get('state', ''))) or not 0 <= time.time() - attempt.get('started', 0) <= 600:
        return failure(request, 'This sign-in request expired or is invalid. Please start again.')
    if request.GET.get('error'):
        return failure(request, 'Google sign-in was cancelled. You can try again when you are ready.')
    code = request.GET.get('code')
    client_id, client_secret = credentials()
    current_user = request.user.pk if request.user.is_authenticated else None
    if not code or not client_id or not client_secret or current_user != attempt.get('link_user_id'):
        return failure(request, 'Please start Google sign-in again.')
    stage = 'token_exchange'
    try:
        response = requests.post('https://oauth2.googleapis.com/token', data={
            'code': code, 'client_id': client_id, 'client_secret': client_secret,
            'redirect_uri': attempt['redirect_uri'], 'grant_type': 'authorization_code',
            'code_verifier': attempt['verifier'],
        }, timeout=15)
        response.raise_for_status()
        token = response.json().get('id_token')
        if not token:
            raise ValueError('No identity token returned.')
        stage = 'token_verification'
        claims = verify_oauth2_token(token, google_request, audience=client_id, clock_skew_in_seconds=TOKEN_CLOCK_SKEW_SECONDS)
        stage = 'nonce_validation'
        if not secrets.compare_digest(str(claims.get('nonce', '')), attempt['nonce']):
            raise ValueError('Invalid sign-in nonce.')
        with transaction.atomic():
            stage = 'account_resolution'
            user = account_for_claims(claims, current_user)
            old_key = request.session.session_key
            stage = 'session_login'
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            stage = 'cart_merge'
            merge_guest_cart(user, old_key, request.session.session_key)
    except (requests.RequestException, GoogleAuthError, ValueError, ValidationError, IntegrityError, TypeError) as error:
        # Never log exception text, URLs, claims, tokens, codes, or credentials.
        logger.warning('Google sign-in failed: stage=%s reason=%s error_type=%s', stage, failure_reason(error, stage), type(error).__name__)
        return failure(request, 'We could not connect this Google account. Try again, or sign in to your existing store account first to connect it.')
    next_url = safe_next(request, attempt.get('next'))
    profile = CustomerDetailsForm({name: getattr(user, name) for name in CustomerDetailsForm.Meta.fields}, instance=user)
    if not profile.is_valid():
        return redirect(reverse('accounts:details') + '?' + urlencode({'next': next_url}))
    return redirect(next_url)
