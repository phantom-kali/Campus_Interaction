from celery import shared_task
from django.contrib.auth.models import User
from .models import Notification

@shared_task
def notify_all_users(notification_type):
    """
    Send to all users.
    """
    users =  User.objects.all()
    for user in users:
        Notification.objects.create(
            recipient = user,
            notification_type = notification_type,
        )
