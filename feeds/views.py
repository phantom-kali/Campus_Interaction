import datetime
from functools import wraps
from time import sleep
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, Q, Prefetch, Count
from django.core.files.storage import default_storage
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db import IntegrityError, OperationalError, transaction

from .models import Post, Comment, PostView, PostLike, Report
from .forms import PostForm, CommentForm
from profiles.models import Profile, UserFollow
import logging

logger = logging.getLogger(__name__)

POSTS_PER_PAGE = 20
CACHE_TTL = 300  # 5 minutes


def get_client_ip(request):
    """
    Extract the client IP address from the request.

    Args:
        request: HttpRequest object

    Returns:
        str: Client IP address from X-Forwarded-For header or REMOTE_ADDR
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )


@cache_page(CACHE_TTL)
def home(request):
    """
    Landing page view that serves trending posts.
    """

    def get_trending_posts():
        return (
            Post.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=1),
                status="published",
            )
            .order_by("-views_count")
            .select_related("user")[:5]
        )

    trending_posts = cache.get_or_set(
        "trending_posts",
        get_trending_posts(),
        CACHE_TTL,
    )
    return render(request, "feeds/home.html", {"trending_posts": trending_posts})


@login_required
def feed(request):
    """
    Main feed view with pagination and filtering options.
    """
    page = request.GET.get("page", 1)
    filter_by = request.GET.get("filter", "all")

    # Base queryset with all necessary joins
    base_queryset = (
        Post.objects.select_related("user")
        .prefetch_related(
            Prefetch(
                "comments",
                queryset=Comment.objects.select_related("user").order_by("-created_at"),
                to_attr="recent_comments",  # Store in custom attribute
            ),
            "likes",
        )
        .filter(status="published")
    )

    if filter_by == "following":
        following_users = request.user.profile.following.values_list("user", flat=True)
        posts = base_queryset.filter(user__in=following_users)
    elif filter_by == "trending":
        posts = base_queryset.order_by("-views_count", "-likes_count", "-created_at")
    else:  # filter_by == "all"
        posts = base_queryset.order_by("-created_at")

    paginator = Paginator(posts, POSTS_PER_PAGE)
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    posts_data = [
        {
            "id": post.id,
            "content": post.content,
            "user": {"id": post.user.id, "username": post.user.username},
            "is_owner": post.user == request.user,
            "created_at": post.created_at.isoformat(),
            "likes_count": post.likes_count,
            "comments_count": (
                len(post.recent_comments) if hasattr(post, "recent_comments") else 0
            ),
            "views_count": post.views_count,
            "image_url": post.image.url if post.image else None,
            "video_url": post.video.url if post.video else None,
            "recent_comments": (
                [
                    {
                        "id": comment.id,
                        "content": comment.content,
                        "user": {
                            "id": comment.user.id,
                            "username": comment.user.username,
                        },
                        "created_at": comment.created_at.isoformat(),
                    }
                    for comment in post.recent_comments[:3]
                ]
                if hasattr(post, "recent_comments")
                else []
            ),
        }
        for post in page_obj
    ]

    return JsonResponse(
        {
            "status": "success",
            "posts": posts_data,
            "has_next": page_obj.has_next(),
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "filter_by": filter_by,
        }
    )


@login_required
def search_posts(request):
    """
    Search posts by content, username, or hashtags.

    Args:
        request: HttpRequest object with 'q' query parameter

    Returns:
        JsonResponse: Paginated search results
    """
    query = request.GET.get("q", "").strip()
    page = request.GET.get("page", 1)

    if not query:
        return JsonResponse(
            {"status": "error", "message": "Search query is required"}, status=400
        )

    # Split query into terms and hashtags
    terms = [term for term in query.split() if not term.startswith("#")]
    hashtags = [term[1:] for term in query.split() if term.startswith("#")]

    posts = Post.objects.select_related("user").filter(status="published")

    # Search in post content and username
    if terms:
        posts = posts.filter(
            Q(content__icontains=" ".join(terms))
            | Q(user__username__icontains=" ".join(terms))
        )

    # Search hashtags
    if hashtags:
        for tag in hashtags:
            posts = posts.filter(content__icontains=f"#{tag}")

    posts = posts.order_by("-created_at")

    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(page)

    posts_data = [
        {
            "id": post.id,
            "content": post.content,
            "user": {"id": post.user.id, "username": post.user.username},
            "created_at": post.created_at.isoformat(),
            "likes_count": post.likes_count,
            "comments_count": post.comments.count(),
            "views_count": post.views_count,
            "image_url": post.image.url if post.image else None,
            "video_url": post.video.url if post.video else None,
        }
        for post in page_obj
    ]

    return JsonResponse(
        {
            "status": "success",
            "posts": posts_data,
            "has_next": page_obj.has_next(),
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
        }
    )


@login_required
@require_POST
@transaction.atomic
def like_post(request, post_id):
    """Toggle like status for a post."""
    try:
        post = Post.objects.select_for_update().get(id=post_id)

        # Check for existing like
        existing_like = PostLike.objects.filter(user=request.user, post=post)

        if existing_like.exists():
            # Unlike - only decrease if count > 0
            if post.likes_count > 0:
                existing_like.delete()
                Post.objects.filter(id=post_id, likes_count__gt=0).update(
                    likes_count=F("likes_count") - 1
                )
            liked = False
        else:
            # Like
            PostLike.objects.create(user=request.user, post=post)
            Post.objects.filter(id=post_id).update(likes_count=F("likes_count") + 1)
            liked = True

        # Refresh to get the updated count
        post.refresh_from_db()

        return JsonResponse(
            {"status": "success", "liked": liked, "likes_count": post.likes_count}
        )
    except Post.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Post not found"}, status=404
        )
    except Exception as e:
        logger.error(f"Error in like_post: {str(e)}")
        return JsonResponse({"status": "error", "message": "Server error"}, status=500)


@login_required
@require_POST
def add_comment(request, post_id):
    """
    Add a comment to a post.

    Args:
        request: HttpRequest object
        post_id (int): ID of the post to comment on

    Returns:
        JsonResponse: New comment data or validation errors
    """
    # Add debugging logs
    logger.debug(f"Received POST data: {request.POST}")

    form = CommentForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                comment = form.save(commit=False)
                comment.post_id = post_id
                comment.user = request.user
                comment.save()

                return JsonResponse(
                    {
                        "status": "success",
                        "comment": {
                            "id": comment.id,
                            "content": comment.content,
                            "user": {
                                "id": comment.user.id,
                                "username": comment.user.username,
                            },
                            "created_at": comment.created_at.isoformat(),
                            "likes_count": 0,
                        },
                    }
                )
        except Exception as e:
            logger.error(f"Error in add_comment: {str(e)}")
            return JsonResponse(
                {"status": "error", "message": "Server error"}, status=500
            )

    # Add form errors to the log
    logger.error(f"Form validation errors: {form.errors}")
    return JsonResponse({"status": "error", "errors": form.errors}, status=400)


@login_required
@require_http_methods(["GET", "POST"])
def create_post(request):
    """
    Create a new post with optional media attachments.

    Args:
        request: HttpRequest object

    Returns:
        JsonResponse: Created post data or validation errors
    """
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    post = form.save(commit=False)
                    post.user = request.user
                    post.save()
                    return JsonResponse(
                        {
                            "status": "success",
                            "post": {
                                "id": post.id,
                                "content": post.content,
                                "user": {
                                    "id": post.user.id,
                                    "username": post.user.username,
                                },
                                "created_at": post.created_at.isoformat(),
                                "image_url": post.image.url if post.image else None,
                                "video_url": post.video.url if post.video else None,
                            },
                        }
                    )
            except Exception as e:
                logger.error(f"Error in create_post: {str(e)}")
                return JsonResponse(
                    {"status": "error", "message": "Error creating post"}, status=500
                )
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)

    return render(request, "feeds/post_create.html", {"form": PostForm()})


def retry_on_db_lock(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                if "database is locked" in str(e):
                    attempt += 1
                    if attempt == max_attempts:
                        raise
                    sleep(0.1 * attempt)  # Exponential backoff
                else:
                    raise

    return wrapper


@login_required
@require_POST
@retry_on_db_lock
def increment_view_count(request, post_id):
    """Track post views with rate limiting"""
    today = timezone.now().date()
    cache_key = f"post_view_{post_id}_{request.user.id}_{today}"

    if not cache.get(cache_key):
        try:
            with transaction.atomic():
                # Use select_for_update(nowait=True) to fail fast if locked
                post = Post.objects.select_for_update(nowait=True).get(id=post_id)

                # Create PostView
                PostView.objects.create(
                    post=post,
                    user=request.user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:200],
                    viewed_at=timezone.now(),
                    viewed_date=today,
                )

                # Update views_count
                post.refresh_from_db()
                post.views_count += 1
                post.save(update_fields=["views_count"])

                # Set cache
                cache.set(cache_key, True, timeout=86400)  # 24 hours

                return JsonResponse(
                    {"status": "success", "views_count": post.views_count}
                )

        except IntegrityError:
            return JsonResponse(
                {"status": "success", "message": "View already counted"}
            )
        except Exception as e:
            logger.error(f"Error in increment_view_count: {str(e)}")
            return JsonResponse(
                {"status": "error", "message": "An internal error has occurred."},
                status=500,
            )

    return JsonResponse({"status": "success", "message": "View already counted"})


@login_required
def post_detail(request, post_id):
    """
    Get detailed information about a specific post.

    Args:
        request: HttpRequest object
        post_id (int): ID of the post to retrieve

    Returns:
        JsonResponse: Detailed post data including comments and engagement metrics
    """
    try:
        post = get_object_or_404(
            Post.objects.select_related("user", "user__profile").prefetch_related(
                Prefetch(
                    "comments",
                    queryset=Comment.objects.select_related("user", "user__profile")
                    .prefetch_related(
                        "likes",
                        Prefetch(
                            "replies",
                            queryset=Comment.objects.select_related(
                                "user", "user__profile"
                            ).prefetch_related("likes"),
                        ),
                    )
                    .filter(parent=None)
                    .order_by("-created_at"),
                ),
                "likes",
            ),
            id=post_id,
        )

        if post.status != "published" and post.user != request.user:
            return JsonResponse(
                {"status": "error", "message": "Permission denied"}, status=403
            )

        Post.objects.filter(id=post_id).update(views_count=F("views_count") + 1)

        def serialize_comment(comment):
            return {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at.isoformat(),
                "user": {
                    "id": comment.user.id,
                    "username": comment.user.username,
                    "avatar_url": comment.user.profile.get_avatar_url(),
                    "is_online": comment.user.profile.is_online,
                    "was_recently_online": comment.user.profile.was_recently_online(),
                },
                "likes_count": comment.likes_count,
                "is_liked": request.user in comment.likes.all(),
                "replies_count": comment.replies.count(),
                "replies": (
                    [serialize_comment(reply) for reply in comment.replies.all()]
                    if comment.replies.exists()
                    else []
                ),
            }

        response_data = {
            "status": "success",
            "post": {
                "id": post.id,
                "content": post.content,
                "user": {
                    "id": post.user.id,
                    "username": post.user.username,
                    "avatar_url": post.user.profile.get_avatar_url(),
                    "is_online": post.user.profile.is_online,
                    "was_recently_online": post.user.profile.was_recently_online(),
                    "student_id": post.user.profile.student_id,
                    "course": post.user.profile.course,
                },
                "created_at": post.created_at.isoformat(),
                "image_url": post.image.url if post.image else None,
                "video_url": post.video.url if post.video else None,
                "likes_count": post.likes_count,
                "views_count": post.views_count,
                "comments_count": post.comments.filter(parent=None).count(),
                "is_liked": request.user in post.likes.all(),
                "is_owner": post.user == request.user,
                "comments": [
                    serialize_comment(comment) for comment in post.comments.all()
                ],
            },
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error in post_detail: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": "Error retrieving post"}, status=500
        )


@login_required
def suggested_users(request):
    user_profile = request.user.profile

    # Get IDs of users already being followed
    following_ids = user_profile.following.values_list("id", flat=True)

    # Base queryset excluding the user themselves and users they already follow
    base_qs = Profile.objects.exclude(Q(user=request.user) | Q(id__in=following_ids))

    # Find users with similar attributes (same campus, course, year of study)
    similar_users = base_qs.filter(
        Q(campus=user_profile.campus)
        | Q(course=user_profile.course)
        | Q(year_of_study=user_profile.year_of_study)
    ).distinct()

    # Find users followed by people the user follows (mutual connections)
    mutual_connections = base_qs.filter(followers__in=following_ids).annotate(
        mutual_count=Count("followers")
    )

    # Find active users based on recent posts and engagement
    active_users = (
        base_qs.filter(
            user__post__created_at__gte=timezone.now() - datetime.timedelta(days=30)
        )
        .annotate(post_count=Count("user__post"))
        .filter(post_count__gt=0)
    )

    # Combine and prioritize suggestions
    suggested = (
        list(similar_users[:5]) + list(mutual_connections[:5]) + list(active_users[:5])
    )
    # Remove duplicates while preserving order
    seen = set()
    unique_suggested = []
    for profile in suggested:
        if profile.id not in seen:
            seen.add(profile.id)
            unique_suggested.append(profile)

    # Limit to top 10 suggestions
    suggested_profiles = unique_suggested[:10]

    return JsonResponse(
        {
            "users": [
                {
                    "id": profile.user.id,
                    "username": profile.user.username,
                    "avatar_url": profile.get_avatar_url(),
                    "course": profile.course,
                    "year_of_study": profile.year_of_study,
                    "campus": profile.campus,
                    "mutual_followers": UserFollow.objects.filter(
                        following__in=following_ids, follower=profile
                    ).count(),
                }
                for profile in suggested_profiles
            ]
        }
    )


@login_required
def report_post(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    post = get_object_or_404(Post, id=post_id)
    report_type = request.POST.get("report_type")
    description = request.POST.get("description", "")

    if not report_type or report_type not in dict(Report.REPORT_TYPES):
        return JsonResponse({"error": "Invalid report type"}, status=400)

    # Check if user has already reported this post
    if Report.objects.filter(reporter=request.user, post=post).exists():
        return JsonResponse(
            {"error": "You have already reported this post"}, status=400
        )

    report = Report.objects.create(
        reporter=request.user,
        post=post,
        report_type=report_type,
        description=description,
        status="pending",
    )

    return JsonResponse(
        {"message": "Report submitted successfully", "report_id": report.id}, status=201
    )


@login_required
def report_comment(request, comment_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    comment = get_object_or_404(Comment, id=comment_id)
    report_type = request.POST.get("report_type")
    description = request.POST.get("description", "")

    if not report_type or report_type not in dict(Report.REPORT_TYPES):
        return JsonResponse({"error": "Invalid report type"}, status=400)

    # Create a new Report model for comments if you want to track them separately
    # For now, we'll create a report against the parent post with additional context
    if Report.objects.filter(reporter=request.user, post=comment.post).exists():
        return JsonResponse(
            {"error": "You have already reported this content"}, status=400
        )

    report = Report.objects.create(
        reporter=request.user,
        post=comment.post,  # Link to parent post
        report_type=report_type,
        description=f"Comment ID {comment.id}: {description}",  # Include comment context
        status="pending",
    )

    return JsonResponse(
        {"message": "Report submitted successfully", "report_id": report.id}, status=201
    )


@login_required
@require_POST
@transaction.atomic
def delete_post(request, post_id):
    """
    Delete a post and its associated media files.

    Args:
        request: HttpRequest object
        post_id (int): ID of the post to delete

    Returns:
        JsonResponse: Success or error status
    """
    try:
        post = get_object_or_404(Post, id=post_id)

        if post.user != request.user and not request.user.is_staff:
            return JsonResponse(
                {"status": "error", "message": "Permission denied"}, status=403
            )

        image_path = post.image.path if post.image else None
        video_path = post.video.path if post.video else None

        post.delete()

        if image_path:
            default_storage.delete(image_path)
        if video_path:
            default_storage.delete(video_path)

        return JsonResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Error in delete_post: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": "Error deleting post"}, status=500
        )


@login_required
def post_engagement(request, post_id, engagement_type):
    """
    Get detailed engagement information for a post.

    Args:
        request: HttpRequest object
        post_id (int): ID of the post
        engagement_type (str): Type of engagement to retrieve (likes/comments/views)

    Returns:
        JsonResponse: Paginated engagement data
    """
    post = get_object_or_404(Post, id=post_id)

    if post.user != request.user and not request.user.is_staff:
        return JsonResponse(
            {"status": "error", "message": "Permission denied"}, status=403
        )

    page = request.GET.get("page", 1)
    items_per_page = 50

    if engagement_type == "likes":
        queryset = post.likes.select_related("profile").order_by(
            "-postlike__created_at"
        )
    elif engagement_type == "comments":
        queryset = post.comments.select_related("user").order_by("-created_at")
    elif engagement_type == "views":
        queryset = post.views.select_related("user").order_by("-viewed_at")
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid engagement type"}, status=400
        )

    paginator = Paginator(queryset, items_per_page)
    page_obj = paginator.get_page(page)

    data = []
    for item in page_obj:
        if engagement_type == "likes":
            data.append(
                {
                    "user_id": item.id,
                    "username": item.username,
                    "profile_pic": (
                        item.profile.profile_pic.url
                        if item.profile.profile_pic
                        else None
                    ),
                    "timestamp": item.postlike_set.filter(post=post)
                    .first()
                    .created_at.isoformat(),
                }
            )
        elif engagement_type == "comments":
            data.append(
                {
                    "id": item.id,
                    "user_id": item.user.id,
                    "username": item.user.username,
                    "content": item.content,
                    "timestamp": item.created_at.isoformat(),
                    "likes_count": item.likes_count,
                }
            )
        else:  # views
            data.append(
                {
                    "user_id": item.user.id,
                    "username": item.user.username,
                    "timestamp": item.viewed_at.isoformat(),
                    "ip_address": item.ip_address if request.user.is_staff else None,
                }
            )

    return JsonResponse(
        {
            "status": "success",
            "data": data,
            "has_next": page_obj.has_next(),
            "total_pages": paginator.num_pages,
            "current_page": page_obj.number,
        }
    )


@login_required
def like_comment(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(Comment, id=comment_id)
        # Assuming you want to like a comment by the user making the request
        user = request.user

        # Check if the user has already liked the comment
        if user in comment.likes.all():
            return JsonResponse(
                {"message": "You have already liked this comment."}, status=400
            )

        # Like the comment
        comment.likes.add(user)
        comment.likes_count += 1
        comment.save()

        return JsonResponse(
            {
                "message": "Comment liked successfully.",
                "likes_count": comment.likes_count,
            }
        )


@login_required
def delete_comment(request, comment_id):
    if request.method == "DELETE":
        comment = get_object_or_404(Comment, id=comment_id)

        # Check if the user is the owner of the comment
        if comment.user != request.user:
            return JsonResponse(
                {"message": "You do not have permission to delete this comment."},
                status=403,
            )

        # Delete the comment
        comment.delete()

        # Update the post's comments count
        Post.objects.filter(id=comment.post.id).update(
            comments_count=F("comments_count") - 1
        )

        return JsonResponse({"message": "Comment deleted successfully."})
