from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Category(models.Model):
    """Catégorie des plats (Entrées, Plats principaux, Desserts, etc.)"""
    name = models.CharField(max_length=100, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class MenuItem(models.Model):
    """Plats du menu"""
    name = models.CharField(max_length=200, verbose_name="Nom du plat")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    preparation_time = models.PositiveIntegerField(help_text="Temps de préparation en minutes")
    ingredients = models.TextField(blank=True, verbose_name="Ingrédients")
    allergens = models.CharField(max_length=500, blank=True, verbose_name="Allergènes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plat du menu"
        verbose_name_plural = "Plats du menu"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.price}€"

class Table(models.Model):
    """Tables du restaurant"""
    number = models.PositiveIntegerField(unique=True, verbose_name="Numéro de table")
    capacity = models.PositiveIntegerField(verbose_name="Capacité")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    location = models.CharField(max_length=100, blank=True, verbose_name="Emplacement")
    
    class Meta:
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        ordering = ['number']
    
    def __str__(self):
        return f"Table {self.number} ({self.capacity} places)"

class Customer(models.Model):
    """Clients du restaurant"""
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    loyalty_points = models.PositiveIntegerField(default=0, verbose_name="Points de fidélité")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Staff(models.Model):
    """Personnel du restaurant"""
    ROLE_CHOICES = [
        ('waiter', 'Serveur'),
        ('chef', 'Chef'),
        ('manager', 'Manager'),
        ('cashier', 'Caissier'),
        ('host', 'Hôte d\'accueil'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Rôle")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    hire_date = models.DateField(verbose_name="Date d'embauche")
    salary = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Salaire")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Personnel"
        verbose_name_plural = "Personnel"
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

class Order(models.Model):
    """Commandes"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('preparing', 'En préparation'),
        ('ready', 'Prête'),
        ('served', 'Servie'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
    ]
    
    PAYMENT_CHOICES = [
        ('cash', 'Espèces'),
        ('card', 'Carte bancaire'),
        ('check', 'Chèque'),
        ('mobile', 'Paiement mobile'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Numéro de commande")
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="Table")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Client")
    waiter = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name="Serveur")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True, verbose_name="Mode de paiement")
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Sous-total")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Montant TVA")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Montant total")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Remise")
    
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    served_at = models.DateTimeField(null=True, blank=True, verbose_name="Heure de service")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Heure de paiement")
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commande {self.order_number} - Table {self.table.number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Générer un numéro de commande unique
            import uuid
            self.order_number = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculer le total de la commande"""
        items_total = sum(item.total_price for item in self.orderitem_set.all())
        self.subtotal = items_total
        self.tax_amount = items_total * Decimal('0.20')  # TVA 20%
        self.total_amount = self.subtotal + self.tax_amount - self.discount
        self.save()

class OrderItem(models.Model):
    """Articles d'une commande"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Commande")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name="Plat")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Prix unitaire")
    special_instructions = models.TextField(blank=True, verbose_name="Instructions spéciales")
    
    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
        unique_together = ['order', 'menu_item']
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.menu_item.price
        super().save(*args, **kwargs)

class Reservation(models.Model):
    """Réservations"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('seated', 'Installée'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
        ('no_show', 'Absent'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Client")
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="Table")
    date = models.DateField(verbose_name="Date")
    time = models.TimeField(verbose_name="Heure")
    party_size = models.PositiveIntegerField(verbose_name="Nombre de personnes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    special_requests = models.TextField(blank=True, verbose_name="Demandes spéciales")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['date', 'time']
        unique_together = ['table', 'date', 'time']
    
    def __str__(self):
        return f"Réservation {self.customer.full_name} - {self.date} {self.time}"

class Inventory(models.Model):
    """Inventaire des ingrédients"""
    name = models.CharField(max_length=200, verbose_name="Nom de l'ingrédient")
    unit = models.CharField(max_length=50, verbose_name="Unité de mesure")
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Stock actuel")
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Stock minimum")
    cost_per_unit = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Coût par unité")
    supplier = models.CharField(max_length=200, blank=True, verbose_name="Fournisseur")
    last_restocked = models.DateTimeField(null=True, blank=True, verbose_name="Dernier réapprovisionnement")
    
    class Meta:
        verbose_name = "Inventaire"
        verbose_name_plural = "Inventaire"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"
    
    @property
    def needs_restock(self):
        return self.current_stock <= self.minimum_stock
