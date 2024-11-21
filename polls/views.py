from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Poll, Option, Vote, Comment, Like
from .forms import PollForm, OptionFormSet, EditPollForm
from django.db.models import Count, Sum, Q
from datetime import timedelta
import logging
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
import pytz
from django.http import HttpResponse
import json
from django.urls import reverse
from io import BytesIO
import qrcode
import base64
from itertools import chain
from django.db.models import Count
from django.db.models.functions import ExtractMonth


logger = logging.getLogger(__name__)
from django.db.models import Q


def base_poll(request):
    query = request.GET.get("query", "")
    poll_type = request.GET.get("poll_type", "")

    current_time = timezone.now()
    polls = Poll.objects.prefetch_related("options").order_by("-created_at")

    # Filter based on the query
    if query:
        polls = polls.filter(
            (Q(title__icontains=query) | Q(description__icontains=query))
            & Q(is_archived=False)  # Exclude optional archived polls
            & (
                Q(expiration_time__gt=current_time) | Q(allow_expiration=False)
            )  # Exclude expired polls
        )
    else:
        # Without a query, show active polls by filtering out expired and archived polls
        polls = polls.filter(
            Q(expiration_time__gt=current_time) | Q(allow_expiration=False)
        )

    # Filter based on poll type
    if poll_type:
        polls = polls.filter(poll_type=poll_type)

    # Filter active polls (those that are not expired and allow expiration)
    active_polls = polls.filter(
        Q(expiration_time__gt=current_time) | Q(allow_expiration=False)
    ).distinct()

    no_polls_message = None
    if not active_polls.exists():
        no_polls_message = "No polls found matching your search criteria."

    # Get popular polls
    popular_polls = (
        Poll.objects.filter(view_count__gt=10)
        .exclude(expiration_time__lt=current_time)
        .filter(Q(expiration_time__lt=current_time) & Q(allow_expiration=True))
        .distinct()
        .order_by("-view_count")
    )

    # Get liked polls
    liked_polls = Like.objects.filter(
        user=request.user, poll__in=active_polls
    ).values_list("poll_id", flat=True)
    liked_comments = Like.objects.filter(
        user=request.user, poll__in=active_polls
    ).values_list("comment_id", flat=True)
    liked_comments_set = set(liked_comments)
    liked_polls_set = set(liked_polls)

    # Expired polls moved to archived polls
    archived_polls = Poll.objects.filter(
        Q(expiration_time__lt=current_time) & Q(allow_expiration=True)
    ).distinct()
    # User choosen to archived poll
    optional_polls_archived = polls.filter(Q(is_archived=True))
    archived_results = polls.filter(Q(is_archived_results=True))



    return render(
        request,
        "polls/all_polls.html",
        {
            "polls": active_polls,
            "query": query,
            "poll_type": poll_type,
            "popular_polls": popular_polls,
            "liked_polls_set": liked_polls_set,
            "liked_comments_set": liked_comments_set,
            "archived_polls": archived_polls,
            "no_polls_message": no_polls_message,
            "optional_polls_archived": optional_polls_archived,
            "archived_results": archived_results,
        },
    )


# Searching Polls
def search_poll(request, title):
    polls = Poll.objects.filter(title__iexact=title)
    current_time = timezone.now()
    popular_polls = (
        Poll.objects.filter(view_count__gt=10)
        .exclude(expiration_time__lt=current_time)
        .filter(Q(expiration_time__lt=current_time) & Q(allow_expiration=True))
        .distinct()
        .order_by("-view_count")
    )
    archived_polls = Poll.objects.filter(
        Q(expiration_time__lt=current_time) & Q(allow_expiration=True)
    ).distinct()
    archived_results = polls.filter(Q(is_archived_results=True))
    if not polls.exists():
        # Handle case where no poll matches the title
        return render(
            request, "all_polls.html", {"message": "No polls found with that title."}
        )
    return render(
        request,
        "polls/all_polls.html",
        {
            "polls": polls,
            "archived_results": archived_results,
            "popular_polls": popular_polls,
            "archived_polls": archived_polls,
        },
    )


# Load Comments 5 per every load
def load_comments(request, poll_id):
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 5))
    comments = Comment.objects.filter(poll_id=poll_id).order_by("-created_at")[
        offset : offset + limit
    ]
    liked_comments = Like.objects.filter(user=request.user).values_list(
        "comment_id", flat=True
    )
    liked_comments_set = set(liked_comments)

    comments_data = []
    for c in comments:
        comments_data.append(
            {
                "id": c.id,
                "user": {"username": c.user.username},
                "text": c.text,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "total_likes": c.total_likes(),  # Call the method with parentheses
                "liked": c.id
                in liked_comments_set,  # Check if the comment is liked by the user
            }
        )

    return JsonResponse({"comments": comments_data})


def add_polls(request):
    if request.method == "POST":
        poll_form = PollForm(request.POST, request.FILES)
        option_formset = OptionFormSet(request.POST, request.FILES)
        error_message = None

        if poll_form.is_valid() and option_formset.is_valid():
            poll = poll_form.save(commit=False)  # Create poll instance but don't save yet

            if poll.poll_type == "question":
                correct_answers = any(
                    option_form.cleaned_data.get("is_correct")
                    for option_form in option_formset
                )
                if not correct_answers:
                    error_message = "A question must have at least one correct answer."
                else:
                    if request.user.is_authenticated:
                        poll.creator = request.user
                    poll.save()
                    if "banner_image" in request.FILES:
                        poll.banner_image = request.FILES["banner_image"]
                        poll.save()
                    poll.generate_unique_link()
                    poll.generate_qr_code()
                    poll.save()

                    for option_form in option_formset:
                        if option_form.cleaned_data.get("option_text") or option_form.cleaned_data.get("option_image"):
                            option = option_form.save(commit=False)
                            option.poll = poll
                            option.save()

                    return redirect("polls:vote_poll", poll_id=poll.id)
            else:
                if request.user.is_authenticated:
                    poll.creator = request.user
                poll.save()
                if "banner_image" in request.FILES:
                    poll.banner_image = request.FILES["banner_image"]
                    poll.save()
                poll.generate_unique_link()
                poll.generate_qr_code()
                poll.save()

                for option_form in option_formset:
                    if option_form.cleaned_data.get("option_text") or option_form.cleaned_data.get("option_image"):
                        option = option_form.save(commit=False)
                        option.poll = poll
                        option.save()

                return redirect("polls:vote_poll", poll_id=poll.id)
        else:
            logger.error("Poll Form Errors: %s", poll_form.errors)
            logger.error("Option Formset Errors: %s", option_formset.errors)

            # Handle banner image error separately
            if 'banner_image' in poll_form.errors:
                error_message = poll_form.errors['banner_image'][0]
            elif option_formset.non_form_errors():
                error_message = "At least two options are required."
            else:
                error_message = []
                for i, form in enumerate(option_formset.forms):
                    if not form.is_valid():
                        for error in form.errors.as_data().values():
                            error_message.append(f"Option {i + 1}: {error[0].message}")

                if not error_message:
                    error_message = "Please correct the errors below."

    else:
        poll_form = PollForm()
        option_formset = OptionFormSet(queryset=Option.objects.none())
        error_message = None

    return render(
        request,
        "polls/add_polls.html",
        {
            "poll_form": poll_form,
            "option_formset": option_formset,
            "error_message": error_message,
        },
    )
@login_required
def user_dashboard(request):
    query = request.GET.get("query", "")
    polls = Poll.objects.filter(creator=request.user).order_by("-created_at")

    if query:
        polls = polls.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    polls_with_status = [
        (
            poll,
            poll.is_active,
            f"http://127.0.0.1:8000{reverse('polls:poll_results', args=[poll.id])}",
        )
        for poll in polls
    ]

    now = timezone.now()
    months = [now.replace(month=m).strftime("%B") for m in range(1, 13)]
    polls_count = (
        Poll.objects.filter(creator=request.user)
        .annotate(month=ExtractMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    data = [0] * 12
    for entry in polls_count:
        data[entry["month"] - 1] = entry["count"]

    total_votes = Vote.objects.filter(poll__creator=request.user).count()
    total_comments = Comment.objects.filter(poll__creator=request.user).count()
    total_polls = polls.count()
    total_views = polls.aggregate(total_views=Sum("view_count"))["total_views"] or 0

    response_rate = int(min((total_votes / total_polls * 100), 100)) if total_polls > 0 else 0
    engagement_rate = int(((total_votes + total_comments) / (total_polls * 2)) * 100) if total_polls > 0 else 0

    most_engaged_poll = (
        polls.annotate(engagement=Count("poll_likes") + Count("comments"))
        .order_by("-engagement")
        .first()
    )
    most_engaged_poll_title = most_engaged_poll.title if most_engaged_poll else "N/A"

    average_votes_per_poll = int(total_votes / total_polls) if total_polls > 0 else 0
    average_comments_per_poll = int(total_comments / total_polls) if total_polls > 0 else 0

    return render(
        request,
        "polls/user_dashboard.html",
        {
            "polls_with_status": polls_with_status,
            "query": query,
            "months": months,
            "data": data,
            "response_rate": response_rate,
            "engagement_rate": engagement_rate,
            "total_votes": total_votes,
            "total_comments": total_comments,
            "total_polls": total_polls,
            "total_views": total_views,
            "most_engaged_poll_title": most_engaged_poll_title,
            "average_votes_per_poll": average_votes_per_poll,
            "average_comments_per_poll": average_comments_per_poll,
        },
    )


@login_required
def delete_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id, creator=request.user)
    if request.method == "POST":
        poll.delete()
        return redirect("polls:user_dashboard")


@login_required
def edit_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id, creator=request.user)
    existing_options = poll.options.all()

    error_message = None

    if request.method == "POST":
        poll_form = EditPollForm(request.POST, request.FILES, instance=poll)
        option_formset = OptionFormSet(request.POST, request.FILES, queryset=existing_options)

        # Check if the poll type is "question" and if there are any correct answers
        if poll.poll_type == "question":
            correct_answers = any(
                option_form.cleaned_data.get("is_correct") for option_form in option_formset if option_form.is_valid()
            )
            if not correct_answers:
                error_message = "A question must have at least one correct answer."

        # Check if both forms are valid and handle saving
        if poll_form.is_valid() and option_formset.is_valid() and not error_message:
            poll = poll_form.save()

            # Save the banner image if it exists
            if "banner_image" in request.FILES:
                poll.banner_image = request.FILES["banner_image"]
                poll.save()

            # Save options from the formset
            for option_form in option_formset:
                if option_form.cleaned_data.get("option_text") or option_form.cleaned_data.get("option_image"):
                    option = option_form.save(commit=False)
                    option.poll = poll
                    if "option_image" in option_form.cleaned_data and option_form.cleaned_data["option_image"]:
                        option.option_image = option_form.cleaned_data["option_image"]
                    option.save()
                    

            return redirect("polls:user_dashboard")
        else:
            logger.error("Poll Form Errors: %s", poll_form.errors)
            logger.error("Option Formset Errors: %s", option_formset.errors)
            error_message = error_message or "There were errors in the form. Please check the fields."

    else:
        # Initialize the forms with the existing poll and options data
        poll_form = EditPollForm(instance=poll)
        option_formset = OptionFormSet(queryset=existing_options)

    return render(
        request,
        "polls/edit_poll.html",
        {
            "poll_form": poll_form,
            "option_formset": option_formset,
            "poll": poll,
            "error_message": error_message,  # Pass error_message to the template
        },
    )


@login_required
def vote_poll(request, poll_id):
    # Attempt to retrieve the poll; will raise 404 if it doesn't exist
    poll = get_object_or_404(Poll, id=poll_id)

    # Check if the poll is expired
    expiration_status = poll.check_expiration()
    if expiration_status["expired"]:
        if expiration_status["redirect"]:
            return redirect("polls:poll_results", poll_id=poll.id)
        else:
            return HttpResponse(
                "This poll has expired and is not public. You cannot vote on this poll."
            )

    # Increment view count if not viewed before
    if not request.session.get(f"viewed_poll_{poll.id}", False):
        poll.increment_view_count()
        request.session[f"viewed_poll_{poll.id}"] = True

    options = poll.options.all()
    user_vote = Vote.objects.filter(poll=poll, user=request.user).first()
    has_reached_vote_limit = False

    if user_vote and not user_vote.can_vote_again():
        has_reached_vote_limit = True

    utc_now = timezone.now()
    kenyan_tz = pytz.timezone("Africa/Nairobi")
    now = utc_now.astimezone(kenyan_tz)

    time_limit = now - timedelta(minutes=30)

    if request.method == "POST":
        if "cancel_vote" in request.POST and user_vote and user_vote.can_vote_again():
            if (
                poll.poll_type == "opinion"
                and user_vote.created_at >= time_limit
                and poll.is_active
            ):
                # Increment the attempts in Poll
                poll.attempts += 1
                poll.save()  # Save the updated attempts
                user_vote.delete()  # Delete the existing vote
                return redirect("polls:vote_poll", poll_id=poll.id)

        # Voting logic
        selected_options = (
            request.POST.getlist("option")
            if poll.multi_option
            else [request.POST.get("option")]
        )

        if not user_vote or user_vote.can_vote_again():
            if poll.multi_option:
                for option_id in selected_options:
                    option = get_object_or_404(Option, id=option_id)
                    Vote.objects.create(poll=poll, option=option, user=request.user)
            else:
                option_id = selected_options[0]
                option = get_object_or_404(Option, id=option_id)
                if user_vote:
                    user_vote.option = option
                    user_vote.created_at = timezone.now()
                    user_vote.save()
                else:
                    Vote.objects.create(poll=poll, option=option, user=request.user)

            # Increment the attempts in Poll
            poll.attempts += 1
            poll.save()

            return redirect("polls:vote_poll", poll_id=poll.id)

    remaining_attempts = 2 - poll.attempts
    return render(
        request,
        "polls/vote.html",
        {
            "poll": poll,
            "options": options,
            "multi_option": poll.multi_option,
            "user_vote": user_vote,
            "has_reached_vote_limit": has_reached_vote_limit,
            "qr_code_url": poll.qr_code.url if poll.qr_code else None,
            "poll_link": poll.link,
            "remaining_attempts": remaining_attempts,
            "now": now,
            "time_limit": time_limit,
        },
    )


def poll_results(request, poll_id):
    # Fetch the poll and options
    poll = get_object_or_404(Poll, id=poll_id)
    options = Option.objects.filter(poll=poll)
    total_votes = poll.total_votes()  # Total votes across all options
    results = []

    top_voted_option = None
    max_votes = 0

    # Populate results and find the top-voted option
    for option in options:
        is_correct = option.is_correct
        votes = option.votes.count()

        # Get scored users if the poll is public
        scored_users = (
            option.votes.values_list("user__username", flat=True)
            if poll.is_public
            else []
        )

        # Get failed users if the option is incorrect
        failed_users = []
        if not is_correct:
            failed_users = option.votes.values_list("user__username", flat=True)

        percentage = (votes / total_votes * 100) if total_votes > 0 else 0
        results.append(
            {
                "option_text": option.option_text,
                "is_correct": is_correct,
                "votes": votes,
                "scored_users": scored_users,
                "failed_users": failed_users,
                "percentage": percentage,
                "option_image": option.option_image if option.option_image else None,
            }
        )

        # Determine the top-voted option
        if votes > max_votes:
            max_votes = votes
            top_voted_option = option.option_text

    # Generate the QR code
    result_link = (
        f"http://127.0.0.1:8000{reverse('polls:poll_results', args=[poll.id])}"
    )
    qr_code = qrcode.make(result_link)
    buffer = BytesIO()
    qr_code.save(buffer, format="PNG")
    result_qr_code_url = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Add data to context
    context = {
        "poll": poll,
        "results": results,
        "total_votes": total_votes,
        "top_voted_option": top_voted_option,
        "qr_code_url": result_qr_code_url,
        "poll_link": result_link,
    }

    return render(request, "polls/poll_results.html", context)


@login_required
def add_comment(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if request.method == "POST":
        # Extract comment text from the JSON request
        data = json.loads(request.body)
        comment_text = data.get("comment")

        # Set created_at to Nairobi time
        nairobi_tz = pytz.timezone("Africa/Nairobi")
        created_at_nairobi = timezone.now().astimezone(nairobi_tz)

        # Create the comment, setting created_at automatically with auto_now_add
        comment = Comment.objects.create(
            poll=poll,
            user=request.user,
            text=comment_text,
            created_at=created_at_nairobi,
        )

        # Return a JSON response with the comment data
        return JsonResponse(
            {
                "success": True,
                "user": request.user.username,
                "comment_text": comment.text,
            }
        )

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def like_comment(request, comment_id):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        comment = get_object_or_404(Comment, id=comment_id)
        user = request.user
        existing_like = Like.objects.filter(user=user, comment=comment).first()

        if existing_like:
            existing_like.delete()
            liked = False
        else:
            Like.objects.create(user=user, comment=comment)
            liked = True

        total_likes = comment.comment_likes.count()

        return JsonResponse(
            {"success": True, "total_likes": total_likes, "liked": liked}
        )

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required
def like_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    # Check if the user has already liked the poll
    existing_like = Like.objects.filter(
        user=request.user, poll=poll, comment=None
    ).first()

    if not existing_like:
        # Create a new like
        Like.objects.create(user=request.user, poll=poll)
        liked = True
    else:
        existing_like.delete()
        liked = False

    total_likes = poll.poll_likes.count()

    return JsonResponse({"success": True, "liked": liked, "total_likes": total_likes})


def archived_polls_view(request):
    query = request.GET.get("query", "")
    current_time = timezone.now()

    # Retrieve all archived polls
    archived_polls = Poll.objects.filter(
        allow_expiration=True, expiration_time__lt=current_time
    ).order_by("-expiration_time")

    # Retrieve user archived polls
    optional_polls_archived = Poll.objects.filter(is_archived=True)
    archived_results = Poll.objects.filter(Q(is_archived_results=True))


    if query:
        archived_polls = archived_polls.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        optional_polls_archived = optional_polls_archived.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    liked_polls_set = set()

    # Get popular polls
    popular_polls = (
        Poll.objects.filter(view_count__gt=10)
        .exclude(expiration_time__lt=current_time)
        .filter(Q(expiration_time__lt=current_time) & Q(allow_expiration=True))
        .distinct()
        .order_by("-view_count")
    )

    # Check if the user is authenticated and get liked polls
    if request.user.is_authenticated:
        liked_polls_set = set(
            Like.objects.filter(user=request.user, poll__in=archived_polls).values_list(
                "poll_id", flat=True
            )
        )

    no_polls_message = None
    if not archived_polls.exists() and not optional_polls_archived.exists():
        no_polls_message = "No archived polls found matching your search criteria."

    # Combine both querysets into one list
    combined_polls = list(chain(archived_polls, optional_polls_archived))

    return render(
        request,
        "polls/archived_polls.html",
        {
            "combined_polls": combined_polls,
            "liked_polls_set": liked_polls_set,
            "query": query,
            "archived_polls": archived_polls,
            "archived_results" : archived_results,
            "optional_polls_archived": optional_polls_archived,
            "popular_polls": popular_polls,
            "no_polls_message": no_polls_message,  # Include the message in the context
        },
    )




@login_required
def archive_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id, creator=request.user)
    poll.archive()  # Toggle the archived state
    return JsonResponse(
        {
            "success": True,
            "is_archived": poll.is_archived,
            "message": "Poll archived successfully.",
        }
    )

@login_required
def archive_poll_results(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id, creator=request.user)
    poll.archived_results()  # Toggle the archived state
    return JsonResponse(
        {
            "success": True,
            "is_archived_results": poll.is_archived_results,
            "message": "Poll archived successfully.",
        }
    )

