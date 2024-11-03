# events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import api_views, views

# Create a router for the main viewset
router = routers.DefaultRouter()
router.register(r'events', api_views.EventViewSet, basename='event')

# Create a nested router for comments
event_router = routers.NestedDefaultRouter(router, r'events', lookup='event')
event_router.register(r'comments', api_views.CommentViewSet, basename='event-comments')

app_name = 'events'

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    path('api/', include(event_router.urls)),
    
    # Traditional URLs
    path('', views.event_list, name='event_list'),
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('create/', views.create_event, name='create_event'),
    path('<int:event_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('<int:event_id>/react/', views.toggle_reaction, name='toggle_reaction'),
    path('university/autocomplete/', views.campus_autocomplete, name='university_autocomplete'),
    path('select2/', include('django_select2.urls')),
    path('<int:event_id>/comments/', views.load_more_comments, name='load_more_comments'),
    # urls.py
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]