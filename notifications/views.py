from django.contrib.auth.models import User
from notifications.models import Notification  # Assuming Notification model exists
from celery import shared_task

class NotificationManager:
    def __init__(self, user):
        self.user = user

    def add(self, notification_type, sender):
        """
        Add a new notification for the user.
        """
        Notification.objects.create(
            recipient=self.user,
            notification_type=notification_type,
            sender=sender
        )

    def delete(self, notification_id):
        """
        Delete a specific notification by ID.
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=self.user)
            notification.delete()
        except Notification.DoesNotExist:
            pass

    def mark_as_read(self, notification_id=None):
        """
        Mark a single notification as read by ID, or all notifications if ID is None.
        """
        if notification_id:
            Notification.objects.filter(id=notification_id, recipient=self.user).update(is_read=True)
        else:
            Notification.objects.filter(recipient=self.user, is_read=False).update(is_read=True)

    def mark_as_unread(self, notification_id=None):
        """
        Mark a single notification as unread by ID, or all notifications if ID is None.
        """
        if notification_id:
            Notification.objects.filter(id=notification_id, recipient=self.user).update(is_read=False)
        else:
            Notification.objects.filter(recipient=self.user, is_read=True).update(is_read=False)

    def get_notifications(self, read=None):
        """
        Retrieve notifications for the user.
        Set `read=True` for only read notifications, `read=False` for unread, or None for all.
        """
        if read is None:
            return Notification.objects.filter(recipient=self.user).order_by('-created_at')
        return Notification.objects.filter(recipient=self.user, is_read=read).order_by('-created_at')

    def __len__(self):
        """
        Returns the count of unread notifications.
        """
        return Notification.objects.filter(recipient=self.user, is_read=False).count()
