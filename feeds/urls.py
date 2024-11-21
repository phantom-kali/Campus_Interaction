from django.urls import path
from . import views

app_name = 'feeds'

urlpatterns = [
    path('feeds/', views.feed_list, name='feed_list'),
    path('feeds/trending/', views.trending_feed, name='trending_feed'),
    path('feeds/create/', views.create_post, name='create_post'),
    path('feeds/post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('feeds/load-more/', views.load_more_posts, name='load_more_posts'),
    path('feeds/post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('feeds/post/<int:post_id>/comments/', views.load_comments, name='load_comments'),
    path('feeds/post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('feeds/comment/<int:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('feeds/post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('feeds/post/<int:post_id>/report/', views.report_post, name='report_post'),
    path('feeds/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]
