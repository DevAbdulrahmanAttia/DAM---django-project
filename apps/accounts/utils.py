import random
import string
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailVerificationOTP


def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def _send_email(subject, message, recipient):
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
    send_mail(subject, message, from_email, [recipient], fail_silently=False)


def issue_email_verification_otp(user):
    """Create a fresh verification OTP and email it to the user."""
    otp = generate_otp()
    EmailVerificationOTP.objects.filter(user=user).delete()
    EmailVerificationOTP.objects.create(
        user=user,
        otp=otp,
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    send_email_verification_otp_email(user, otp)
    return otp


def send_email_verification_otp_email(user, otp):
    subject = 'Verify your email'
    message = (
        f'Hi {user.username},\n\n'
        f'Your email verification code is: {otp}\n\n'
        'Enter this code in the app to verify your account.\n'
        'This code expires in 10 minutes.\n\n'
        'If you did not sign up, you can ignore this email.'
    )
    _send_email(subject, message, user.email)


def issue_password_reset_otp(user):
    """Create a fresh password-reset OTP and email it to the user."""
    from .models import PasswordResetOTP

    otp = generate_otp()
    PasswordResetOTP.objects.filter(user=user, is_verified=False).delete()
    PasswordResetOTP.objects.create(
        user=user,
        otp=otp,
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    send_password_reset_otp_email(user, otp)
    return otp


def send_password_reset_otp_email(user, otp):
    subject = 'Password reset code'
    message = (
        f'Hi {user.username},\n\n'
        f'Your password reset code is: {otp}\n\n'
        'This code expires in 10 minutes.\n'
        'If you did not request a password reset, you can ignore this email.'
    )
    _send_email(subject, message, user.email)
