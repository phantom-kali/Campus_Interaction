import logging
from notifications.bulk import notify_all_users
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from profiles.models import Profile
from .models import Event, EventRegistration, Comment, EventReaction
from .forms import EventForm, CommentForm, EventRegistrationForm
import json
from django.core.paginator import EmptyPage, InvalidPage
from django.template.loader import render_to_string
from django.db.models import Count

# Set up logging
logger = logging.getLogger(__name__)

# events/views.py

@login_required
def event_list(request):
    status_filter = request.GET.get('status')
    campus_filter = request.GET.get('campus')

    events = Event.objects.all().order_by('-start_date').prefetch_related('comments')


    # Fetch all events and related data
    events = Event.objects.all().order_by('-start_date').prefetch_related('comments')

    # Apply status filter if present

    if status_filter:
        now = timezone.now()
        if status_filter == 'upcoming':
            events = events.filter(start_date__gte=now)
        elif status_filter == 'ongoing':
            events = events.filter(start_date__lte=now, end_date__gte=now)
        elif status_filter == 'completed':
            events = events.filter(end_date__lt=now)
            
    if campus_filter:
        events = events.filter(campus__campus=campus_filter)

    # Get unique campus values from Profile model
    campuses = Profile.objects.values_list('campus', flat=True).distinct()

    paginator = Paginator(events, 12)
    page = request.GET.get('page')
    events = paginator.get_page(page)

    for event in events:
        event.comments_count = event.comments.count()

    return render(request, 'events/event_list.html')

    # Apply campus filter if present
    if campus_filter:
        events = events.filter(campus=campus_filter)

    # Get unique campuses for the filter form
    campuses = Profile.objects.values_list('campus', flat=True).distinct()

    # Pagination setup
    paginator = Paginator(events, 12)  # Show 12 events per page
    page = request.GET.get('page')
    events = paginator.get_page(page)

    # Add comments count for each event
    for event in events:
        event.comments_count = event.comments.count()

    context = {
        'events': events,
        'campuses': campuses,
    }

    # If it's an HTMX request, return only the events partial
    if request.headers.get('HX-Request'):
        return render(request, 'events/partials/event_list_content.html', context)
    
    # Otherwise return the full template
    return render(request, 'events/event_list.html', context)

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    user_registered = EventRegistration.objects.filter(event=event, participant=user_profile).exists()

    # Fetch top-level comments only and prefetch related replies and likes
    comments = event.comments.filter(parent=None).prefetch_related('replies', 'likes')
    comment_form = CommentForm()

    if request.method == 'POST':
        # Handle registration
        if 'register' in request.POST:
            registration_form = EventRegistrationForm(data=request.POST, event=event)
            if registration_form.is_valid():
                EventRegistration.objects.create(event=event, participant=user_profile)
                messages.success(request, "Successfully registered for the event!")
                return redirect('event_detail', event_id=event_id)
            else:
                messages.error(request, "Invalid registration details. Please try again.")

    context = {
        'event': event,
        'user_registered': user_registered,
        'comment_form': comment_form,
        'comments': comments,
        'registration_form': EventRegistrationForm(event=event)
    }
    return render(request, 'events/event_detail.html', context)

@login_required
@transaction.atomic
def create_event(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                event = form.save(commit=False)
                event.organizer = user_profile
                event.campus = user_profile.campus
                event.save()
                isPublic = form.cleaned_data['is_public']
                if isPublic == True:
                    notify_all_users("New Event") # notify all users for upcoming event if made public
                messages.success(request, "Event created successfully!")
                return redirect('events:event_list')
            except Exception as e:
                messages.error(request, f"An error occurred while saving the event: {e}")
        else:
            messages.error(request, "Invalid form submission.")
            print(form.errors)  # Print form errors to console for debugging
    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})
@login_required
def load_more_comments(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    page = request.GET.get('page', 1)
    comments = Comment.objects.filter(event=event).order_by('-created_at')
    paginator = Paginator(comments, 5)  # Display 5 comments per page

    if int(page) > paginator.num_pages:
        return JsonResponse({'comments_html': ''})  # No more pages

    comments_page = paginator.get_page(page)
    comments_html = render(request, 'events/partials/comments_pagination.html', {
        'comments': comments_page,
    }).content.decode('utf-8')


# views.py
@login_required
@require_POST
@require_http_methods(["POST"])
def add_comment(request, event_id):
    """Add a new comment or reply to an event."""
    try:
        # Get the event
        event = get_object_or_404(Event, id=event_id)

        # Create a form instance with the POST data
        form = CommentForm(request.POST)

        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if form.is_valid():
            # Create comment instance but don't save yet
            comment = form.save(commit=False)
            comment.event = event
            comment.user = request.user.profile  # Assuming you have a profile relation

            # Handle parent comment for replies
            parent_id = request.POST.get('parent_comment_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    if is_ajax:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Parent comment not found'
                        }, status=400)
                    else:
                        messages.error(request, 'Parent comment not found')
                        return redirect('events:event_detail', event_id=event_id)

            # Save the comment
            comment.save()

            if is_ajax:
                # Render the comment HTML
                comment_html = render_to_string('events/partials/comment.html', {
                    'comment': comment,
                    'event': event
                }, request=request)

                return JsonResponse({
                    'status': 'success',
                    'comment_html': comment_html,
                    'comment_id': comment.id
                })
            else:
                messages.success(request, 'Comment added successfully!')
                return redirect('events:event_detail', event_id=event_id)
        else:
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                }, status=400)
            else:
                messages.error(request, 'Please correct the errors below.')
                return redirect('events:event_detail', event_id=event_id)

    except Exception as e:
        print(f"Error in add_comment: {str(e)}")  # Add logging for debugging
        if is_ajax:
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while processing your request'
            }, status=500)
        else:
            messages.error(request, 'An error occurred while processing your request')
            return redirect('events:event_detail', event_id=event_id)

@login_required
@require_http_methods(["DELETE"])
def delete_comment(request, comment_id):
    """Delete a comment or reply."""
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if the user is the owner of the comment
        if comment.user != request.user.profile:
            return JsonResponse({
                'status': 'error',
                'message': 'You do not have permission to delete this comment'
            }, status=403)
        
        comment.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Comment deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while deleting the comment'
        }, status=500)@login_required
def load_more_comments(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    page = int(request.GET.get('page', 1))
    comments_per_page = 5

    comments = Comment.objects.filter(
        event=event,
        parent=None
    ).select_related(
        'user__user'
    ).prefetch_related(
        'replies'
    ).order_by('-created_at')

    paginator = Paginator(comments, comments_per_page)

    try:
        comments_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        return JsonResponse({'comments_html': '', 'has_next': False})

    comments_html = render_to_string(
        'events/partials/comments_pagination.html',
        {'comments': comments_page, 'event': event},
        request=request
    )

    return JsonResponse({
        'comments_html': comments_html,
        'has_next': comments_page.has_next()
    })
@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user_profile = request.user.profile

    if user_profile in comment.likes.all():  # Check if user already liked the comment
        comment.likes.remove(user_profile)
        liked = False
    else:
        comment.likes.add(user_profile)
        liked = True

    return JsonResponse({
        'status': 'success',
        'liked': liked,
        'likes_count': comment.likes.count()
    })

@login_required
@require_http_methods(["POST", "DELETE"])
@transaction.atomic
def delete_event(request, event_id):
    # Fetch the event or return 404 if it doesn't exist
    event = get_object_or_404(Event, id=event_id)

    # Permission check
    if event.organizer.user != request.user and not request.user.is_staff:
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)

    # Attempt to delete image if exists
    image_path = event.image.path if event.image else None
    event.delete()  # Delete event from the database

    # Delete associated media file if it exists
    if image_path:
        try:
            default_storage.delete(image_path)
        except Exception as e:
            logger.error(f"Error deleting file {image_path}: {e}")
            return JsonResponse({
                "status": "success",
                "message": "Event deleted, but media file removal failed."
            }, status=500)

    # Use Django messages for UI feedback and return JSON response
    messages.success(request, "Event deleted successfully.")
    return JsonResponse({"status": "success", "message": "Event deleted successfully."})

@login_required
@require_POST
def toggle_reaction(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        reaction_type = request.POST.get('reaction_type')

        if reaction_type not in dict(EventReaction.REACTION_CHOICES):
            return JsonResponse({'status': 'error', 'message': 'Invalid reaction type'}, status=400)

        reaction, created = EventReaction.objects.get_or_create(
            event=event,
            user=request.user.profile,
            defaults={'reaction_type': reaction_type}
        )

        if not created:
            if reaction.reaction_type == reaction_type:
                reaction.delete()
                return JsonResponse({'status': 'removed', 'reaction_type': reaction_type})
            else:
                reaction.reaction_type = reaction_type
                reaction.save()

        return JsonResponse({'status': 'success', 'reaction_type': reaction_type})

    return JsonResponse({'status': 'error'}, status=400)

@login_required
def campus_autocomplete(request):
    if 'term' in request.GET:
        query = request.GET.get('term')

        # Query for campus using Profile model
        campuses = Profile.objects.filter(
            Q(campus__icontains=query)
        ).values('id', 'campus').distinct()[:10]

        # Format the results to return campus data
        results = [{'id': profile['id'], 'label': profile['campus'], 'value': profile['campus']} for profile in campuses]
        return JsonResponse(results, safe=False)

    return JsonResponse([], safe=False)
