from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


def send_account_activation_email(email, email_token):
    subject = 'Verify your account'
    email_from = settings.EMAIL_HOST_USER
    activation_url = f'{settings.SITE_URL}{reverse("activate_email", args=[email_token])}'
    message = f'Use this link to activate your account: {activation_url}'
    send_mail(subject, message, email_from, [email])