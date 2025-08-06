from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Category, MenuItem, Table, Customer, Staff, Order, 
    OrderItem, Reservation, Inventory
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    ordering = ['name']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'preparation_time']
    list_filter = ['category', 'is_available', 'created_at']
    search_fields = ['name', 'description', 'ingredients']
    list_editable = ['is_available', 'price']
    ordering = ['category', 'name']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'category', 'price')
        }),
        ('Disponibilité et temps', {
            'fields': ('is_available', 'preparation_time')
        }),
        ('Détails', {
            'fields': ('ingredients', 'allergens'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'capacity', 'is_available', 'location']
    list_filter = ['is_available', 'capacity']
    list_editable = ['is_available']
    ordering = ['number']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'loyalty_points', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    list_filter = ['created_at', 'date_of_birth']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'date_of_birth')
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Fidélité', {
            'fields': ('loyalty_points',)
        }),
    )

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user_full_name', 'role', 'hire_date', 'salary', 'is_active']
    list_filter = ['role', 'is_active', 'hire_date']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    list_editable = ['is_active']
    ordering = ['user__last_name', 'user__first_name']
    
    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = 'Nom complet'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']
    fields = ['menu_item', 'quantity', 'unit_price', 'total_price', 'special_instructions']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'table', 'customer', 'waiter', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at', 'waiter']
    search_fields = ['order_number', 'customer__first_name', 'customer__last_name']
    list_editable = ['status']
    ordering = ['-created_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('order_number', 'table', 'customer', 'waiter', 'status')
        }),
        ('Paiement', {
            'fields': ('payment_method', 'subtotal', 'tax_amount', 'discount', 'total_amount')
        }),
        ('Dates', {
            'fields': ('served_at', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ['table', 'customer']
        return self.readonly_fields

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'unit_price', 'total_price']
    list_filter = ['order__status', 'menu_item__category']
    search_fields = ['order__order_number', 'menu_item__name']
    ordering = ['-order__created_at']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['customer', 'table', 'date', 'time', 'party_size', 'status']
    list_filter = ['status', 'date', 'table']
    search_fields = ['customer__first_name', 'customer__last_name']
    list_editable = ['status']
    ordering = ['date', 'time']
    
    fieldsets = (
        ('Informations de réservation', {
            'fields': ('customer', 'table', 'date', 'time', 'party_size')
        }),
        ('Statut et demandes', {
            'fields': ('status', 'special_requests')
        }),
    )

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'current_stock', 'unit', 'minimum_stock', 'needs_restock_display', 'cost_per_unit', 'supplier']
    list_filter = ['unit', 'supplier', 'last_restocked']
    search_fields = ['name', 'supplier']
    ordering = ['name']
    
    def needs_restock_display(self, obj):
        if obj.needs_restock:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Réapprovisionner</span>')
        return format_html('<span style="color: green;">✅ Stock OK</span>')
    needs_restock_display.short_description = 'État du stock'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'unit', 'supplier')
        }),
        ('Stock', {
            'fields': ('current_stock', 'minimum_stock', 'last_restocked')
        }),
        ('Coût', {
            'fields': ('cost_per_unit',)
        }),
    )

# Personnalisation de l'interface d'administration
admin.site.site_header = "Administration Restaurant"
admin.site.site_title = "Restaurant Admin"
admin.site.index_title = "Gestion du Restaurant"
