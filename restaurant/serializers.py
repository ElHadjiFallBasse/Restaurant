from rest_framework import serializers
from .models import (
    Category, MenuItem, Table, Customer, Staff, Order, 
    OrderItem, Reservation, Inventory
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'category', 'category_name',
            'is_available', 'preparation_time', 'ingredients', 'allergens',
            'created_at', 'updated_at'
        ]

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'number', 'capacity', 'is_available', 'location']

class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'address', 'date_of_birth', 'loyalty_points', 'created_at'
        ]

class StaffSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'id', 'user', 'user_name', 'role', 'phone', 'hire_date',
            'salary', 'is_active'
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'menu_item_name', 'quantity', 'unit_price',
            'total_price', 'special_instructions'
        ]

class OrderSerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(source='table.number', read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    waiter_name = serializers.CharField(source='waiter.user.get_full_name', read_only=True)
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'table', 'table_number', 'customer', 'customer_name',
            'waiter', 'waiter_name', 'status', 'payment_method', 'subtotal',
            'tax_amount', 'total_amount', 'discount', 'notes', 'created_at',
            'updated_at', 'served_at', 'paid_at', 'items'
        ]

class ReservationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    table_number = serializers.IntegerField(source='table.number', read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'customer', 'customer_name', 'table', 'table_number',
            'date', 'time', 'party_size', 'status', 'special_requests',
            'created_at', 'updated_at'
        ]

class InventorySerializer(serializers.ModelSerializer):
    needs_restock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'name', 'unit', 'current_stock', 'minimum_stock',
            'needs_restock', 'cost_per_unit', 'supplier', 'last_restocked'
        ]