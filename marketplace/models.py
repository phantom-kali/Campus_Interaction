from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta


class Like(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="marketplace_likes"
    )
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "user",
            "item",
        )  # Ensures that each user can only like an item once

    def __str__(self):
        return f"{self.user.username} liked {self.item.title}"


# Category model
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Item model
class Item(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField()
    specification = models.TextField(
        null=True, blank=True
    )  # Make specification optional
    brand = models.CharField(
        max_length=50, null=True, blank=True
    )  # Make brand optional
    price = models.IntegerField()  # Price as integer (the current price)
    original_price = models.IntegerField(
        null=True, blank=True
    )  # The original price when the item was first added
    new_price = models.IntegerField(
        null=True, blank=True
    )  # The new price, can be updated by the seller
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="item_images/")  # Main image
    created_at = models.DateTimeField(auto_now_add=True)
    sold = models.BooleanField(default=False)
    sold_date = models.DateTimeField(
        null=True, blank=True
    )  # Date when the item was sold

    likes = models.ManyToManyField(User, through=Like, related_name="liked_items")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Set the original price when creating the item, if not provided
        if self.original_price is None:
            self.original_price = self.price

        # Automatically set sold_date when the item is marked as sold
        if self.sold and not self.sold_date:
            self.sold_date = timezone.now()

        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        avg = self.ratings.aggregate(Avg("stars"))["stars__avg"]
        return avg if avg is not None else 0.0

    @property
    def effective_price(self):
        """Returns the current price if a new price is set, otherwise the original price."""
        return self.new_price if self.new_price else self.price

    @property
    def is_deal(self):
        return self.effective_price < self.original_price

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return round(discount, 2)
        return 0.0

    @property
    def total_likes(self):
        return self.likes.count()


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    @property
    def total_items(self):
        """Returns the total number of items in the cart."""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Calculates the total price of all items in the cart."""
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    @property
    def total_price(self):
        """Returns the total price for this cart item based on quantity."""
        return self.quantity * self.item.effective_price


class ItemImage(models.Model):
    item = models.ForeignKey(
        "Item", on_delete=models.CASCADE, related_name="additional_images"
    )
    image = models.ImageField(upload_to="item_images/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.item.title}"


class Notification(models.Model):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="marketplace_notifications"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Adding a ForeignKey to Item if each notification is related to a specific item
    item = models.ForeignKey("Item", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.recipient.username}"

    def has_expired(self):
        # Returns True if the notification is older than 24 hours
        return timezone.now() > self.created_at + timedelta(hours=24)

    def time_remaining(self):
        now = timezone.now()
        time_diff = (
            now - self.created_at
        )  # Time difference between now and notification creation

        if time_diff.total_seconds() <= 0:
            return "Just posted"

        seconds = time_diff.total_seconds()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        # Return the time in "X hrs X min ago" format
        return f"Posted {int(hours)} hour{'s' if hours != 1 else ''} {int(minutes)} minute{'s' if minutes != 1 else ''} ago"


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=200)
    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Search by {self.user.username}: {self.query}"


class UserRating(models.Model):
    item = models.ForeignKey(Item, related_name="ratings", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stars = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating by {self.user.username} for {self.item.title}"
