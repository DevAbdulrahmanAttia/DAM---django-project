from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse


def send_verification_email(user, request):
    """Build a verification link and send it to the user's email."""

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    relative_link = reverse('accounts:verify-email', kwargs={'uidb64': uidb64, 'token': token})
    verification_url = request.build_absolute_uri(relative_link)

    subject = 'Verify your email'
    message = (
        f'Hi {user.username},\n\n'
        f'Please verify your email by clicking the link below:\n{verification_url}\n\n'
        'If you did not sign up, you can ignore this email.'
    )

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

    send_mail(subject, message, from_email, [user.email], fail_silently=False)
