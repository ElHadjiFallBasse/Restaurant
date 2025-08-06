from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Menu
    path('menu/', views.menu_list, name='menu_list'),
    
    # Orders
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Tables
    path('tables/', views.tables_status, name='tables_status'),
    path('tables/<int:table_id>/toggle/', views.toggle_table_availability, name='toggle_table_availability'),
    
    # Customers
    path('customers/', views.customers_list, name='customers_list'),
    
    # Reservations
    path('reservations/', views.reservations_list, name='reservations_list'),
    
    # Inventory
    path('inventory/', views.inventory_list, name='inventory_list'),
]