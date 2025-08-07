from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from restaurant.models import Utilisateur, ProfilUtilisateur, Plat, Categorie, Reservation, Table
import datetime

class GerantViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Créer un utilisateur gérant
        self.user = Utilisateur.objects.create_user(username='gerant', password='testpass123', role='gerant')
        
        # Créer une catégorie et un plat
        self.categorie = Categorie.objects.create(nom='Entrées', active=True)
        self.plat = Plat.objects.create(
            nom='Salade César',
            description='Salade fraîche avec poulet',
            prix=12.50,
            categorie=self.categorie,
            disponible=True,
            stock=10
        )
        
        # Créer une table
        self.table = Table.objects.create(numero=1, nombre_places=4, disponible=True)
        
        # Créer une réservation
        self.reservation = Reservation.objects.create(
            client=self.user,
            nom='Jean Dupont',
            email='jean@example.com',
            telephone='0123456789',
            date=timezone.now().date(),
            heure=datetime.time(19, 0),
            personnes=4,
            confirme=False,
            annule=False
        )

    def test_dashboard_access_gerant(self):
        """Test que le gérant peut accéder au tableau de bord."""
        self.client.login(username='gerant', password='testpass123')
        response = self.client.get(reverse('restaurant:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'restaurant/dashboard.html')
        self.assertIn('plats', response.context)
        self.assertIn('stats', response.context)
        self.assertIn('alertes', response.context)

    def test_dashboard_access_non_gerant(self):
        """Test que les non-gérants sont redirigés."""
        user_client = Utilisateur.objects.create_user(username='client', password='testpass123', role='client')
        self.client.login(username='client', password='testpass123')
        response = self.client.get(reverse('restaurant:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirection car pas gérant

    def test_ajouter_plat(self):
        """Test l'ajout d'un plat par le gérant."""
        self.client.login(username='gerant', password='testpass123')
        data = {
            'nom': 'Pizza Margherita',
            'description': 'Pizza classique',
            'prix': 10.00,
            'categorie': self.categorie.id,
            'disponible': True,
            'stock': 20
        }
        response = self.client.post(reverse('restaurant:ajouter_plat'), data)
        self.assertEqual(response.status_code, 302)  # Redirection après succès
        self.assertTrue(Plat.objects.filter(nom='Pizza Margherita').exists())

    def test_modifier_plat(self):
        """Test la modification d'un plat par le gérant."""
        self.client.login(username='gerant', password='testpass123')
        data = {
            'nom': 'Salade César Modifiée',
            'description': 'Salade avec poulet grillé',
            'prix': 13.00,
            'categorie': self.categorie.id,
            'disponible': True,
            'stock': 15
        }
        response = self.client.post(reverse('restaurant:modifier_plat', args=[self.plat.id]), data)
        self.assertEqual(response.status_code, 302)  # Redirection après succès
        self.plat.refresh_from_db()
        self.assertEqual(self.plat.nom, 'Salade César Modifiée')

    def test_reservation_submit(self):
        """Test la confirmation d'une réservation avec attribution de table."""
        self.client.login(username='gerant', password='testpass123')
        data = {
            'reservation_id': self.reservation.id,
            'table_id': self.table.id
        }
        response = self.client.post(reverse('restaurant:reservation_submit'), data)
        self.assertEqual(response.status_code, 302)  # Redirection après succès
        self.reservation.refresh_from_db()
        self.table.refresh_from_db()
        self.assertTrue(self.reservation.confirme)
        self.assertFalse(self.table.disponible)
        self.assertEqual(self.reservation.table, self.table)