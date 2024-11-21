from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core.files.base import ContentFile
from django.conf import settings
import qrcode
from datetime import timedelta
from io import BytesIO
import pytz


class Poll(models.Model):
    POLL_TYPE_CHOICES = (
        ("question", "Question"),
        ("opinion", "Opinion"),
    )

    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    poll_type = models.CharField(
        max_length=10, choices=POLL_TYPE_CHOICES, default="opinion"
    )
    background_color = models.CharField(max_length=7, default="#ffffff")  # HEX color format
    show_share_button = models.BooleanField(default=True)
    link = models.URLField(max_length=200, blank=True)  # Auto-generated unique link
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)  # Track views
    expiration_time = models.DateTimeField(null=True, blank=True)
    allow_expiration = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    banner_image = models.ImageField(upload_to="poll_banners/", blank=True, null=True)
    multi_option = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    is_archived_results = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)  # Track vote attempts

    def archive(self):
        """Toggle the archived state of the poll."""
        self.is_archived = not self.is_archived
        self.save()
    
    def archived_results(self):
        """Toggle the archived state of the poll."""
        self.is_archived_results = not self.is_archived_results
        self.save()
        
    @property
    def is_active(self):
        """Checks if the poll is still active based on expiration time and allow_expiration in Kenyan timezone."""
        now = timezone.now()
        if self.allow_expiration and self.expiration_time:
            return now < self.expiration_time
        return True  
    def check_expiration(self):
        """Check if the poll is expired and handle the redirect logic."""
        if not self.is_active:
            if self.is_public:
                return {"expired": True, "redirect": True}
            else:
                return {"expired": True, "redirect": False}
        return {"expired": False}

    def increment_view_count(self):
        """Increments the view count each time the poll is viewed."""
        self.view_count += 1
        self.save()

    def get_absolute_url(self):
        """Returns the URL for the poll's detail view."""
        return reverse("polls:vote_poll", args=[str(self.id)])

    def generate_unique_link(self):
        """Generates a unique link to the poll based on its absolute URL."""
        self.link = f"http://127.0.0.1:8000{self.get_absolute_url()}"

    def generate_qr_code(self):
        """Generates a QR code image for the poll's unique link."""
        qr = qrcode.make(self.link)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        self.qr_code.save(
            f"qr_{self.id}.png", ContentFile(buffer.getvalue()), save=False
        )

    def total_votes(self):
        """Returns the total number of votes cast for the poll."""
        return Vote.objects.filter(poll=self).count()

    def total_likes(self):
        """Returns the total number of likes for the poll."""
        return self.likes.count()

    def comment_count(self):
        """Returns the total number of comments for the poll."""
        return self.comments.count()

    def user_has_liked(self, user):
        """Checks if a specific user has liked this poll."""
        return self.likes.filter(user=user).exists()

    def __str__(self):
        return self.title

class Comment(models.Model):
    poll = models.ForeignKey(
        Poll, related_name="comments", on_delete=models.CASCADE, null=True, blank=True
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="poll_comments"
    )
    parent = models.ForeignKey(
        "self",
        related_name="subcomments",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_likes(self):
        """Returns the total number of likes for the comment or subcomment."""
        return self.comment_likes.count() 

    def comment_count(self):
        """Returns the total number of comments for the poll."""
        return self.comments.count()

    def __str__(self):
        if self.parent:
            return f"Subcomment by {self.user.username} on comment {self.parent.id}"
        return f"Comment by {self.user.username} on poll {self.poll.title}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(
        Poll, null=True, blank=True, related_name="poll_likes", on_delete=models.CASCADE
    )
    comment = models.ForeignKey(
        Comment, null=True, blank=True, related_name="comment_likes", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "poll", "comment")  # Ensures unique likes per user per poll/comment

    def __str__(self):
        if self.poll:
            return f"Like by {self.user.username} on poll {self.poll.title}"
        elif self.comment:
            return f"Like by {self.user.username} on comment {self.comment.id}"

class Option(models.Model):
    poll = models.ForeignKey(Poll, related_name="options", on_delete=models.CASCADE)
    option_text = models.CharField(
        max_length=100, blank=True
    )  
    is_correct = models.BooleanField(default=False)
    option_image = models.ImageField(
        upload_to="option_images/", blank=True, null=True
    )  

    def __str__(self):
        return (
            self.option_text or "Option without text"
        )  


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    option = models.ForeignKey(
        Option, related_name="votes", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def can_vote_again(self):
        """Determine if the user can vote again based on the poll's attempts."""
        return self.poll.attempts < 2  
