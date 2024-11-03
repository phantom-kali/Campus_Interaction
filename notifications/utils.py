def get_notification_types():
    # Import and gather notification types from each app
    return [
        ("message", "New Message"),
        ("comment", "New Comment"),
        ("like", "New Like"),
        ("follow", "New  Follow"),
        ("forum", "New Forum"),
        ("Event", "New Event"),
        ("poll", "New Poll"),
    ]
