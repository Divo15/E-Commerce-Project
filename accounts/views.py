from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import RegistrationForm
from carts.models import Cart


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegistrationForm(request.POST if request.method == 'POST' else None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('accounts:login')

    return render(request, 'register.html', {'form': form})


@require_POST
def logout(request):
    auth_logout(request)
    return redirect('accounts:login')


def login(request):
    if request.user.is_authenticated:
        return redirect('home')

    error_message = None

    if request.method == 'POST':
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
                    if old_session_key:
                        Cart.objects.filter(cart_id=old_session_key).update(
                            cart_id=request.session.session_key,
                        )
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
