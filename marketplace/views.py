from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Item,
    UserRating,
    Category,
    SearchHistory,
    Like,
    Notification,
    ItemImage,
    Cart,
    CartItem,
)
from .forms import ItemForm, RatingForm
from django.shortcuts import render
from django.db.models import Q, F  # Import Q for complex queries
from .models import Item
from django.contrib import messages
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import Item
import json
from django.http import JsonResponse
import calendar
from django.views.decorators.http import require_POST
from datetime import timedelta
from django.db.models import Avg
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import logging
from django.http import JsonResponse
from django.db.models import F, Count, Q
from django.core.exceptions import ObjectDoesNotExist
import os

logger = logging.getLogger(__name__)


# All Items
def item_list(request):
    query = request.GET.get("q")
    items = Item.objects.all()

    # Filter items if there is a search query
    if query:
        items = items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Get the IDs of items liked by the current user
    liked_items = set(
        Like.objects.filter(user=request.user).values_list("item_id", flat=True)
    )
    # Assuming the structure: CartItem -> Cart -> User
    cart_count = CartItem.objects.filter(
        cart__user=request.user, item__sold=False
    ).count()

    # Check if the request is an AJAX request
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        items_data = [
            {
                "id": item.id,
                "title": item.title,
                "price": item.price,
                "image_url": item.image.url,
                "category": item.category.name,
                "sold": item.sold,
                "liked": item.id in liked_items,
                "total_likes": item.total_likes,
                "original_price": item.original_price,
                "new_price": item.new_price,
            }
            for item in items
        ]
        return JsonResponse({"items": items_data})

    # For non-AJAX requests (initial load)
    categories = Category.objects.all()
    deal_items = Item.objects.filter(
        new_price__lt=F("original_price"),
        new_price__isnull=False,
        original_price__isnull=False,
        sold=False,
    )

    # Feature items - Items where the new price is less than the original price, and both prices are not null, and not sold.
    feature_items = Item.objects.filter(
        new_price__lt=F("original_price"),
        new_price__isnull=False,
        original_price__isnull=False,
        sold=False,
    )[:3]

    # Hot trend items - Items with at least 2 likes, not sold.
    hot_trend_items = Item.objects.annotate(num_likes=Count("likes")).filter(
        num_likes__gte=5, sold=False
    )[:3]

    best_seller_sellers = (
        Item.objects.filter(sold=True)
        .values("seller")
        .annotate(sold_count=Count("id"))
        .filter(sold_count__gte=2)
        .values_list("seller", flat=True)
    )

    best_seller_items = Item.objects.filter(seller__in=best_seller_sellers, sold=False)[
        :3
    ]
    success_message = request.session.pop("success_message", None)

    return render(
        request,
        "marketplace/item_list.html",
        {
            "items": items,
            "categories": categories,
            "deal_items": deal_items,
            "feature_items": feature_items,  # Features
            "hot_trend_items": hot_trend_items,
            "best_seller_items": best_seller_items,
            "liked_items": liked_items,  # Pass liked items to the template
            "cart_count": cart_count,
            "success_message": success_message,
        },
    )


def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    form = RatingForm()

    # Get the ratings and count them
    reviews = item.ratings.all()  # Retrieve all reviews for the item
    review_count = reviews.count()  # Count the number of reviews

    # If user submits a review
    if request.method == "POST" and request.user.is_authenticated:
        stars = request.POST.get("stars")
        comment = request.POST.get("comment")
        form = RatingForm(request.POST)

        if form.is_valid() and stars:
            user_rating, created = UserRating.objects.get_or_create(
                item=item,
                user=request.user,
                defaults={"stars": stars, "comment": comment},
            )

            if not created:
                user_rating.stars = stars
                user_rating.comment = comment
                user_rating.save()

            return redirect("marketplace:item_detail", item_id=item.id)

    # Retrieve related items in the same category, excluding the current item
    related_items = Item.objects.filter(category=item.category).exclude(id=item_id)[
        :4
    ]  # limit to 4 items
    liked_items = set(
        Like.objects.filter(user=request.user).values_list("item_id", flat=True)
    )

    is_in_cart = CartItem.objects.filter(cart__user=request.user, item=item).exists()

    if request.user.is_authenticated:
        SearchHistory.objects.get_or_create(user=request.user, query=item.title)

    return render(
        request,
        "marketplace/item_detail.html",
        {
            "item": item,
            "form": form,
            "reviews": reviews,
            "review_count": review_count,
            "average_rating": item.average_rating,
            "related_items": related_items,
            "liked_items": liked_items,
            "is_in_cart": is_in_cart,
        },
    )


@login_required
def add_item(request):
    error_message = None  # Initialize error_message

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)

        # Check if the image field is missing
        if "image" not in request.FILES or not request.FILES["image"]:
            error_message = (
                "Image required."  # Set the error message if image is missing
            )
            return render(
                request,
                "marketplace/add_item.html",
                {"form": form, "error_message": error_message},
            )

        # Form validation
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            request.session["success_message"] = (
                "Your item has been successfully listed!"
            )
            return redirect("marketplace:item_list")
        else:
            # If the form has other validation errors, we can add a general error message
            messages.error(
                request,
                "There were errors in your submission. Please correct them below.",
            )
            return render(request, "marketplace/add_item.html", {"form": form})

    else:
        form = ItemForm()

    return render(
        request,
        "marketplace/add_item.html",
        {"form": form, "error_message": error_message},
    )


@login_required
def seller_dashboard(request):
    if request.user.is_authenticated:
        user_items = Item.objects.filter(seller=request.user)

        # Collect data for the sales graph
        months = []
        total_sales = []

        # Get sales data grouped by month
        sales_data = (
            Item.objects.filter(seller=request.user, sold=True)
            .values("sold_date__month")
            .annotate(total_sales=Sum("price"))
            .order_by("sold_date__month")
        )

        # Prepare the data for JavaScript
        for data in sales_data:
            month_name = calendar.month_name[data["sold_date__month"]]
            months.append(month_name)
            total_sales.append(data["total_sales"])

        Notification.objects.filter(
            recipient=request.user, created_at__lt=timezone.now() - timedelta(hours=24)
        ).delete()

        # Fetch unread notifications for the seller without marking as read
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
            created_at__gte=timezone.now() - timedelta(hours=24),
        )

        # Determine which products are popular (more than 1 like)
        popular_items = []
        for item in user_items:
            if item.likes.count() >= 5 and not item.sold:
                popular_items.append(item)

        # Check if any item price has been lowered, remove from popular_items
        for item in popular_items:
            if item.new_price and item.new_price < item.price:
                popular_items.remove(item)

        success_message = request.session.pop("success_message", None)

        return render(
            request,
            "marketplace/seller_dashboard.html",
            {
                "user_items": user_items,
                "months": json.dumps(months),
                "total_sales": json.dumps(total_sales),
                "unread_notifications": unread_notifications,
                "popular_items": popular_items,  # Pass the popular items to the template
                "success_message": success_message,
            },
        )
    else:
        return redirect("login")


def mark_as_sold(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == "POST" and request.user == item.seller:
        item.sold = True
        item_name = item.title
        item.save()
        request.session["success_message"] = f'"{item_name}" has been market as sold.'
        return redirect("marketplace:seller_dashboard")
    return redirect("marketplace:item_detail", item_id=item.id)


def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == "POST" and request.user == item.seller:
        item_name = item.title

        if item.image:
            try:
                if os.path.isfile(item.image.path):
                    os.remove(item.image.path)
            except (AttributeError, ObjectDoesNotExist, FileNotFoundError):
                pass

        item.delete()

        request.session["success_message"] = (
            f'"{item_name}" has been successfully deleted from your listings.'
        )
        return redirect("marketplace:seller_dashboard")

    return redirect("marketplace:item_detail", item_id=item.id)


@require_POST
def like_item(request, item_id):
    item = Item.objects.get(id=item_id)
    user = request.user
    like, created = Like.objects.get_or_create(user=user, item=item)

    if not created:
        # If the item was already liked, the user is un liking it

        like.delete()
        liked = False
    else:
        liked = True
        if user != item.seller:
            Notification.objects.create(
                recipient=item.seller,
                item=item,
                message=f"{user.username} is interested in your product '{item.title}'.",
            )

    return JsonResponse(
        {
            "liked": liked,
            "total_likes": item.likes.count(),
        }
    )


# The view to display the form for updating an item
def update_item_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    if request.method == "POST":
        item.title = request.POST.get("title")
        item.description = request.POST.get("description")
        item.price = request.POST.get("price")

        # Check if new_price is not empty, otherwise set to None
        new_price = request.POST.get("new_price", None)
        if new_price == "":
            new_price = None
        item.new_price = new_price

        item.specification = request.POST.get("specification", None)
        item.brand = request.POST.get("brand", None)

        if "image" in request.FILES:
            item.image = request.FILES["image"]

        if "additional_images" in request.FILES:
            for img in request.FILES.getlist("additional_images"):
                ItemImage.objects.create(item=item, image=img)

        item.save()
        return redirect("marketplace:item_detail", item_id=item.id)

    return render(request, "marketplace/update_item.html", {"item": item})


@require_http_methods(["POST"])
def rate_item(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "You must be logged in to rate items"}, status=403
        )

    item = get_object_or_404(Item, id=item_id)

    try:
        # Attempt to parse the JSON body
        data = json.loads(request.body)
        stars = data.get("stars")
        comment = data.get("comment", "")

        # Validate the stars rating
        if not stars or not isinstance(stars, (int, str)) or not (1 <= int(stars) <= 5):
            return JsonResponse({"error": "Invalid star rating"}, status=400)

        stars = int(stars)

        # Save or update the user rating
        user_rating, created = UserRating.objects.update_or_create(
            item=item, user=request.user, defaults={"stars": stars, "comment": comment}
        )

        # Calculate the average rating
        average_rating = UserRating.objects.filter(item=item).aggregate(Avg("stars"))[
            "stars__avg"
        ]
        average_rating = round(float(average_rating or 0), 2)

        return JsonResponse(
            {
                "success": True,
                "average_rating": average_rating,
                "message": "Rating submitted successfully",
            }
        )

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON data")  # Log the error
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    except ValueError as e:
        logger.error(f"ValueError: {str(e)}")  # Log the error
        return JsonResponse({"error": "Invalid value provided"}, status=400)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")  # Log the error
        return JsonResponse({"error": "An internal error occurred"}, status=500)


# Add to Cart
@login_required
def add_to_cart(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Check if the user owns the item
        if item.seller == request.user:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "You cannot add your own item to the cart.",
                },
                status=400  # Use 400 status for client-side errors
            )

        # Check if the item is sold
        if item.sold:  # Assuming there is a BooleanField 'sold' in the Item model
            return JsonResponse(
                {
                    "status": "error",
                    "message": "This item is sold and cannot be added to the cart.",
                },
                status=400
            )

        # Check if the item is already in the cart
        if CartItem.objects.filter(cart=cart, item=item).exists():
            return JsonResponse(
                {
                    "status": "exists",
                    "message": "Item already in cart",
                }
            )

        # If item is not in the cart and not owned by the user, add it
        CartItem.objects.create(cart=cart, item=item, quantity=1)
        return JsonResponse(
            {
                "status": "success",
                "message": "Item added to cart",
            }
        )

    return JsonResponse(
        {"status": "error", "message": "Authentication required"}, status=403
    )



def cart_page(request):
    # Retrieve the cart items for the logged-in user
    cart_items = CartItem.objects.filter(cart__user=request.user)

    # Calculate the total price of the items in the cart, excluding sold items
    total_price = sum(
        item.item.price * item.quantity for item in cart_items if not item.item.sold
    )

    # Calculate the cart count excluding sold items
    cart_count = CartItem.objects.filter(
        cart__user=request.user, item__sold=False
    ).count()
    deal_items = Item.objects.filter(
        new_price__lt=F("original_price"),
        new_price__isnull=False,
        original_price__isnull=False,
        sold=False,
    )

    # Pass the cart items, total price, and count to the template
    context = {
        "cart_items": cart_items,
        "total_price": total_price,
        "cart_count": cart_count,
        "deal_items": deal_items,
    }
    return render(request, "marketplace/cart_page.html", context)


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def remove_cart_item(request):
    if request.method == "POST":
        data = json.loads(request.body)
        item_id = data.get("item_id")

        # Retrieve and delete the cart item for the user
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart_item.delete()

        # Calculate the new total and item count for the user's cart
        user_cart_items = CartItem.objects.filter(cart__user=request.user)
        new_total = sum(item.item.price * item.quantity for item in user_cart_items)
        cart_count = user_cart_items.count()

        return JsonResponse(
            {"success": True, "new_total": new_total, "cart_count": cart_count}
        )

    return JsonResponse({"success": False})
