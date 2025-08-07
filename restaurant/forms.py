from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import time
import re
from .models import Utilisateur, Plat, Categorie, Reservation, Commande, ItemCommande, Paiement, Notification, ProfilUtilisateur, Ingredient

# =============================
# === Formulaire d'inscription ===
# =============================

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    adresse = forms.CharField(widget=forms.Textarea, required=False)
    date_naissance = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    lieu_naissance = forms.CharField(max_length=100, required=False)
    telephone = forms.CharField(max_length=20)
    role = forms.ChoiceField(choices=Utilisateur.ROLE_CHOICES)

    class Meta:
        model = Utilisateur
        fields = [
            'username', 'email', 'password1', 'password2',
            'nom', 'prenom', 'adresse', 'date_naissance',
            'lieu_naissance', 'telephone', 'role',
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone', '').replace(' ', '').replace('-', '')
        if not re.match(r'^(?:\+221)?(70|75|76|77|78|33)\d{7}$', telephone):
            raise ValidationError("Veuillez entrer un numéro de téléphone sénégalais valide.")
        return telephone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nom = self.cleaned_data['nom']
        user.prenom = self.cleaned_data['prenom']
        user.adresse = self.cleaned_data['adresse']
        user.date_naissance = self.cleaned_data['date_naissance']
        user.lieu_naissance = self.cleaned_data['lieu_naissance']
        user.telephone = self.cleaned_data['telephone']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user

# =============================
# === Formulaire de profil utilisateur ===
# =============================

class ProfilUtilisateurForm(forms.ModelForm):
    class Meta:
        model = ProfilUtilisateur
        fields = ['telephone', 'adresse', 'date_naissance', 'preferences_alimentaires', 'notifications_email', 'notifications_sms']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'preferences_alimentaires': forms.Textarea(attrs={'rows': 3}),
        }

# =============================
# === Formulaire des plats ===
# =============================

class PlatForm(forms.ModelForm):
    ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Ingrédients",
        help_text="Sélectionnez les ingrédients de ce plat"
    )

    class Meta:
        model = Plat
        fields = [
            'nom', 'description', 'prix', 'image', 'categorie', 'disponible',
            'ingredients', 'allergenes', 'temps_preparation', 'calories', 
            'vegetarien', 'vegan', 'stock'
        ]
        labels = {
            'nom': 'Nom du plat',
            'description': 'Description',
            'prix': 'Prix (€)',
            'image': 'Image du plat',
            'disponible': 'Plat disponible',
            'ingredients': 'Ingredients',
            'allergenes': 'Allergènes',
            'temps_preparation': 'Temps de préparation (minutes)',
            'calories': 'Calories',
            'vegetarien': 'Plat végétarien',
            'vegan': 'Plat vegan',
            'stock': 'Stock disponible'
        }
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Décrivez le plat...'
            }),
            'allergenes': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Listez les allergènes (gluten, noix, etc.)'
            }),
            'prix': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'temps_preparation': forms.NumberInput(attrs={
                'min': '1',
                'placeholder': 'en minutes'
            }),
            'calories': forms.NumberInput(attrs={
                'min': '0',
                'placeholder': 'nombre de calories'
            }),
            'stock': forms.NumberInput(attrs={
                'min': '0',
                'placeholder': 'quantité en stock'
            })
        }
        help_texts = {
            'nom': 'Nom unique et descriptif du plat',
            'prix': 'Prix en euros (ex: 15.50)',
            'stock': 'Quantité disponible en cuisine',
            'temps_preparation': 'Temps estimé de préparation en minutes'
        }

    def clean_prix(self):
        prix = self.cleaned_data.get('prix')
        if prix <= 0:
            raise ValidationError("Le prix doit être positif.")
        return prix

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock < 0:
            raise ValidationError("Le stock ne peut pas être négatif.")
        return stock

    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if len(nom.strip()) < 2:
            raise ValidationError("Le nom doit contenir au moins 2 caractères.")
        return nom.strip()

    def clean_temps_preparation(self):
        temps = self.cleaned_data.get('temps_preparation')
        if temps is not None and temps <= 0:
            raise ValidationError("Le temps de préparation doit être positif.")
        return temps

# =============================
# === Formulaire de réservation ===
# =============================

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['date', 'heure', 'personnes', 'nom', 'email', 'telephone', 'message']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure': forms.TimeInput(attrs={'type': 'time'}),
            'message': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date < timezone.now().date():
            raise ValidationError("La date de réservation ne peut pas être dans le passé.")
        return date

    def clean_heure(self):
        heure = self.cleaned_data.get('heure')
        if heure and not ((time(11, 30) <= heure <= time(14, 30)) or (time(18, 30) <= heure <= time(23, 0))):
            raise ValidationError("Les réservations sont possibles de 11h30 à 14h30 et de 18h30 à 23h00.")
        return heure

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone', '').replace(' ', '').replace('-', '')
        if not re.match(r'^(?:\+221)?(70|75|76|77|78|33)\d{7}$', telephone):
            raise ValidationError("Veuillez entrer un numéro de téléphone sénégalais valide.")
        return telephone

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        heure = cleaned_data.get('heure')
        if date == timezone.now().date() and heure and heure <= timezone.now().time():
            raise ValidationError("L'heure doit être dans le futur.")
        return cleaned_data

# =============================
# === Formulaires de commande ===
# =============================

class CommandeForm(forms.ModelForm):
    numero_table = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        label="Numéro de table",
        widget=forms.NumberInput(attrs={'placeholder': 'Entrez le numéro de table (pour commandes sur place)'})
    )

    class Meta:
        model = Commande
        fields = ['type_commande', 'numero_table', 'commentaire_client']
        widgets = {
            'type_commande': forms.Select(choices=Commande.TYPE_COMMANDE_CHOICES),
            'commentaire_client': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        type_commande = cleaned_data.get('type_commande')
        numero_table = cleaned_data.get('numero_table')
        if type_commande == 'sur_place' and not numero_table:
            raise ValidationError("Le numéro de table est requis pour les commandes sur place.")
        if type_commande == 'a_livrer' and numero_table:
            raise ValidationError("Le numéro de table ne doit pas être spécifié pour les commandes à livrer.")
        return cleaned_data

class CommandeStatutForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['statut']
        widgets = {
            'statut': forms.Select(choices=Commande.STATUT_CHOICES),
        }

class ItemCommandeForm(forms.ModelForm):
    class Meta:
        model = ItemCommande
        fields = ['plat', 'quantite']
        widgets = {
            'quantite': forms.NumberInput(attrs={'min': 1, 'max': 99}),
        }

    def clean_plat(self):
        plat = self.cleaned_data.get('plat')
        if plat and not plat.is_disponible():
            raise ValidationError("Ce plat n'est pas disponible.")
        return plat

# =============================
# === Formulaire de recherche ===
# =============================

class RechercheForm(forms.Form):
    recherche = forms.CharField(required=False)
    categorie = forms.ModelChoiceField(
        queryset=Categorie.objects.filter(active=True),
        required=False,
        empty_label="Toutes les catégories"
    )
    prix_min = forms.DecimalField(required=False, min_value=0)
    prix_max = forms.DecimalField(required=False, min_value=0)
    vegetarien = forms.BooleanField(required=False)
    vegan = forms.BooleanField(required=False)
    temps_preparation_max = forms.IntegerField(required=False, min_value=1, label="Temps de préparation max (min)")
    tri = forms.ChoiceField(choices=[
        ('nom', 'Nom'),
        ('prix', 'Prix croissant'),
        ('-prix', 'Prix décroissant'),
        ('categorie', 'Catégorie'),
    ], required=False)

    def clean(self):
        cleaned_data = super().clean()
        prix_min = cleaned_data.get('prix_min')
        prix_max = cleaned_data.get('prix_max')
        temps_preparation_max = cleaned_data.get('temps_preparation_max')
        if prix_min and prix_max and prix_min > prix_max:
            raise ValidationError("Le prix minimum ne peut pas dépasser le prix maximum.")
        if temps_preparation_max and temps_preparation_max < 1:
            raise ValidationError("Le temps de préparation maximum doit être positif.")
        return cleaned_data

# =============================
# === Formulaire de contact ===
# =============================

class ContactForm(forms.Form):
    nom = forms.CharField(max_length=100)
    email = forms.EmailField()
    sujet = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise ValidationError("Le message doit contenir au moins 10 caractères.")
        return message

# =============================
# === Formulaire de paiement ===
# =============================

class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['methode_paiement', 'montant']
        widgets = {
            'methode_paiement': forms.Select(choices=Paiement.METHODE_PAIEMENT_CHOICES),
            'montant': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.commande = kwargs.pop('commande', None)
        super().__init__(*args, **kwargs)

    def clean_montant(self):
        montant = self.cleaned_data.get('montant')
        if self.commande and montant != self.commande.total:
            raise ValidationError(f"Le montant doit être égal au total de la commande ({self.commande.total}€).")
        return montant

# =============================
# === Formulaire de notification ===
# =============================

class NotificationForm(forms.ModelForm):
    destinataire = forms.ModelChoiceField(
        queryset=Utilisateur.objects.all(),
        label="Destinataire",
        empty_label="Sélectionner un destinataire"
    )

    class Meta:
        model = Notification
        fields = ['destinataire', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }

# =============================
# === Formulaire de gestion des ingrédients ===
# =============================

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['nom', 'stock', 'unite']
        widgets = {
            'stock': forms.NumberInput(attrs={'min': 0}),
        }