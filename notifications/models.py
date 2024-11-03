from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.contrib.auth.models import User
from .utils import get_notification_types

class Notification(models.Model):
    NOTIFICATION_TYPES = get_notification_types()

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    sender = models.CharField(max_length=20, default='')

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        if self.sender == '':
            return f"{self.get_notification_type_display()}"
        return f"{self.get_notification_type_display()} from {self.sender}"
