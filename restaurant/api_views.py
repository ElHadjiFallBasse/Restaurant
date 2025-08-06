from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import (
    Category, MenuItem, Table, Customer, Staff, Order, 
    OrderItem, Reservation, Inventory
)
from .serializers import (
    CategorySerializer, MenuItemSerializer, TableSerializer, CustomerSerializer,
    StaffSerializer, OrderSerializer, OrderItemSerializer, ReservationSerializer,
    InventorySerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description', 'ingredients']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['category', 'name']
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Obtenir seulement les plats disponibles"""
        available_items = self.get_queryset().filter(is_available=True)
        serializer = self.get_serializer(available_items, many=True)
        return Response(serializer.data)

class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_available', 'capacity']
    ordering_fields = ['number', 'capacity']
    ordering = ['number']
    
    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """Basculer la disponibilité d'une table"""
        table = self.get_object()
        table.is_available = not table.is_available
        table.save()
        serializer = self.get_serializer(table)
        return Response({
            'message': f'Table {table.number} est maintenant {"disponible" if table.is_available else "occupée"}',
            'table': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Obtenir seulement les tables disponibles"""
        available_tables = self.get_queryset().filter(is_available=True)
        serializer = self.get_serializer(available_tables, many=True)
        return Response(serializer.data)

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['last_name', 'first_name', 'created_at', 'loyalty_points']
    ordering = ['last_name', 'first_name']
    
    @action(detail=False, methods=['get'])
    def top_customers(self, request):
        """Obtenir les meilleurs clients par points de fidélité"""
        top_customers = self.get_queryset().order_by('-loyalty_points')[:10]
        serializer = self.get_serializer(top_customers, many=True)
        return Response(serializer.data)

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.select_related('user').all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['user__last_name', 'hire_date', 'salary']
    ordering = ['user__last_name']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Obtenir seulement le personnel actif"""
        active_staff = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_staff, many=True)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('table', 'customer', 'waiter').prefetch_related('orderitem_set__menu_item').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'table', 'waiter']
    search_fields = ['order_number', 'customer__first_name', 'customer__last_name']
    ordering_fields = ['created_at', 'total_amount', 'order_number']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'une commande"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Statut invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        if new_status == 'served':
            from django.utils import timezone
            order.served_at = timezone.now()
        elif new_status == 'paid':
            from django.utils import timezone
            order.paid_at = timezone.now()
        
        order.save()
        serializer = self.get_serializer(order)
        return Response({
            'message': f'Statut mis à jour: {order.get_status_display()}',
            'order': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def calculate_total(self, request, pk=None):
        """Recalculer le total d'une commande"""
        order = self.get_object()
        order.calculate_total()
        serializer = self.get_serializer(order)
        return Response({
            'message': 'Total recalculé',
            'order': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Obtenir les commandes d'aujourd'hui"""
        from django.utils import timezone
        today = timezone.now().date()
        today_orders = self.get_queryset().filter(created_at__date=today)
        serializer = self.get_serializer(today_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Obtenir les commandes en attente"""
        pending_orders = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(pending_orders, many=True)
        return Response(serializer.data)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related('order', 'menu_item').all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'menu_item']
    ordering_fields = ['order__created_at', 'menu_item__name']
    ordering = ['-order__created_at']

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related('customer', 'table').all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'date', 'table']
    search_fields = ['customer__first_name', 'customer__last_name']
    ordering_fields = ['date', 'time', 'created_at']
    ordering = ['date', 'time']
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Obtenir les réservations d'aujourd'hui"""
        from django.utils import timezone
        today = timezone.now().date()
        today_reservations = self.get_queryset().filter(date=today)
        serializer = self.get_serializer(today_reservations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Obtenir les prochaines réservations"""
        from django.utils import timezone
        now = timezone.now()
        upcoming_reservations = self.get_queryset().filter(
            date__gte=now.date(),
            status__in=['pending', 'confirmed']
        ).order_by('date', 'time')[:10]
        serializer = self.get_serializer(upcoming_reservations, many=True)
        return Response(serializer.data)

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'supplier']
    ordering_fields = ['name', 'current_stock', 'last_restocked']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Obtenir les articles avec un stock bas"""
        from django.db import models
        low_stock_items = self.get_queryset().filter(
            current_stock__lte=models.F('minimum_stock')
        )
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def restock(self, request, pk=None):
        """Réapprovisionner un article"""
        item = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        try:
            quantity = float(quantity)
            if quantity <= 0:
                return Response(
                    {'error': 'La quantité doit être positive'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item.current_stock += quantity
            from django.utils import timezone
            item.last_restocked = timezone.now()
            item.save()
            
            serializer = self.get_serializer(item)
            return Response({
                'message': f'{quantity} {item.unit} ajoutées au stock',
                'item': serializer.data
            })
            
        except ValueError:
            return Response(
                {'error': 'Quantité invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )