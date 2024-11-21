import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.db.models import F
from django.db import models
import json
import logging
from .models import Post, PostView, PostLike, Comment
from .forms import PostForm, CommentForm, ReportForm

POSTS_PER_PAGE = 10


@login_required
def feed_list(request):
    # Get all published posts, newest first
    posts = (
        Post.objects.filter(status="published")
        .select_related("user")
        .prefetch_related("comments")
        .order_by("-created_at")
    )

    # First page of posts
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(1)

    context = {
        "posts": page_obj,
        "has_next": page_obj.has_next(),
        "current_page": 1,
        "is_trending": False,
    }

    return render(request, "feeds/feed_list.html", context)


@login_required
def trending_feed(request):
    # Get posts from the last 7 days
    last_week = timezone.now() - timedelta(days=7)

    # Get trending posts based on likes, comments, and views
    posts = (
        Post.objects.filter(status="published", created_at__gte=last_week)
        .select_related("user")
        .prefetch_related("comments")
        .annotate(engagement_score=Count("likes") + Count("comments") + Count("views"))
        .order_by("-engagement_score")
    )

    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(1)

    context = {
        "posts": page_obj,
        "has_next": page_obj.has_next(),
        "current_page": 1,
        "is_trending": True,
    }

    return render(request, "feeds/feed_list.html", context)


@login_required
def load_more_posts(request):
    page_number = int(request.GET.get("page", 1))
    is_trending = request.GET.get("trending", "false") == "true"

    if is_trending:
        last_week = timezone.now() - timedelta(days=7)
        posts = (
            Post.objects.filter(status="published", created_at__gte=last_week)
            .select_related("user")
            .prefetch_related("comments")
            .annotate(
                engagement_score=Count("likes") + Count("comments") + Count("views")
            )
            .order_by("-engagement_score")
        )
    else:
        posts = (
            Post.objects.filter(status="published")
            .select_related("user")
            .prefetch_related("comments")
            .order_by("-created_at")
        )

    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(page_number)

    posts_data = [
        {
            "id": post.id,
            "content": post.content,
            "image_url": post.image.url if post.image else None,
            "video_url": post.video.url if post.video else None,
            "created_at": post.created_at.isoformat(),
            "likes_count": post.likes_count,
            "comments_count": post.comments_count,
            "views_count": post.views_count,
            "user": {
                "id": post.user.id,
                "username": post.user.username,
                "profile_pic": post.user.profile.get_avatar_url(),
            },
        }
        for post in page_obj
    ]

    return JsonResponse(
        {
            "posts": posts_data,
            "has_next": page_obj.has_next(),
            "current_page": page_number,
        }
    )


@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()

            if request.headers.get("HX-Request"):
                # Return only the new post HTML for HTMX requests
                return render(
                    request, "feeds/partials/post_list.html", {"posts": [post]}
                )
            return redirect("feeds:post_detail", post_id=post.id)
    else:
        form = PostForm()

    return render(request, "feeds/create_post.html", {"form": form})


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("user").prefetch_related("comments__user"),
        id=post_id,
    )

    # Record view if not already viewed today
    PostView.objects.get_or_create(
        post=post,
        user=request.user,
        viewed_date=timezone.now().date(),
        defaults={
            "ip_address": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:200],
        },
    )

    context = {
        "post": post,
        "comments": post.comments.filter(parent=None).order_by("-created_at")[:10],
    }
    return render(request, "feeds/post_detail.html", context)


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()
        Post.objects.filter(pk=post_id).update(likes_count=F("likes_count") - 1)
        is_liked = False
    else:
        Post.objects.filter(pk=post_id).update(likes_count=F("likes_count") + 1)
        is_liked = True

    return JsonResponse({"is_liked": is_liked, "likes_count": post.likes_count})


@login_required
def load_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = (
        post.comments.filter(parent=None)
        .select_related("user", "user__profile")  # Add this to prefetch profile data
        .prefetch_related("replies")
    )

    html = render_to_string(
        "feeds/partials/comment.html", {"comments": comments, "user": request.user}
    )

    return JsonResponse({"html": html})


@login_required
@require_POST
def add_comment(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        content = data.get("content")
        parent_id = data.get("parent_id")

        if not content:
            return JsonResponse({"error": "Comment content is required"}, status=400)

        parent = None
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id, post=post)

        comment = Comment.objects.create(
            post=post, user=request.user, content=content, parent=parent
        )

        # Get the latest post data with profile information
        comment = Comment.objects.select_related("user", "user__profile").get(
            id=comment.id
        )

        html = render_to_string(
            "feeds/partials/comment.html", {"comment": comment, "user": request.user}
        )

        return JsonResponse({"html": html, "comments_count": post.comments_count})
    except Exception as e:
        logging.error("An error occurred while adding a comment: %s", str(e))
        return JsonResponse({"error": "An internal error has occurred!"}, status=500)


@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
        comment.likes_count = F("likes_count") - 1
        is_liked = False
    else:
        comment.likes.add(request.user)
        comment.likes_count = F("likes_count") + 1
        is_liked = True

    comment.save()

    return JsonResponse({"is_liked": is_liked, "likes_count": comment.likes_count})


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    post.delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
def report_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.user:
        return JsonResponse({"error": "Cannot report your own post"}, status=400)

    form = ReportForm(data=json.loads(request.body))
    if form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.post = post
        report.save()
        return JsonResponse({"success": True})

    return JsonResponse({"errors": form.errors}, status=400)


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    post = comment.post
    comment.delete()

    return JsonResponse({"success": True, "comments_count": post.comments_count})
