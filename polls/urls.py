from django.urls import path
from . import views

app_name = "polls"
urlpatterns = [
    path("", views.base_poll, name="base_poll"),
    path("add_polls/", views.add_polls, name="add_polls"),
    path("polls/search_poll/<str:title>/", views.search_poll, name="search_poll"),   
    path("polls/<int:poll_id>/vote/", views.vote_poll, name="vote_poll"),
    path("dashboard/", views.user_dashboard, name="user_dashboard"),
    path("polls/edit/<int:poll_id>/", views.edit_poll, name="edit_poll"),
    path("polls/delete/<int:poll_id>/", views.delete_poll, name="delete_poll"),
    path("polls/<int:poll_id>/results/", views.poll_results, name="poll_results"),
    path("poll/<int:poll_id>/add_comment/", views.add_comment, name="add_comment"),
    path("poll/<int:poll_id>/like/", views.like_poll, name="like_poll"),
    path("comment/<int:comment_id>/like/", views.like_comment, name="like_comment"),
    path("polls/<int:poll_id>/comments/", views.load_comments, name="load_comments"),
    path('archived-polls/', views.archived_polls_view, name='archived_polls'),
]
