from django.urls import path
from . import views


app_name = "marketplace"
urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('add/', views.add_item, name='add_item'),   
    path('dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('item/<int:item_id>/mark_as_sold/', views.mark_as_sold, name='mark_as_sold'),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'), 
]
