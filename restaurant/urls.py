from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'restaurant'

urlpatterns = [
    # Authentication
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('inscription/', views.register_view, name='inscription'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/serveur/', views.dashboard_serveur, name='dashboard_serveur'),
    path('dashboard/cuisine/', views.cuisine_dashboard, name='cuisine_dashboard'),
    path('dashboard/livreur/', views.dashboard_livreur, name='dashboard_livreur'),
    path('cuisine/stats/', views.cuisine_stats, name='cuisine_stats'),
    path('statistiques/', views.statistiques, name='statistiques'),
    path('gerer-personnel/', views.gerer_personnel, name='gerer_personnel'),
    path('gerer-stocks/', views.gerer_stocks, name='gerer_stocks'),
    path('gerer-configurations/', views.gerer_configurations, name='gerer_configurations'),

    # Menu Management
    path('plats/', views.menu, name='menu'),
    path('plats/ajouter/', views.ajouter_plat, name='ajouter_plat'),
    path('plats/<int:pk>/modifier/', views.modifier_plat, name='modifier_plat'),
    path('plats/<int:pk>/supprimer/', views.supprimer_plat, name='supprimer_plat'),
    path('produits/', views.liste_produits, name='liste_produits'),
    path('plats/<int:plat_id>/avis/', views.ajouter_avis, name='ajouter_avis'),
    path('plats/<int:plat_id>/favori/', views.ajouter_favori, name='ajouter_favori'),
    path('api/plats/<int:plat_id>/toggle-disponibilite/', views.api_toggle_disponibilite, name='api_toggle_disponibilite'),

    # Cart and Orders
    path('panier/', views.panier, name='panier'),
    path('panier/vider/', views.vider_panier, name='vider_panier'),
    path('panier/ajouter/<int:plat_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('commander/<int:plat_id>/', views.ajouter_au_panier, name='commander_plat'),
    path('panier/modifier/<int:item_id>/<str:action>/', views.modifier_panier, name='modifier_quantite'),
    path('commande/valider/', views.valider_commande, name='valider_commande'),
    path('commande/<int:commande_id>/', views.detail_commande, name='detail_commande'),
    path('commande/<int:commande_id>/annuler/', views.annuler_commande, name='annuler_commande'),
    path('commande/<int:commande_id>/encaisser/', views.encaisser_commande, name='encaisser_commande'),
    path('paiement/<int:paiement_id>/reçu/', views.generer_recu_pdf, name='generer_recu_pdf'),
    path('mes-commandes/', views.mes_commandes, name='mes_commandes'),
    path('historique-livraisons/', views.historique_livraisons, name='historique_livraisons'),

    # Reservations
    path('reserver/', views.reserver_table, name='reserver_table'),
    path('reservations/', views.reservations, name='reservations'),
    path('admin/reservations/', views.admin_reservations, name='admin_reservations'),
    path('admin/reservations/<int:reservation_id>/confirmer/', views.confirmer_reservation, name='confirmer_reservation'),
    path('gerant/reservations/', views.reservations_non_confirmees, name='reservations_non_confirmees'),
    path('reservation/submit/', views.reservation_submit, name='reservation_submit'),
    path('tables/<int:table_id>/toggle-disponibilite/', views.toggle_table_disponibilite, name='toggle_table_disponibilite'),
    path('reservations/<int:reservation_id>/annuler/', views.annuler_reservation, name='annuler_reservation'),

    # Informational Pages
    path('accueil/', views.accueil_public, name='accueil_public'),
    path('home/', views.home, name='home_alias'),
    path('infos/', views.infos_restaurant, name='infos_restaurant'),
    path('horaires/', views.horaires, name='horaires'),
    path('tables/', views.tables, name='tables'),
    path('paiements/', views.paiements, name='paiements'),
    path('settings/', views.settings, name='settings'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('contact/', views.contact, name='contact'),
    path('notifications/', views.notifications, name='notifications'),
    path('envoyer-message/', views.envoyer_message, name='envoyer_message'),

    # API Endpoints
    path('api/panier/count/', views.api_panier_count, name='api_panier_count'),
    path('api/plats/<int:plat_id>/toggle-disponibilite/', views.api_toggle_disponibilite, name='api_toggle_disponibilite'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)