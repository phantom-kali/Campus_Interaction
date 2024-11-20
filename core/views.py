from django.shortcuts import render
from events.models import Event
from feeds.models import Post
from polls.models import Poll
from marketplace.models import Item
from maps.models import Landmark
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone


def home(request):
    return render(request, "core/home.html")


def about(request):
    return render(request, "core/about.html")


# Truncate Searched Descriptions
def truncate_description(text, max_chars=80):
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return truncated + "..."


def search(request):
    query = request.GET.get("q")
    results = {}
    now = timezone.now()

    if query:
        # Search in Event model fields like title, description, and content
        events = Event.objects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(content__icontains=query)
        )[:5]

        if events:
            results["events"] = [
                {
                    "id": event.id,
                    "title": event.title,
                    "description": truncate_description(event.description),
                }
                for event in events
            ]
        # Search in Poll model fields like title and description
        polls = Poll.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            Q(is_public=True),
            Q(allow_expiration=False) | Q(expiration_time__gt=now),
        )[:5]

        if polls:
            results["polls"] = [
                {
                    "id": poll.id,
                    "title": poll.title,
                    "description": truncate_description(poll.description),
                }
                for poll in polls
            ]

        # Search in Post model's content, user (username), and status fields
        posts = Post.objects.filter(
            Q(content__icontains=query)
            | Q(user__username__icontains=query)
            | Q(status__icontains=query),
            Q(status="published"),  # Only return published posts
        )[:5]

        if posts:
            results["posts"] = [
                {
                    "id": post.id,
                    "title": post.user.username[:20],  # Basic title
                    "description": truncate_description(
                        post.content
                    ),  # Basic description
                }
                for post in posts
            ]

        # Search in Item model's content, title, and description
        items = Item.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:5]

        if items:
            results["items"] = [
                {
                    "id": item.id,
                    "title": item.title[:20]
                    + ("..." if len(item.title) > 10 else ""),  # Short title preview
                    "description": truncate_description(item.description),
                }
                for item in items
            ]

    # Check if the request is AJAX
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # If no events, polls, or posts are found, add a "no results" entry
        if not results:
            results = {"no_results": "No search results found"}

        return JsonResponse(results)

    # Optionally render a search results page here if not an AJAX request
    return
