from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

# ============================
# === Utilisateur ===
# ============================

class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('gerant', 'Gérant'),
        ('serveur', 'Serveur'),
        ('cuisinier', 'Cuisinier'),
        ('livreur', 'Livreur'),
        ('client', 'Client'),
    ]
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')

    def __str__(self):
        return f"{self.username} ({self.role})"

# ============================
# === Profil Utilisateur ===
# ============================

class ProfilUtilisateur(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    date_naissance = models.DateField(null=True, blank=True)
    preferences_alimentaires = models.TextField(blank=True, null=True)
    notifications_email = models.BooleanField(default=True)
    notifications_sms = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profil de {self.user.username}"

# ============================
# === Ingrédient ===
# ============================

class Ingredient(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    stock = models.PositiveIntegerField(default=0)
    unite = models.CharField(max_length=50, default='unités')

    def __str__(self):
        return self.nom

# ============================
# === Catégories & Plats ===
# ============================

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    ordre = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    est_specialite = models.BooleanField(default=False)

    class Meta:
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom

class Plat(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    image = models.ImageField(upload_to='plats/', blank=True, null=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='plats')
    disponible = models.BooleanField(default=True)
    ingredients = models.ManyToManyField(Ingredient, blank=True)
    allergenes = models.TextField(blank=True, null=True)
    temps_preparation = models.PositiveIntegerField(null=True, blank=True)
    calories = models.PositiveIntegerField(null=True, blank=True)
    vegetarien = models.BooleanField(default=False)
    vegan = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['categorie__ordre', 'nom']
        indexes = [
            models.Index(fields=['disponible', 'categorie']),
            models.Index(fields=['nom']),
        ]

    def __str__(self):
        return f"{self.nom} - {self.prix}€"

    @property
    def total(self):
        return self.prix

    def is_disponible(self):
        return self.disponible and self.categorie.active and self.stock > 0

# ============================
# === Panier ===
# ============================

class Panier(models.Model):
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Panier de {self.utilisateur.username}"

    @property
    def total(self):
        return sum(item.total for item in self.items.all())

    @property
    def nombre_items(self):
        return sum(item.quantite for item in self.items.all())

    def vider(self):
        self.items.all().delete()

class ItemPanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='items')
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['panier', 'plat']

    def __str__(self):
        return f"{self.plat.nom} x{self.quantite}"

    @property
    def total(self):
        return self.plat.prix * self.quantite

# ============================
# === Commandes ===
# ============================

class Commande(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_preparation', 'En préparation'),
        ('prete', 'Prête'),
        ('en_livraison', 'En livraison'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
        ('epuise', 'Épuisé'),
        ('archivee', 'Archivée'),
    ]
    TYPE_COMMANDE_CHOICES = [
        ('sur_place', 'Sur place'),
        ('a_livrer', 'À livrer'),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='commandes'
    )
    nom_client = models.CharField(max_length=100, blank=True, null=True)
    email_client = models.EmailField(blank=True, null=True)
    telephone_client = models.CharField(max_length=20, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    type_commande = models.CharField(max_length=20, choices=TYPE_COMMANDE_CHOICES, default='sur_place')
    numero_table = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Numéro de table pour les commandes sur place"
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_commande = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_livraison_prevue = models.DateTimeField(null=True, blank=True)
    commentaire_client = models.TextField(blank=True, null=True)
    commentaire_interne = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_commande']
        indexes = [
            models.Index(fields=['date_commande']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"Commande #{self.id} - {self.utilisateur.username} ({self.type_commande})"

    @property
    def peut_etre_annulee(self):
        return self.statut in ['en_attente', 'confirmee']

    def calculer_total(self):
        total = sum(item.prix * item.quantite for item in self.items.all())
        self.total = total
        self.save()

class ItemCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='items')
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    prix = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.plat.nom} x{self.quantite}"

    def save(self, *args, **kwargs):
        if not self.prix:
            self.prix = self.plat.prix
        super().save(*args, **kwargs)

# ============================
# === Réservations ===
# ============================

class Reservation(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    date = models.DateField()
    heure = models.TimeField()
    personnes = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    message = models.TextField(blank=True, null=True)
    confirme = models.BooleanField(default=False)
    annule = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations'
    )
    table = models.ForeignKey(
        'Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations'
    )

    class Meta:
        ordering = ['-date', '-heure']
        indexes = [
            models.Index(fields=['date', 'heure']),
            models.Index(fields=['confirme', 'annule']),
        ]

    def __str__(self):
        return f"{self.nom} - {self.date} à {self.heure} ({self.personnes} pers.)"

    def save(self, *args, **kwargs):
        if self.confirme and not self.date_confirmation:
            self.date_confirmation = timezone.now()
        super().save(*args, **kwargs)

    @property
    def datetime_reservation(self):
        return timezone.datetime.combine(self.date, self.heure)

    @property
    def est_passee(self):
        return self.datetime_reservation < timezone.now()

    @property
    def statut_affichage(self):
        if self.annule:
            return "Annulée"
        elif self.est_passee:
            return "Passée"
        elif self.confirme:
            return "Confirmée"
        else:
            return "En attente"

# ============================
# === Tables ===
# ============================

class Table(models.Model):
    numero = models.PositiveIntegerField(unique=True, verbose_name="Numéro de la table")
    nombre_places = models.PositiveIntegerField(default=4, validators=[MinValueValidator(1)])
    disponible = models.BooleanField(default=True, verbose_name="Table disponible ?")

    def __str__(self):
        return f"Table {self.numero}"

# ============================
# === Avis ===
# ============================

class Avis(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE, related_name='avis')
    note = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    commentaire = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['utilisateur', 'plat']
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.utilisateur.username} - {self.plat.nom} ({self.note}/5)"

# ============================
# === Paiement ===
# ============================

class Paiement(models.Model):
    METHODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('cb', 'Carte bancaire'),
        ('mobile_money', 'Mobile Money'),
    ]
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    methode_paiement = models.CharField(max_length=20, choices=METHODE_PAIEMENT_CHOICES)
    date_paiement = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Paiement {self.id} - Commande {self.commande.id} ({self.methode_paiement})"

# ============================
# === Favori ===
# ============================

class Favori(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['utilisateur', 'plat']

    def __str__(self):
        return f"{self.utilisateur.username} - {self.plat.nom}"

# ============================
# === Notification ===
# ============================

class Notification(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='notifications_envoyees')

    def __str__(self):
        return f"Notification pour {self.utilisateur.username}"

# ============================
# === Signaux ===
# ============================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        ProfilUtilisateur.objects.create(user=instance)
        Panier.objects.create(utilisateur=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profilutilisateur'):
        instance.profilutilisateur.save()