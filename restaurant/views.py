import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from django.template.loader import get_template
import subprocess
import os
from .models import (
    Utilisateur, Plat, Categorie, Commande, Reservation, Panier, ItemPanier,
    ItemCommande, Table, Avis, Paiement, Favori, Notification, Ingredient
)
from .forms import (
    PlatForm, ReservationForm, RegisterForm, CommandeForm, CommandeStatutForm,
    RechercheForm, ContactForm, PaiementForm, NotificationForm, ProfilUtilisateurForm, IngredientForm
)
from django.shortcuts import render
from .models import Categorie, Plat, Favori

logger = logging.getLogger(__name__)

# --- Utility Functions ---

def est_gestionnaire(user):
    """Vérifie si l'utilisateur est dans le groupe 'Gestionnaire'."""
    return user.groups.filter(name='Gestionnaire').exists()

def is_gerant(user):
    """Vérifie si l'utilisateur a le rôle 'gerant'."""
    return user.is_authenticated and user.role == 'gerant'

def is_serveur(user):
    """Vérifie si l'utilisateur a le rôle 'serveur'."""
    return user.is_authenticated and user.role == 'serveur'

def is_cuisinier(user):
    """Vérifie si l'utilisateur a le rôle 'cuisinier'."""
    return user.is_authenticated and user.role == 'cuisinier'

def is_livreur(user):
    """Vérifie si l'utilisateur a le rôle 'livreur'."""
    return user.is_authenticated and user.role == 'livreur'

def get_panier_from_session(request):
    """Récupère le panier de la session pour les utilisateurs anonymes."""
    return request.session.get('panier', {})

def update_panier_session(request, panier):
    """Met à jour le panier dans la session et marque la session comme modifiée."""
    request.session['panier'] = panier
    request.session.modified = True

def kitchen_required(view_func):
    """Décorateur pour restreindre l'accès au personnel de cuisine."""
    def wrapper(request, *args, **kwargs):
        if not is_cuisinier(request.user):
            messages.error(request, "Accès réservé au personnel de cuisine.")
            return redirect('restaurant:home')
        return view_func(request, *args, **kwargs)
    return wrapper

def delivery_required(view_func):
    """Décorateur pour restreindre l'accès aux livreurs."""
    def wrapper(request, *args, **kwargs):
        if not is_livreur(request.user):
            messages.error(request, "Accès réservé aux livreurs.")
            return redirect('restaurant:home')
        return view_func(request, *args, **kwargs)
    return wrapper

def gerant_required(view_func):
    """Décorateur pour restreindre l'accès aux gérants."""
    def wrapper(request, *args, **kwargs):
        if not is_gerant(request.user):
            messages.error(request, "Accès réservé aux gérants.")
            return redirect('restaurant:home')
        return view_func(request, *args, **kwargs)
    return wrapper

def serveur_required(view_func):
    """Décorateur pour restreindre l'accès aux serveurs."""
    def wrapper(request, *args, **kwargs):
        if not is_serveur(request.user):
            messages.error(request, "Accès réservé aux serveurs.")
            return redirect('restaurant:home')
        return view_func(request, *args, **kwargs)
    return wrapper

# --- Authentication Views ---

def login_view(request):
    """Vue pour la connexion des utilisateurs."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Connexion réussie.")
            if user.role == 'gerant':
                return redirect('restaurant:dashboard')
            elif user.role == 'serveur':
                return redirect('restaurant:dashboard_serveur')
            elif user.role == 'cuisinier':
                return redirect('restaurant:cuisine_dashboard')
            elif user.role == 'livreur':
                return redirect('restaurant:dashboard_livreur')
            else:
                return redirect('restaurant:home_alias')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
    return render(request, 'restaurant/login.html')

def register_view(request):
    """Vue pour l'inscription des utilisateurs."""
    if request.user.is_authenticated:
        return redirect('restaurant:dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Inscription réussie ! Bienvenue !')
            return redirect('restaurant:dashboard')
    else:
        form = RegisterForm()
    return render(request, 'restaurant/inscription.html', {'form': form})

@login_required
def logout_view(request):
    """Vue pour la déconnexion."""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('restaurant:login')

class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    """Vue pour la réinitialisation du mot de passe."""
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    success_message = "Un email de réinitialisation a été envoyé."

# --- Public Views ---

def accueil_public(request):
    """Vue pour la page d'accueil publique."""
    categories = Categorie.objects.prefetch_related('plats').filter(plats__disponible=True).distinct()
    panier_items_count = 0
    favoris = []
    if request.user.is_authenticated:
        try:
            panier_obj = Panier.objects.get(utilisateur=request.user)
            panier_items_count = panier_obj.nombre_items
            favoris = Favori.objects.filter(utilisateur=request.user).select_related('plat')
        except Panier.DoesNotExist:
            panier_items_count = 0
    else:
        panier_session = get_panier_from_session(request)
        panier_items_count = sum(panier_session.values())
    return render(request, 'restaurant/home.html', {
        'categories': categories,
        'panier_items_count': panier_items_count,
        'favoris': favoris
    })

def home(request):
    """Alias pour la page d'accueil publique."""
    return accueil_public(request)

def infos_restaurant(request):
    """Vue pour les informations du restaurant."""
    return render(request, 'restaurant/infos_restaurant.html')

def horaires(request):
    """Vue pour les horaires du restaurant."""
    return render(request, 'restaurant/horaires.html')

def contact(request):
    """Vue pour le formulaire de contact."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                send_mail(
                    subject=form.cleaned_data['sujet'],
                    message=f"De : {form.cleaned_data['nom']} <{form.cleaned_data['email']}>\n\n{form.cleaned_data['message']}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True,
                )
                messages.success(request, "Votre message a été envoyé avec succès.")
                return redirect('restaurant:contact')
            except Exception as e:
                logger.error(f"Erreur envoi email contact: {str(e)}")
                messages.error(request, "Erreur lors de l'envoi du message.")
    else:
        form = ContactForm()
    return render(request, 'restaurant/contact.html', {'form': form})

# --- Dashboard Views ---

from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

@login_required
@gerant_required
def dashboard(request):
    if not (is_gerant(request.user) or request.user.is_superuser):
        messages.error(request, "Accès non autorisé.")
        return redirect('restaurant:home')

    plats = Plat.objects.select_related('categorie').all()
    categories = Categorie.objects.filter(active=True)
    today = timezone.now().date()

    # Statistiques générales
    stats = {
        'total_plats': plats.count(),
        'plats_disponibles': plats.filter(disponible=True, stock__gt=0).count(),
        'reservations_du_jour': Reservation.objects.filter(date=today).count(),
        'commandes_en_attente': Commande.objects.filter(statut='en_attente').count(),
        'commandes_en_preparation': Commande.objects.filter(statut='en_preparation').count(),
        'revenus_journaliers': Commande.objects.filter(date_commande__date=today).aggregate(total=Sum('total'))['total'] or 0,
        'revenus_hebdomadaires': Commande.objects.filter(date_commande__gte=today - timedelta(days=7)).aggregate(total=Sum('total'))['total'] or 0,
        'revenus_mensuels': Commande.objects.filter(date_commande__month=today.month).aggregate(total=Sum('total'))['total'] or 0,
        'clients_aujourd_hui': Reservation.objects.filter(date=today).count(),
        'commandes_aujourd_hui': Commande.objects.filter(date_commande__date=today).count(),
    }

    # Alertes
    alertes = {
        'reservations_urgentes': Reservation.objects.filter(date=today, confirme=False, annule=False).count(),
        'plats_en_rupture': Plat.objects.filter(stock__lte=5, disponible=True).count(),
        'commandes_urgentes': Commande.objects.filter(statut='en_attente', date_commande__date=today).count(),
    }

    # Revenus mensuels pour le graphique
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)
    revenus_mensuels = (
        Commande.objects
        .filter(date_commande__range=[start_date, end_date])
        .annotate(month=TruncMonth('date_commande'))
        .values('month')
        .annotate(total=Sum('total'))
        .order_by('month')
    )
    chart_data = {
        'labels': [entry['month'].strftime('%b %Y') for entry in revenus_mensuels],
        'data': [float(entry['total']) for entry in revenus_mensuels],
    }

    # Plats populaires pour le graphique
    plats_populaires = (
        ItemCommande.objects
        .filter(commande__date_commande__date=today)
        .values('plat__nom')
        .annotate(total=Sum('quantite'))
        .order_by('-total')[:5]
    )
    plats_data = {
        'labels': [entry['plat__nom'] for entry in plats_populaires],
        'data': [entry['total'] for entry in plats_populaires],
    }

    # Avis récents
    avis_recents = Avis.objects.select_related('plat').order_by('-date_creation')[:5]

    # Liste du personnel
    utilisateurs = Utilisateur.objects.exclude(role='client').order_by('username')

    paginator = Paginator(plats, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'restaurant/dashboard.html', {
        'plats': page_obj,
        'categories': categories,
        'stats': stats,
        'alertes': alertes,
        'chart_data': chart_data,
        'plats_populaires': plats_data,
        'avis_recents': avis_recents,
        'utilisateurs': utilisateurs,
    })

@login_required
@serveur_required
def dashboard_serveur(request):
    """Tableau de bord pour les serveurs."""
    commandes = Commande.objects.filter(
        type_commande='sur_place',
        statut__in=['en_attente', 'confirmee', 'en_preparation', 'prete']
    ).prefetch_related('items__plat').order_by('-date_commande')
    tables = Table.objects.all().order_by('numero')
    return render(request, 'restaurant/dashboard_serveur.html', {
        'user': request.user,
        'title': 'Dashboard Serveur',
        'commandes': commandes,
        'tables': tables
    })

@login_required
@delivery_required
def dashboard_livreur(request):
    """Tableau de bord pour les livreurs."""
    commandes = Commande.objects.filter(
        type_commande='a_livrer',
        statut__in=['prete', 'en_livraison']
    ).prefetch_related('items__plat').order_by('-date_commande')
    return render(request, 'restaurant/dashboard_livreur.html', {
        'user': request.user,
        'title': 'Dashboard Livreur',
        'commandes': commandes
    })

@login_required
@kitchen_required
def cuisine_dashboard(request):
    """Tableau de bord pour la cuisine."""
    try:
        today = timezone.now().date()
        commandes = Commande.objects.exclude(statut__in=['annulee', 'livree', 'archivee']).prefetch_related('items__plat')
        statut_filter = request.GET.get('statut')
        if statut_filter:
            commandes = commandes.filter(statut=statut_filter)
        commandes = commandes.order_by('-date_commande')
        stats = {
            'en_attente': commandes.filter(statut='en_attente').count(),
            'en_preparation': commandes.filter(statut='en_preparation').count(),
            'prete': commandes.filter(statut='prete').count(),
            'total_jour': commandes.filter(date_commande__date=today).count(),
        }
        if request.method == 'POST':
            commande_id = request.POST.get('commande_id')
            commande = get_object_or_404(Commande, id=commande_id)
            form = CommandeStatutForm(request.POST, instance=commande)
            if form.is_valid():
                form.save()
                if form.cleaned_data['statut'] == 'epuise':
                    for item in commande.items.all():
                        item.plat.disponible = False
                        item.plat.stock = 0
                        item.plat.save()
                if form.cleaned_data['statut'] == 'prete' and commande.type_commande == 'a_livrer':
                    livreur = Utilisateur.objects.filter(role='livreur').first()
                    if livreur:
                        Notification.objects.create(
                            utilisateur=livreur,
                            message=f"La commande #{commande.id} est prête à être livrée.",
                            auteur=request.user
                        )
                try:
                    send_mail(
                        f'Mise à jour de votre commande #{commande.id}',
                        f"Bonjour {commande.utilisateur.username},\n\nLe statut de votre commande #{commande.id} a été mis à jour à '{commande.get_statut_display()}'.\nMerci !",
                        settings.DEFAULT_FROM_EMAIL,
                        [commande.email_client or commande.utilisateur.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    messages.warning(request, f"Statut mis à jour, mais l'email de notification n'a pas pu être envoyé: {str(e)}")
                messages.success(request, f"Statut de la commande n°{commande.id} mis à jour.")
                logger.info(f"Statut de la commande n°{commande.id} mis à jour à {commande.statut} par {request.user.username}")
                return redirect('restaurant:cuisine_dashboard' + (f'?statut={statut_filter}' if statut_filter else ''))
            else:
                messages.error(request, "Erreur lors de la mise à jour du statut.")
        else:
            form = CommandeStatutForm()
        urgent_commandes = commandes if not statut_filter else commandes.filter(statut__in=['en_attente', 'en_preparation'])
        return render(request, 'restaurant/dashboard_cuisine.html', {
            'commandes': urgent_commandes,
            'stats': stats,
            'form': form,
        })
    except Exception as e:
        logger.error(f"Erreur dans cuisine_dashboard: {str(e)}")
        messages.error(request, "Une erreur s'est produite lors du chargement du tableau de bord.")
        return render(request, 'restaurant/dashboard_cuisine.html', {
            'commandes': [],
            'stats': {'en_attente': 0, 'en_preparation': 0, 'prete': 0, 'total_jour': 0},
            'form': CommandeStatutForm()
        })

@login_required
@kitchen_required
def cuisine_stats(request):
    """Statistiques pour la cuisine."""
    today = timezone.now().date()
    stats = {
        'total_commandes': Commande.objects.filter(date_commande__date=today).count(),
        'total_revenus': Commande.objects.filter(date_commande__date=today).aggregate(total=Sum('total'))['total'] or 0,
        'plats_populaires': ItemCommande.objects.filter(commande__date_commande__date=today)
            .values('plat__nom').annotate(total=Sum('quantite')).order_by('-total')[:5]
    }
    return render(request, 'restaurant/cuisine_stats.html', {'stats': stats})

@login_required
@gerant_required
def statistiques(request):
    """Statistiques générales pour le gérant."""
    stats = {
        'total_plats': Plat.objects.count(),
        'plats_disponibles': Plat.objects.filter(disponible=True, stock__gt=0).count(),
        'total_commandes': Commande.objects.count(),
        'commandes_en_attente': Commande.objects.filter(statut='en_attente').count(),
        'commandes_confirmee': Commande.objects.filter(statut='confirmee').count(),
        'commandes_en_preparation': Commande.objects.filter(statut='en_preparation').count(),
        'commandes_prete': Commande.objects.filter(statut='prete').count(),
        'commandes_en_livraison': Commande.objects.filter(statut='en_livraison').count(),
        'commandes_livree': Commande.objects.filter(statut='livree').count(),
        'commandes_annulee': Commande.objects.filter(statut='annulee').count(),
        'commandes_epuise': Commande.objects.filter(statut='epuise').count(),
        'total_reservations': Reservation.objects.count(),
        'reservations_aujourd_hui': Reservation.objects.filter(date=timezone.now().date()).count(),
        'revenus_mensuels': Commande.objects.filter(date_commande__month=timezone.now().month)
            .aggregate(total=Sum('total'))['total'] or 0,
    }
    return render(request, 'restaurant/statistiques.html', {'stats': stats})

# --- Menu Management Views ---

def menu(request):
    """Vue pour afficher le menu."""
    form = RechercheForm(request.GET or None)
    plats = Plat.objects.filter(disponible=True, categorie__active=True, stock__gt=0).select_related('categorie')
    if form.is_valid():
        recherche = form.cleaned_data.get('recherche')
        categorie = form.cleaned_data.get('categorie')
        prix_min = form.cleaned_data.get('prix_min')
        prix_max = form.cleaned_data.get('prix_max')
        vegetarien = form.cleaned_data.get('vegetarien')
        vegan = form.cleaned_data.get('vegan')
        temps_preparation_max = form.cleaned_data.get('temps_preparation_max')
        tri = form.cleaned_data.get('tri')

        if recherche:
            plats = plats.filter(Q(nom__icontains=recherche) | Q(description__icontains=recherche))
        if categorie:
            plats = plats.filter(categorie=categorie)
        if prix_min:
            plats = plats.filter(prix__gte=prix_min)
        if prix_max:
            plats = plats.filter(prix__lte=prix_max)
        if vegetarien:
            plats = plats.filter(vegetarien=True)
        if vegan:
            plats = plats.filter(vegan=True)
        if temps_preparation_max:
            plats = plats.filter(temps_preparation__lte=temps_preparation_max)
        if tri:
            if tri == 'categorie':
                plats = plats.order_by('categorie__ordre', 'nom')
            else:
                plats = plats.order_by(tri)

    categories = Categorie.objects.all()
    favoris = []
    if request.user.is_authenticated:
        # Récupérer les identifiants des plats favoris de l'utilisateur
        favoris = Favori.objects.filter(utilisateur=request.user).values_list('plat__id', flat=True)
    context = {
        'categories': categories,
        'plats': plats,
        'form': form,
        'favoris': favoris
    }
    return render(request, 'restaurant/menu.html', context)

@login_required
@gerant_required
def ajouter_plat(request):
    """Vue pour ajouter un plat (gérant uniquement)."""
    if request.method == 'POST':
        form = PlatForm(request.POST, request.FILES)
        if form.is_valid():
            plat = form.save()
            messages.success(request, f"Plat '{plat.nom}' ajouté avec succès.")
            return redirect('restaurant:dashboard')
    else:
        form = PlatForm()
    return render(request, 'restaurant/ajouter_plat.html', {'form': form})

@login_required
@gerant_required
def modifier_plat(request, pk):
    """Vue pour modifier un plat (gérant uniquement)."""
    plat = get_object_or_404(Plat, pk=pk)
    if request.method == 'POST':
        form = PlatForm(request.POST, request.FILES, instance=plat)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plat '{plat.nom}' modifié avec succès.")
            return redirect('restaurant:dashboard')
    else:
        form = PlatForm(instance=plat)
    return render(request, 'restaurant/modifier_plat.html', {'form': form, 'plat': plat})

@login_required
@gerant_required
def supprimer_plat(request, pk):
    """Vue pour supprimer un plat (gérant uniquement)."""
    plat = get_object_or_404(Plat, pk=pk)
    if request.method == 'POST':
        nom_plat = plat.nom
        plat.delete()
        messages.success(request, f"Plat '{nom_plat}' supprimé avec succès.")
        return redirect('restaurant:dashboard')
    return render(request, 'restaurant/supprimer_plat.html', {'plat': plat})

@login_required
def ajouter_avis(request, plat_id):
    """Vue pour ajouter un avis sur un plat."""
    plat = get_object_or_404(Plat, id=plat_id)
    if request.method == 'POST':
        note = request.POST.get('note')
        commentaire = request.POST.get('commentaire')
        try:
            Avis.objects.create(
                utilisateur=request.user,
                plat=plat,
                note=int(note),
                commentaire=commentaire
            )
            messages.success(request, "Votre avis a été ajouté avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout de l'avis : {str(e)}")
        return redirect('restaurant:menu')
    return render(request, 'restaurant/ajouter_avis.html', {'plat': plat})

@login_required
def ajouter_favori(request, plat_id):
    """Vue pour ajouter ou retirer un plat des favoris."""
    plat = get_object_or_404(Plat, id=plat_id)
    favori, created = Favori.objects.get_or_create(
        utilisateur=request.user,
        plat=plat
    )
    if not created:
        favori.delete()
        messages.success(request, f"{plat.nom} retiré des favoris.")
    else:
        messages.success(request, f"{plat.nom} ajouté aux favoris.")
    return redirect(request.POST.get('next', 'restaurant:menu'))

@login_required
@gerant_required
def api_toggle_disponibilite(request, plat_id):
    """API pour basculer la disponibilité d'un plat."""
    plat = get_object_or_404(Plat, id=plat_id)
    plat.disponible = not plat.disponible
    plat.save()
    return JsonResponse({'success': True, 'disponible': plat.disponible})

# --- Cart Views ---

def ajouter_au_panier(request, plat_id):
    """Vue pour ajouter un plat au panier."""
    plat = get_object_or_404(Plat, id=plat_id, disponible=True)
    if not plat.is_disponible() or plat.stock <= 0:
        messages.error(request, f"{plat.nom} est en rupture de stock.")
        return redirect(request.POST.get('next', request.META.get('HTTP_REFERER', 'restaurant:home')))
    if request.user.is_authenticated:
        panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
        item, created = ItemPanier.objects.get_or_create(panier=panier, plat=plat)
        if not created:
            if item.quantite + 1 > plat.stock:
                messages.error(request, f"Stock insuffisant pour {plat.nom} (disponible : {plat.stock}).")
                return redirect(request.POST.get('next', request.META.get('HTTP_REFERER', 'restaurant:home')))
            item.quantite += 1
        item.save()
    else:
        panier = get_panier_from_session(request)
        plat_key = str(plat_id)
        if plat_key in panier and panier[plat_key] >= plat.stock:
            messages.error(request, f"Stock insuffisant pour {plat.nom} (disponible : {plat.stock}).")
            return redirect(request.POST.get('next', request.META.get('HTTP_REFERER', 'restaurant:home')))
        panier[plat_key] = panier.get(plat_key, 0) + 1
        update_panier_session(request, panier)
    messages.success(request, f"{plat.nom} a été ajouté au panier.")
    return redirect(request.POST.get('next', request.META.get('HTTP_REFERER', 'restaurant:home')))

def panier(request):
    """Vue pour afficher le panier."""
    items = []
    total = 0
    panier_items_count = 0
    if request.user.is_authenticated:
        try:
            panier_obj = Panier.objects.get(utilisateur=request.user)
            items_panier = ItemPanier.objects.filter(panier=panier_obj).select_related('plat')
            for item in items_panier:
                items.append({
                    'id': item.id,
                    'plat': item.plat,
                    'quantite': item.quantite,
                    'total': item.total
                })
                total += item.total
                panier_items_count += item.quantite
        except Panier.DoesNotExist:
            pass
    else:
        panier_session = get_panier_from_session(request)
        for plat_id, quantite in panier_session.items():
            try:
                plat = Plat.objects.get(id=plat_id)
                sous_total = plat.prix * quantite
                items.append({
                    'id': plat_id,
                    'plat': plat,
                    'quantite': quantite,
                    'total': sous_total
                })
                total += sous_total
                panier_items_count += quantite
            except Plat.DoesNotExist:
                continue
    context = {
        'items': items,
        'total': total,
        'panier_items_count': panier_items_count,
    }
    return render(request, 'restaurant/panier.html', context)

@login_required
def modifier_panier(request, item_id, action):
    """Vue pour modifier la quantité ou supprimer un item du panier."""
    if action not in ['plus', 'moins', 'supprimer']:
        messages.error(request, "Action non valide.")
        return redirect('restaurant:panier')
    try:
        item = get_object_or_404(ItemPanier, id=item_id, panier__utilisateur=request.user)
        if action == 'plus':
            if item.quantite + 1 > item.plat.stock:
                messages.error(request, f"Stock insuffisant pour {item.plat.nom} (disponible : {item.plat.stock}).")
                return redirect('restaurant:panier')
            item.quantite += 1
            item.save()
        elif action == 'moins':
            item.quantite -= 1
            if item.quantite <= 0:
                item.delete()
            else:
                item.save()
        elif action == 'supprimer':
            item.delete()
        messages.success(request, "Panier mis à jour.")
    except ItemPanier.DoesNotExist:
        messages.error(request, "Produit non trouvé dans le panier.")
    return redirect('restaurant:panier')

@login_required
def vider_panier(request):
    """Vue pour vider le panier."""
    try:
        panier = Panier.objects.get(utilisateur=request.user)
        panier.vider()
        messages.success(request, "Panier vidé avec succès.")
    except Panier.DoesNotExist:
        messages.error(request, "Votre panier est déjà vide.")
    return redirect('restaurant:panier')

@login_required
def api_panier_count(request):
    """API pour obtenir le nombre d'items dans le panier."""
    try:
        panier = Panier.objects.get(utilisateur=request.user)
        count = panier.nombre_items
    except Panier.DoesNotExist:
        count = 0
    return JsonResponse({'count': count})

# --- Order Views ---

@login_required
def valider_commande(request):
    """Vue pour valider une commande."""
    try:
        panier = Panier.objects.get(utilisateur=request.user)
        items = ItemPanier.objects.filter(panier=panier).select_related('plat')
    except Panier.DoesNotExist:
        messages.error(request, "Votre panier est vide.")
        return redirect('restaurant:panier')
    if not items:
        messages.error(request, "Votre panier est vide.")
        return redirect('restaurant:panier')
    if request.method == 'POST':
        form = CommandeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    commande = Commande.objects.create(
                        utilisateur=request.user,
                        statut='en_attente',
                        type_commande=form.cleaned_data['type_commande'],
                        nom_client=request.user.nom or request.user.username,
                        email_client=request.user.email,
                        telephone_client=request.user.telephone,
                        numero_table=form.cleaned_data['numero_table'] if form.cleaned_data['type_commande'] == 'sur_place' else None,
                        commentaire_client=form.cleaned_data['commentaire_client']
                    )
                    total_commande = 0
                    for item in items:
                        if item.quantite > item.plat.stock:
                            messages.error(request, f"Stock insuffisant pour {item.plat.nom} (disponible : {item.plat.stock}).")
                            return redirect('restaurant:panier')
                        ItemCommande.objects.create(
                            commande=commande,
                            plat=item.plat,
                            quantite=item.quantite,
                            prix=item.plat.prix
                        )
                        item.plat.stock -= item.quantite
                        item.plat.save()
                        total_commande += item.plat.prix * item.quantite
                    items.delete()
                    commande.total = total_commande
                    commande.save()
                    try:
                        send_mail(
                            'Confirmation de votre commande',
                            f"Bonjour {commande.utilisateur.username},\n\nVotre commande #{commande.id} ({commande.get_type_commande_display()}) "
                            f"a été enregistrée avec succès.\n"
                            f"{'Table n°' + str(commande.numero_table) if commande.numero_table else ''}\n"
                            f"Total : {commande.total}€\n"
                            f"Merci de votre confiance !",
                            settings.DEFAULT_FROM_EMAIL,
                            [commande.email_client],
                            fail_silently=True,
                        )
                    except Exception:
                        messages.warning(request, "Commande validée, mais l'email de confirmation n'a pas pu être envoyé.")
                    messages.success(request, "Commande validée avec succès !")
                    return render(request, 'restaurant/confirmation_commande.html', {'commande': commande})
            except Exception as e:
                logger.error(f"Erreur lors de la validation de la commande: {str(e)}")
                messages.error(request, f"Erreur lors de la validation : {str(e)}")
                return redirect('restaurant:panier')
    else:
        form = CommandeForm(initial={'type_commande': 'sur_place'})
    return render(request, 'restaurant/valider_commande.html', {
        'form': form,
        'panier': items,
    })

@login_required
def mes_commandes(request):
    """Vue pour afficher l'historique des commandes de l'utilisateur."""
    commandes = Commande.objects.filter(utilisateur=request.user).prefetch_related('items__plat').order_by('-date_commande')
    paginator = Paginator(commandes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'restaurant/mes_commandes.html', {'commandes': page_obj})

@login_required
def detail_commande(request, commande_id):
    """Vue pour afficher les détails d'une commande."""
    if is_gerant(request.user) or is_serveur(request.user) or is_cuisinier(request.user) or is_livreur(request.user):
        commande = get_object_or_404(Commande, id=commande_id)
    else:
        commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    items = commande.items.all()
    return render(request, 'restaurant/detail_commande.html', {'commande': commande, 'items': items})

@login_required
def annuler_commande(request, commande_id):
    """Vue pour annuler une commande."""
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    if not commande.peut_etre_annulee:
        messages.error(request, "Cette commande ne peut pas être annulée.")
        return redirect('restaurant:mes_commandes')
    if request.method == "POST":
        commande.statut = 'annulee'
        commande.save()
        for item in commande.items.all():
            item.plat.stock += item.quantite
            item.plat.save()
        try:
            send_mail(
                'Annulation de votre commande',
                f"Bonjour {commande.utilisateur.username},\n\nVotre commande #{commande.id} a été annulée.",
                settings.DEFAULT_FROM_EMAIL,
                [commande.email_client],
                fail_silently=True,
            )
            messages.success(request, "Commande annulée avec succès.")
        except Exception as e:
            logger.error(f"Erreur envoi email pour annulation commande {commande.id}: {str(e)}")
            messages.warning(request, "Commande annulée mais email non envoyé.")
        return redirect('restaurant:mes_commandes')
    return render(request, 'restaurant/confirm_annuler_commande.html', {'commande': commande})

@login_required
def encaisser_commande(request, commande_id):
    """Vue pour encaisser une commande (serveur ou gérant)."""
    if not (is_serveur(request.user) or is_gerant(request.user)):
        messages.error(request, "Accès non autorisé.")
        return redirect('restaurant:dashboard')
    commande = get_object_or_404(Commande, id=commande_id, statut__in=['prete', 'en_livraison'])
    if request.method == 'POST':
        form = PaiementForm(request.POST, commande=commande)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.commande = commande
            paiement.utilisateur = request.user
            paiement.save()
            commande.statut = 'livree' if commande.type_commande == 'a_livrer' else 'confirmee'
            commande.save()
            messages.success(request, f"Paiement de la commande #{commande.id} enregistré.")
            return redirect('restaurant:generer_recu_pdf', paiement_id=paiement.id)
    else:
        form = PaiementForm(initial={'montant': commande.total}, commande=commande)
    return render(request, 'restaurant/encaisser_commande.html', {'form': form, 'commande': commande})

@login_required
def generer_recu_pdf(request, paiement_id):
    """Vue pour générer un reçu PDF pour un paiement."""
    paiement = get_object_or_404(Paiement, id=paiement_id)
    commande = paiement.commande
    items = [
        f"{item.plat.nom} & {item.quantite} & {item.prix * item.quantite} \\euro \\\\" 
        for item in commande.items.all()
    ]
    context = {
        'paiement': paiement,
        'commande': commande,
        'items': "\n".join(items),
        'restaurant_nom': "Le Gourmet",
        'restaurant_adresse': "123 Rue de Dakar, Senegal",
        'restaurant_telephone': "+221 767871996",
    }
    template = get_template('restaurant/reçu.tex')
    latex_content = template.render(context)
    
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_tex_file = os.path.join(temp_dir, f'recu_{paiement.id}.tex')
    temp_pdf_file = os.path.join(temp_dir, f'recu_{paiement.id}.pdf')
    
    with open(temp_tex_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    try:
        subprocess.run(['latexmk', '-pdf', '-interaction=nonstopmode', temp_tex_file], cwd=temp_dir, check=True)
        with open(temp_pdf_file, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=reçu_commande_{commande.id}.pdf'
        for ext in ['.tex', '.aux', '.log', '.fls', '.fdb_latexmk', '.pdf']:
            try:
                os.remove(os.path.join(temp_dir, f'recu_{paiement.id}{ext}'))
            except FileNotFoundError:
                pass
        return response
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la génération du PDF : {str(e)}")
        messages.error(request, "Erreur lors de la génération du reçu PDF.")
        return redirect('restaurant:detail_commande', commande_id=commande.id)

# --- Reservation Views ---

def reserver_table(request):
    """Vue pour réserver une table."""
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            if request.user.is_authenticated:
                reservation.client = request.user
                reservation.nom = request.user.nom or request.user.username
                reservation.email = request.user.email
                reservation.telephone = request.user.telephone
            reservation.save()
            try:
                send_mail(
                    'Confirmation de votre réservation',
                    f"Merci {reservation.nom}, votre réservation pour le {reservation.date} à {reservation.heure} a bien été enregistrée.",
                    settings.DEFAULT_FROM_EMAIL,
                    [reservation.email],
                    fail_silently=True,
                )
            except Exception:
                messages.warning(request, "Réservation enregistrée mais email non envoyé.")
            messages.success(request, "Réservation enregistrée avec succès !")
            return render(request, 'restaurant/reservation_confirmation.html', {'reservation': reservation})
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'nom': request.user.nom or request.user.username,
                'email': request.user.email,
                'telephone': request.user.telephone,
            }
        form = ReservationForm(initial=initial_data)
    return render(request, 'restaurant/reserver_table.html', {'form': form})

@login_required
def reservations(request):
    """Vue pour afficher les réservations de l'utilisateur."""
    if is_gerant(request.user) or is_serveur(request.user):
        reservations = Reservation.objects.all().order_by('-date', '-heure')
    else:
        reservations = Reservation.objects.filter(client=request.user).order_by('-date', '-heure')
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'restaurant/reservations.html', {'reservations': page_obj})

@login_required
@gerant_required
def admin_reservations(request):
    """Vue pour gérer toutes les réservations (gérant uniquement)."""
    reservations = Reservation.objects.all().order_by('-date', '-heure')
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'restaurant/admin_reservations.html', {'reservations': page_obj})

@login_required
@gerant_required
def reservations_non_confirmees(request):
    """Vue pour afficher les réservations non confirmées (gérant uniquement)."""
    reservations = Reservation.objects.filter(confirme=False, annule=False).order_by('-date', '-heure')
    paginator = Paginator(reservations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'restaurant/reservations_non_confirmees.html', {'reservations': page_obj})

@login_required
@gerant_required
def confirmer_reservation(request, reservation_id):
    """Vue pour confirmer une réservation et attribuer une table (gérant uniquement)."""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if request.method == 'POST':
        table_id = request.POST.get('table_id')
        try:
            table = Table.objects.get(id=table_id, disponible=True)
            with transaction.atomic():
                reservation.confirme = True
                reservation.table = table
                reservation.utilisateur = request.user
                reservation.save()
                table.disponible = False
                table.save()
                try:
                    send_mail(
                        'Confirmation de votre réservation',
                        f"Bonjour {reservation.nom},\n\nVotre réservation pour le {reservation.date} à {reservation.heure} a été confirmée. Table n°{table.numero}.",
                        settings.DEFAULT_FROM_EMAIL,
                        [reservation.email],
                        fail_silently=True,
                    )
                except Exception:
                    messages.warning(request, "Réservation confirmée, mais l'email n'a pas pu être envoyé.")
                messages.success(request, "Réservation confirmée avec succès.")
                return redirect('restaurant:admin_reservations')
        except Table.DoesNotExist:
            messages.error(request, "Table non disponible ou introuvable.")
    tables = Table.objects.filter(disponible=True, nombre_places__gte=reservation.personnes)
    return render(request, 'restaurant/confirmer_reservation.html', {
        'reservation': reservation,
        'tables': tables
    })

@login_required
def reservation_submit(request):
    """Vue pour soumettre une réservation avec attribution de table."""
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        table_id = request.POST.get('table_id')
        reservation = get_object_or_404(Reservation, id=reservation_id)
        try:
            table = Table.objects.get(id=table_id, disponible=True)
            with transaction.atomic():
                reservation.confirme = True
                reservation.table = table
                reservation.utilisateur = request.user
                reservation.save()
                table.disponible = False
                table.save()
                messages.success(request, "Réservation confirmée avec succès.")
                return redirect('restaurant:reservations')
        except Table.DoesNotExist:
            messages.error(request, "Table non disponible ou introuvable.")
    return redirect('restaurant:reservations')

@login_required
def annuler_reservation(request, reservation_id):
    """Vue pour annuler une réservation."""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if not (is_gerant(request.user) or is_serveur(request.user) or reservation.client == request.user):
        messages.error(request, "Accès non autorisé.")
        return redirect('restaurant:reservations')
    if request.method == 'POST':
        reservation.annule = True
        if reservation.table:
            reservation.table.disponible = True
            reservation.table.save()
        reservation.save()
        try:
            send_mail(
                'Annulation de votre réservation',
                f"Bonjour {reservation.nom},\n\nVotre réservation pour le {reservation.date} à {reservation.heure} a été annulée.",
                settings.DEFAULT_FROM_EMAIL,
                [reservation.email],
                fail_silently=True,
            )
            messages.success(request, "Réservation annulée avec succès.")
        except Exception:
            messages.warning(request, "Réservation annulée, mais l'email n'a pas pu être envoyé.")
        return redirect('restaurant:reservations')
    return render(request, 'restaurant/confirm_annuler_reservation.html', {'reservation': reservation})

@login_required
@gerant_required
def toggle_table_disponibilite(request, table_id):
    """Vue pour basculer la disponibilité d'une table."""
    table = get_object_or_404(Table, id=table_id)
    table.disponible = not table.disponible
    table.save()
    messages.success(request, f"Table {table.numero} est maintenant {'disponible' if table.disponible else 'indisponible'}.")
    return redirect('restaurant:tables')

def tables(request):
    """Vue pour afficher les tables."""
    tables = Table.objects.all().order_by('numero')
    return render(request, 'restaurant/tables.html', {'tables': tables})

# --- Additional Management Views ---

@login_required
@gerant_required
def gerer_personnel(request):
    """Vue pour gérer le personnel (gérant uniquement)."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Utilisateur '{user.username}' ajouté avec succès.")
            return redirect('restaurant:gerer_personnel')
    else:
        form = RegisterForm(initial={'role': 'serveur'})
    utilisateurs = Utilisateur.objects.exclude(role='client').order_by('username')
    return render(request, 'restaurant/gerer_personnel.html', {
        'form': form,
        'utilisateurs': utilisateurs
    })

@login_required
@gerant_required
def gerer_stocks(request):
    """Vue pour gérer les stocks des plats et ingrédients."""
    plats = Plat.objects.all().order_by('nom')
    ingredients = Ingredient.objects.all().order_by('nom')
    if request.method == 'POST':
        if 'plat_id' in request.POST:
            plat = get_object_or_404(Plat, id=request.POST.get('plat_id'))
            try:
                plat.stock = int(request.POST.get('stock'))
                plat.save()
                messages.success(request, f"Stock de {plat.nom} mis à jour.")
            except ValueError:
                messages.error(request, "Valeur de stock invalide.")
        elif 'ingredient_id' in request.POST:
            ingredient = get_object_or_404(Ingredient, id=request.POST.get('ingredient_id'))
            form = IngredientForm(request.POST, instance=ingredient)
            if form.is_valid():
                form.save()
                messages.success(request, f"Stock de {ingredient.nom} mis à jour.")
            else:
                messages.error(request, "Erreur dans le formulaire d'ingrédient.")
        return redirect('restaurant:gerer_stocks')
    else:
        ingredient_form = IngredientForm()
    return render(request, 'restaurant/gerer_stocks.html', {
        'plats': plats,
        'ingredients': ingredients,
        'ingredient_form': ingredient_form
    })

@login_required
@gerant_required
def gerer_configurations(request):
    """Vue pour gérer les configurations du restaurant (horaires, tables, etc.)."""
    if request.method == 'POST':
        table_id = request.POST.get('table_id')
        nombre_places = request.POST.get('nombre_places')
        if table_id and nombre_places:
            try:
                table = Table.objects.get(id=table_id)
                table.nombre_places = int(nombre_places)
                table.save()
                messages.success(request, f"Table {table.numero} mise à jour.")
            except (Table.DoesNotExist, ValueError):
                messages.error(request, "Erreur lors de la mise à jour de la table.")
        return redirect('restaurant:gerer_configurations')
    tables = Table.objects.all().order_by('numero')
    return render(request, 'restaurant/gerer_configurations.html', {'tables': tables})

@login_required
@delivery_required
def historique_livraisons(request):
    """Vue pour afficher l'historique des livraisons."""
    commandes = Commande.objects.filter(
        type_commande='a_livrer',
        statut__in=['en_livraison', 'livree']
    ).prefetch_related('items__plat').order_by('-date_commande')
    paginator = Paginator(commandes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'restaurant/historique_livraisons.html', {'commandes': page_obj})

@login_required
def notifications(request):
    """Vue pour afficher les notifications de l'utilisateur."""
    notifications = Notification.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = get_object_or_404(Notification, id=notification_id, utilisateur=request.user)
        notification.lu = True
        notification.save()
        messages.success(request, "Notification marquée comme lue.")
        return redirect('restaurant:notifications')
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'restaurant/notifications.html', {'notifications': page_obj})

@login_required
def envoyer_message(request):
    """Vue pour envoyer un message interne (notification)."""
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.auteur = request.user
            notification.utilisateur = form.cleaned_data['destinataire']
            notification.save()
            messages.success(request, "Message envoyé avec succès.")
            return redirect('restaurant:notifications')
    else:
        form = NotificationForm()
    return render(request, 'restaurant/envoyer_message.html', {'form': form})

@login_required
def update_profile(request):
    """Vue pour mettre à jour le profil utilisateur."""
    profil, created = ProfilUtilisateur.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfilUtilisateurForm(request.POST, instance=profil)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('restaurant:settings')
    else:
        form = ProfilUtilisateurForm(instance=profil)
    return render(request, 'restaurant/update_profile.html', {'form': form})

@login_required
def settings(request):
    """Vue pour les paramètres utilisateur."""
    return render(request, 'restaurant/settings.html')

def liste_produits(request):
    """Vue pour afficher la liste des produits (alias du menu)."""
    return menu(request)

def paiements(request):
    return render(request, 'restaurant/paiements.html')