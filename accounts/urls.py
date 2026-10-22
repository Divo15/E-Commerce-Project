from django.urls import path

from . import views
from . import google_auth
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

app_name = 'accounts'

urlpatterns = [
    path('google/start/', google_auth.start, name='google_start'),
    path('google/callback/', google_auth.callback, name='google_callback'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('', views.account, name='account'),
    path('details/', views.details, name='details'),
    path('verification-sent/', views.verification_sent, name='verification_sent'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/sent/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/reset_confirm.html', success_url=reverse_lazy('accounts:password_reset_complete')), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/message.html', extra_context={'title': 'Password reset complete', 'body': 'Your new password is saved. Sign in to continue.'}), name='password_reset_complete'),
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/complete/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/message.html', extra_context={'title': 'Password updated', 'body': 'Your password is saved. You are still signed in on this device.'}), name='password_change_done'),
]
