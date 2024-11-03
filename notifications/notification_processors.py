from .views import NotificationManager

def unread_notifications_count(request):
    if request.user.is_authenticated:
        notification_manager = NotificationManager(request.user)
        unread_count = len(notification_manager)  # Counts unread notifications
    else:
        unread_count = 0

    return {'unread_notifications_count': unread_count}
