from django.urls import path
from . import views

urlpatterns = [
    path('', views.resources , name='resources'),
    path('link', views.new_resource_link, name='link'),
    path('file', views.new_resource_file, name='file')
]