from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from django.contrib.auth import get_user_model
from django.db.models import Q, Exists, OuterRef

User = get_user_model()

@login_required
def chat_room(request, username):
    other_user = get_object_or_404(User, username=username)
    conversation, created = Conversation.objects.get_or_create_conversation(request.user, other_user)
    
    # Fetch messages for this conversation
    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
    
    return render(request, 'messaging/alternate.html', {
        'conversation': conversation,
        'other_user': other_user,
        'conversation_id': conversation.id,
        'messages': messages,  # Pass messages to the template
    })


@login_required
def inbox(request):
    # Get all users you've chatted with
    chat_users = User.objects.filter(
        conversations__participants=request.user
    ).distinct().exclude(id=request.user.id)

    # Handle search functionality
    search_query = request.GET.get('q')
    if search_query:
        users = User.objects.filter(
            Q(username__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        ).exclude(id=request.user.id).annotate(
            is_contact=Exists(
                Conversation.objects.filter(
                    participants=request.user
                ).filter(
                    participants=OuterRef('pk')
                )
            )
        )
    else:
        users = None

    return render(request, 'messaging/inbox.html', {
        'chat_users': chat_users,
        'users': users,
        'search_query': search_query
    })

