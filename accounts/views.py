from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.conf import settings
from urllib.parse import urlsplit
import logging
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import RegistrationForm, CustomerDetailsForm
from .models import Account
from .lifecycle import allow_request, send_verification, verification_tokens
from carts.services import get_cart, merge_guest_cart

logger = logging.getLogger(__name__)


def rate_limited(request):
    response = render(request, 'accounts/message.html', {'title': 'Please try again later', 'body': 'Too many requests. Please wait before trying again.'}, status=429)
    response['Retry-After'] = '3600'
    return response


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegistrationForm(request.POST if request.method == 'POST' else None)

    if request.method == 'POST' and form.is_valid():
        if not allow_request(request, 'register'):
            return rate_limited(request)
        try:
            with transaction.atomic():
                user = form.save()
                send_verification(request, user)
        except Exception:
            logger.error('Account verification email could not be sent.')
            form.add_error(None, 'We could not send the verification email. Please try again shortly.')
        else:
            return redirect('accounts:verification_sent')

    return render(request, 'register.html', {
        'form': form,
        'registration_groups': [
            {'title': 'Your details', 'fields': [form[name] for name in (
                'first_name', 'last_name', 'email', 'phone_number',
            )]},
            {'title': 'Your location', 'fields': [form[name] for name in ('city', 'postal_code')]},
            {'title': 'Set a password', 'fields': [form[name] for name in ('password', 'confirm_password')]},
        ],
    })


@require_POST
def logout(request):
    if request.user.is_authenticated:
        get_cart(request)  # Attach any legacy bag before the session is cleared.
    auth_logout(request)
    return redirect('accounts:login')


@never_cache
def login(request):
    if request.user.is_authenticated:
        return redirect('home')

    error_message = None

    if request.method == 'POST':
        if not allow_request(request, 'login', limit=20, minutes=15):
            return rate_limited(request)
        email = request.POST.get('email', '').strip()
        if not email:
            email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            error_message = 'Email and password are required.'
        else:
            user = authenticate(request, username=email, password=password)

            if user is not None:
                # Django rotates the session key at login; carry the guest bag along.
                old_session_key = request.session.session_key
                with transaction.atomic():
                    auth_login(request, user)
                    merge_guest_cart(user, old_session_key, request.session.session_key)
                next_url = request.POST.get('next') or request.GET.get('next')

                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)

                return redirect('home')

            error_message = 'Invalid email or password.'

    return render(
        request,
        'signin.html',
        {
            'error_message': error_message,
            'email': request.POST.get('email', request.POST.get('username', '')).strip(),
            'next_url': request.POST.get('next', request.GET.get('next', '')),
        },
    )


@login_required
@never_cache
def account(request):
    return render(request, 'accounts/account.html')


@login_required
@never_cache
def details(request):
    next_url = request.POST.get('next') or request.GET.get('next') or reverse_lazy('accounts:account')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = reverse_lazy('accounts:account')
    form = CustomerDetailsForm(request.POST if request.method == 'POST' else None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect(next_url)
    return render(request, 'accounts/details.html', {'form': form, 'next_url': next_url})


@never_cache
def verification_sent(request):
    return email_confirmation(request, 'Open the verification link we sent to finish creating your account. The link expires in one hour.', resend=True)


def email_confirmation(request, body, resend=False):
    local_only = settings.EMAIL_BACKEND in {
        'django.core.mail.backends.filebased.EmailBackend',
        'django.core.mail.backends.console.EmailBackend',
        'django.core.mail.backends.locmem.EmailBackend',
        'django.core.mail.backends.dummy.EmailBackend',
    }
    return render(request, 'accounts/message.html', {
        'title': 'Check your email', 'body': body, 'resend': resend,
        'local_email_delivery': local_only,
    })


@never_cache
def password_reset_done(request):
    return email_confirmation(request, 'If an active account matches that email, a password reset link is on its way. Check your spam folder too. The link expires in one hour.')


@never_cache
def verify_email(request, uidb64, token):
    try:
        user = Account.objects.get(pk=urlsafe_base64_decode(uidb64).decode())
    except (Account.DoesNotExist, ValueError, TypeError, OverflowError, UnicodeDecodeError):
        user = None
    valid = user and user.email_verification_pending and not user.is_active and verification_tokens.check_token(user, token)
    if not valid:
        return render(request, 'accounts/message.html', {'title': 'This link is no longer valid', 'body': 'The verification link has expired or has already been used. Request another email if you still need to verify your account.', 'resend': True}, status=400)
    if request.method == 'POST':
        # Recheck under a transaction so concurrent uses cannot both activate.
        with transaction.atomic():
            user = Account.objects.select_for_update().get(pk=user.pk)
            if not user.email_verification_pending or not verification_tokens.check_token(user, token):
                return render(request, 'accounts/message.html', {'title': 'This link is no longer valid', 'body': 'Sign in or request a new verification email.', 'resend': True}, status=400)
            user.is_active = True
            user.email_verification_pending = False
            user.email_verified_at = timezone.now()
            user.save(update_fields=['is_active', 'email_verification_pending', 'email_verified_at'])
        return render(request, 'accounts/message.html', {'title': 'Your email is verified', 'body': 'Your account is ready. Sign in to continue shopping.'})
    return render(request, 'accounts/verify.html')


@never_cache
def resend_verification(request):
    if request.method == 'POST':
        if not allow_request(request, 'resend-verification'):
            return rate_limited(request)
        user = Account.objects.filter(email__iexact=request.POST.get('email', '').strip(), email_verification_pending=True, is_active=False).first()
        try:
            if user:
                send_verification(request, user)
        except Exception:
            logger.error('Verification resend could not be sent.')
            return render(request, 'accounts/message.html', {'title': 'Email is temporarily unavailable', 'body': 'Please try again shortly.', 'resend': True}, status=503)
        return email_confirmation(request, 'If that address has an account awaiting verification, we have sent a verification link.', resend=True)
    return render(request, 'accounts/email_form.html', {'title': 'Resend verification email', 'intro': 'Enter the email address you registered with.', 'button': 'Send verification link'})


class ResetEmailForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        subject = ''.join(render_to_string(subject_template_name, context).splitlines())
        send_mail(subject, render_to_string(email_template_name, context), from_email, [to_email])


@method_decorator(never_cache, name='dispatch')
class PasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/password_form.html'
    email_template_name = 'accounts/password_reset_email.txt'
    subject_template_name = 'accounts/password_reset_subject.txt'
    form_class = ResetEmailForm
    success_url = reverse_lazy('accounts:password_reset_done')
    extra_context = {'title': 'Reset your password', 'intro': 'Enter your email and we will send a password reset link.', 'button': 'Send reset link'}

    def post(self, request, *args, **kwargs):
        if not allow_request(request, 'password-reset'):
            return rate_limited(request)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            if settings.ACCOUNT_PUBLIC_ORIGIN:
                origin = urlsplit(settings.ACCOUNT_PUBLIC_ORIGIN)
                self.extra_email_context = {'protocol': origin.scheme, 'domain': origin.netloc}
            return super().form_valid(form)
        except Exception:
            logger.error('Password reset email could not be sent.')
            form.add_error(None, 'We could not send email just now. Please try again shortly.')
            return self.form_invalid(form)


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'accounts/password_form.html'
    success_url = reverse_lazy('accounts:password_change_done')
    extra_context = {'title': 'Change your password', 'button': 'Save new password'}

    def form_valid(self, form):
        get_cart(self.request)
        with transaction.atomic():
            response = super().form_valid(form)
        return response
