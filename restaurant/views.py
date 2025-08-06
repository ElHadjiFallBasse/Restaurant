from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .models import (
    Category, MenuItem, Table, Customer, Staff, Order, 
    OrderItem, Reservation, Inventory
)
from .forms import OrderForm, OrderItemForm, ReservationForm, CustomerForm

@login_required
def dashboard(request):
    """Tableau de bord principal"""
    today = timezone.now().date()
    
    # Statistiques du jour
    today_orders = Order.objects.filter(created_at__date=today)
    today_revenue = today_orders.filter(status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Statistiques générales
    stats = {
        'orders_today': today_orders.count(),
        'revenue_today': today_revenue,
        'tables_occupied': Table.objects.filter(is_available=False).count(),
        'total_tables': Table.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'preparing_orders': Order.objects.filter(status='preparing').count(),
        'customers_count': Customer.objects.count(),
        'staff_active': Staff.objects.filter(is_active=True).count(),
    }
    
    # Commandes récentes
    recent_orders = Order.objects.select_related('table', 'customer', 'waiter').order_by('-created_at')[:10]
    
    # Réservations du jour
    today_reservations = Reservation.objects.filter(date=today).select_related('customer', 'table')
    
    # Articles en rupture de stock
    from django.db import models
    low_stock_items = Inventory.objects.filter(
        current_stock__lte=models.F('minimum_stock')
    )[:5]
    
    context = {
        'stats': stats,
        'recent_orders': recent_orders,
        'today_reservations': today_reservations,
        'low_stock_items': low_stock_items,
    }
    
    return render(request, 'restaurant/dashboard.html', context)

@login_required
def menu_list(request):
    """Liste des plats du menu"""
    categories = Category.objects.prefetch_related('menuitem_set').all()
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    menu_items = MenuItem.objects.select_related('category')
    
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(ingredients__icontains=search_query)
        )
    
    if category_filter:
        menu_items = menu_items.filter(category_id=category_filter)
    
    menu_items = menu_items.order_by('category', 'name')
    
    paginator = Paginator(menu_items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    
    return render(request, 'restaurant/menu_list.html', context)

@login_required
def orders_list(request):
    """Liste des commandes"""
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    orders = Order.objects.select_related('table', 'customer', 'waiter')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date=filter_date)
        except ValueError:
            pass
    
    orders = orders.order_by('-created_at')
    
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'restaurant/orders_list.html', context)

@login_required
def order_detail(request, order_id):
    """Détail d'une commande"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.orderitem_set.select_related('menu_item').all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'restaurant/order_detail.html', context)

@login_required
def create_order(request):
    """Créer une nouvelle commande"""
    if request.method == 'POST':
        # Logique de création de commande
        table_id = request.POST.get('table')
        customer_id = request.POST.get('customer')
        
        table = get_object_or_404(Table, id=table_id)
        customer = None
        if customer_id:
            customer = get_object_or_404(Customer, id=customer_id)
        
        # Créer la commande
        order = Order.objects.create(
            table=table,
            customer=customer,
            waiter=request.user.staff if hasattr(request.user, 'staff') else None
        )
        
        messages.success(request, f'Commande {order.order_number} créée avec succès.')
        return redirect('order_detail', order_id=order.id)
    
    # GET request
    tables = Table.objects.filter(is_available=True)
    customers = Customer.objects.all()
    
    context = {
        'tables': tables,
        'customers': customers,
    }
    
    return render(request, 'restaurant/create_order.html', context)

@login_required
def tables_status(request):
    """État des tables"""
    tables = Table.objects.all().order_by('number')
    
    # Ajouter les informations sur les commandes actives
    for table in tables:
        active_order = Order.objects.filter(
            table=table,
            status__in=['pending', 'confirmed', 'preparing', 'ready', 'served']
        ).first()
        table.active_order = active_order
    
    context = {
        'tables': tables,
    }
    
    return render(request, 'restaurant/tables_status.html', context)

@login_required
def customers_list(request):
    """Liste des clients"""
    search_query = request.GET.get('search', '')
    
    customers = Customer.objects.all()
    
    if search_query:
        customers = customers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    customers = customers.order_by('last_name', 'first_name')
    
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'restaurant/customers_list.html', context)

@login_required
def reservations_list(request):
    """Liste des réservations"""
    date_filter = request.GET.get('date', timezone.now().date())
    status_filter = request.GET.get('status', '')
    
    reservations = Reservation.objects.select_related('customer', 'table')
    
    if date_filter:
        try:
            if isinstance(date_filter, str):
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            else:
                filter_date = date_filter
            reservations = reservations.filter(date=filter_date)
        except ValueError:
            filter_date = timezone.now().date()
            reservations = reservations.filter(date=filter_date)
    
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    reservations = reservations.order_by('date', 'time')
    
    context = {
        'reservations': reservations,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'status_choices': Reservation.STATUS_CHOICES,
    }
    
    return render(request, 'restaurant/reservations_list.html', context)

@login_required
def inventory_list(request):
    """Liste de l'inventaire"""
    low_stock_only = request.GET.get('low_stock', False)
    search_query = request.GET.get('search', '')
    
    inventory_items = Inventory.objects.all()
    
    if low_stock_only:
        from django.db import models
        inventory_items = inventory_items.filter(
            current_stock__lte=models.F('minimum_stock')
        )
    
    if search_query:
        inventory_items = inventory_items.filter(
            Q(name__icontains=search_query) |
            Q(supplier__icontains=search_query)
        )
    
    inventory_items = inventory_items.order_by('name')
    
    context = {
        'inventory_items': inventory_items,
        'low_stock_only': low_stock_only,
        'search_query': search_query,
    }
    
    return render(request, 'restaurant/inventory_list.html', context)

# AJAX Views
@login_required
def update_order_status(request, order_id):
    """Mettre à jour le statut d'une commande via AJAX"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            if new_status == 'served':
                order.served_at = timezone.now()
            elif new_status == 'paid':
                order.paid_at = timezone.now()
            order.save()
            
            return JsonResponse({'success': True, 'status': order.get_status_display()})
        
        return JsonResponse({'success': False, 'error': 'Statut invalide'})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def toggle_table_availability(request, table_id):
    """Basculer la disponibilité d'une table via AJAX"""
    if request.method == 'POST':
        table = get_object_or_404(Table, id=table_id)
        table.is_available = not table.is_available
        table.save()
        
        return JsonResponse({
            'success': True, 
            'is_available': table.is_available,
            'status_text': 'Disponible' if table.is_available else 'Occupée'
        })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
