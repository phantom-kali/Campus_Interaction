# events/api_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, EventRegistration, Comment
from .serializers import (
    EventSerializer, EventRegistrationSerializer,
    CommentSerializer
)
from .filters import EventFilter


class IsOrganizerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer.user == request.user or request.user.is_staff


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]
    filterset_class = EventFilter  # Use the custom EventFilter class
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'created_at']

    def get_queryset(self):
        # Optimize queryset with related fields
        return Event.objects.all().select_related(
            'category', 'university', 'organizer'
        ).prefetch_related('comments', 'reactions')

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user.profile)

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        event = self.get_object()
        serializer = EventRegistrationSerializer(
            data={'event': event.id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(participant=request.user.profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(
            event_id=self.kwargs['event_pk']
        ).select_related('user').prefetch_related('likes', 'replies')

    def perform_create(self, serializer):
        event = Event.objects.get(pk=self.kwargs['event_pk'])
        serializer.save(event=event, user=self.request.user.profile)

    @action(detail=True, methods=['post'])
    def like(self, request, event_pk=None, pk=None):
        comment = self.get_object()
        user_profile = request.user.profile
        
        if user_profile in comment.likes.all():
            comment.likes.remove(user_profile)
            liked = False
        else:
            comment.likes.add(user_profile)
            liked = True
        
        return Response({
            'liked': liked,
            'likes_count': comment.likes.count()
        })
        
        
        
