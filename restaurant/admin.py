from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import (
    Utilisateur, Categorie, Plat, Commande, Reservation,
    Panier, ItemPanier, Avis, ProfilUtilisateur, ItemCommande, Table,
    Paiement, Favori, Notification, Ingredient
)

# === Formulaires personnalisés pour l'utilisateur ===

class UtilisateurCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ('username', 'email', 'nom', 'prenom', 'role')

class UtilisateurChangeForm(UserChangeForm):
    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'nom', 'prenom', 'role')

# === Admin Utilisateur ===

class UtilisateurAdmin(UserAdmin):
    add_form = UtilisateurCreationForm
    form = UtilisateurChangeForm
    model = Utilisateur
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ("Informations personnelles", {
            'fields': ('nom', 'prenom', 'adresse', 'date_naissance', 'lieu_naissance', 'telephone', 'role')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Informations personnelles", {
            'fields': ('nom', 'prenom', 'adresse', 'date_naissance', 'lieu_naissance', 'telephone', 'role')
        }),
    )
    search_fields = ['username', 'email', 'nom', 'prenom']
    ordering = ['username']

# === Admin Categorie ===

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ordre', 'active', 'est_specialite')
    list_editable = ('ordre', 'active', 'est_specialite')
    ordering = ['ordre']
    search_fields = ['nom']

# === Admin Plat ===

@admin.register(Plat)
class PlatAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'prix', 'stock', 'disponible', 'vegetarien', 'vegan')
    list_filter = ('categorie', 'disponible', 'vegetarien', 'vegan')
    search_fields = ['nom', 'ingredients', 'allergenes']
    ordering = ['categorie__ordre', 'nom']

# === Admin Commande ===

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'get_plats', 'get_quantite_total', 'statut', 'type_commande', 'numero_table', 'get_prix_total', 'date_commande')
    list_filter = ('statut', 'type_commande', 'date_commande')
    search_fields = ['utilisateur__username', 'items__plat__nom']
    ordering = ['-date_commande']

    def get_plats(self, obj):
        return ", ".join([item.plat.nom for item in obj.items.all()])
    get_plats.short_description = 'Plats'

    def get_quantite_total(self, obj):
        return sum(item.quantite for item in obj.items.all())
    get_quantite_total.short_description = 'Quantité Totale'

    def get_prix_total(self, obj):
        return obj.total
    get_prix_total.short_description = 'Prix Total'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items__plat')

# === Admin Reservation ===

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone', 'date', 'heure', 'personnes', 'confirme', 'annule', 'table')
    list_filter = ('confirme', 'annule', 'date')
    search_fields = ['nom', 'email', 'telephone']
    ordering = ['-date', '-heure']

# === Admin Panier ===

@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date_creation', 'date_modification')
    search_fields = ['utilisateur__username']

# === Admin ItemPanier ===

@admin.register(ItemPanier)
class ItemPanierAdmin(admin.ModelAdmin):
    list_display = ('panier', 'plat', 'quantite', 'date_ajout')
    search_fields = ['plat__nom', 'panier__utilisateur__username']

# === Admin Avis ===

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'plat', 'note', 'date_creation')
    list_filter = ('note',)
    search_fields = ['utilisateur__username', 'plat__nom']
    ordering = ['-date_creation']

# === Admin ProfilUtilisateur ===

@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('user', 'telephone', 'notifications_email', 'notifications_sms', 'date_creation')
    search_fields = ['user__username', 'telephone']
    list_filter = ('notifications_email', 'notifications_sms')

# === Admin ItemCommande ===

@admin.register(ItemCommande)
class ItemCommandeAdmin(admin.ModelAdmin):
    list_display = ('commande', 'plat', 'quantite', 'prix')
    search_fields = ['plat__nom', 'commande__id']

# === Admin Table ===

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre_places', 'disponible')
    list_editable = ('disponible', 'nombre_places')
    ordering = ['numero']
    search_fields = ['numero']

# === Admin Paiement ===

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('id', 'commande', 'montant', 'methode_paiement', 'date_paiement', 'utilisateur')
    list_filter = ('methode_paiement', 'date_paiement')
    search_fields = ['commande__id', 'utilisateur__username']
    ordering = ['-date_paiement']

# === Admin Favori ===

@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'plat', 'date_ajout')
    search_fields = ['utilisateur__username', 'plat__nom']
    ordering = ['-date_ajout']

# === Admin Notification ===

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'message', 'lu', 'date_creation')
    list_filter = ('lu', 'date_creation')
    search_fields = ['utilisateur__username', 'message']
    ordering = ['-date_creation']

# === Admin Ingredient ===

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'stock', 'unite')
    search_fields = ['nom']
    ordering = ['nom']

# Enregistrement du modèle Utilisateur
admin.site.register(Utilisateur, UtilisateurAdmin)