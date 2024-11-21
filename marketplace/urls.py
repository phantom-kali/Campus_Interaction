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
    path('items/', views.item_list, name='item_search'),  
    path('items/<int:item_id>/like/', views.like_item, name='like_item'),
    path('item/update/<int:item_id>/', views.update_item_view, name='update_item'),
    path('items/<int:item_id>/rate/', views.rate_item, name='rate_item'),
    path('items/<int:item_id>/add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_page, name='cart_page'),
    path('remove-cart-item/', views.remove_cart_item, name='remove_cart_item'),
]
