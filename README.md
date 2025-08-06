# 🍽️ Restaurant Management System

Une plateforme complète de gestion de restaurant développée avec Django, offrant une interface moderne et intuitive pour gérer tous les aspects d'un restaurant.

## ✨ Fonctionnalités

### 📊 Tableau de Bord
- Vue d'ensemble des statistiques en temps réel
- Commandes du jour et chiffre d'affaires
- État des tables et alertes de stock
- Actions rapides pour les tâches courantes

### 🍽️ Gestion du Menu
- Catégorisation des plats
- Gestion des prix et disponibilité
- Temps de préparation et allergènes
- Recherche et filtrage avancés

### 📋 Gestion des Commandes
- Création et suivi des commandes
- Statuts en temps réel (en attente, préparation, prêt, servi, payé)
- Calcul automatique des totaux avec TVA
- Historique complet des commandes

### 🪑 Gestion des Tables
- Vue d'ensemble du statut des tables
- Basculement disponible/occupé en un clic
- Capacité et emplacement des tables
- Interface visuelle intuitive

### 👥 Gestion des Clients
- Base de données des clients
- Programme de fidélité avec points
- Historique des commandes par client
- Recherche et filtrage

### 📅 Système de Réservations
- Planification des réservations
- Gestion des statuts (confirmé, installé, terminé)
- Vue calendrier des réservations
- Demandes spéciales

### 📦 Gestion d'Inventaire
- Suivi du stock en temps réel
- Alertes de réapprovisionnement
- Gestion des fournisseurs
- Coûts par unité

### 👨‍💼 Gestion du Personnel
- Profils des employés avec rôles
- Suivi des salaires et dates d'embauche
- Permissions basées sur les rôles
- Personnel actif/inactif

## 🚀 Technologies Utilisées

- **Backend**: Django 4.2.7, Django REST Framework
- **Frontend**: Bootstrap 5, jQuery, HTML5/CSS3
- **Base de données**: SQLite (développement)
- **Authentification**: Django Auth System
- **API**: RESTful API avec filtrage et recherche
- **Styling**: CSS personnalisé avec animations

## 📋 Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)

## 🛠️ Installation

1. **Cloner le projet**
   ```bash
   git clone <repository-url>
   cd restaurant-management
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```

4. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

5. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

6. **Accéder à l'application**
   - Interface principale: http://127.0.0.1:8000/
   - Administration Django: http://127.0.0.1:8000/admin/
   - API REST: http://127.0.0.1:8000/api/

## 🔧 Configuration

### Variables d'environnement (optionnel)
Créez un fichier `.env` à la racine du projet :
```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### Paramètres principaux
- **Langue**: Français (fr-fr)
- **Fuseau horaire**: Europe/Paris
- **Authentification**: Session-based
- **Permissions API**: Authentification requise

## 📊 Structure du Projet

```
restaurant_management/
├── restaurant/                 # Application principale
│   ├── models.py              # Modèles de données
│   ├── views.py               # Vues web
│   ├── api_views.py           # Vues API REST
│   ├── serializers.py         # Sérialiseurs DRF
│   ├── forms.py               # Formulaires Django
│   ├── admin.py               # Configuration admin
│   └── urls.py                # URLs de l'app
├── templates/                 # Templates HTML
│   ├── base.html              # Template de base
│   └── restaurant/            # Templates spécifiques
├── static/                    # Fichiers statiques
│   ├── css/style.css          # Styles personnalisés
│   └── js/main.js             # JavaScript
├── restaurant_management/     # Configuration Django
├── requirements.txt           # Dépendances Python
└── manage.py                  # Script de gestion Django
```

## 🎯 Utilisation

### Interface Web
1. Connectez-vous avec vos identifiants
2. Accédez au tableau de bord pour une vue d'ensemble
3. Naviguez entre les différentes sections via le menu
4. Utilisez les actions rapides pour les tâches courantes

### API REST
L'API offre des endpoints pour toutes les fonctionnalités :

- **GET /api/menu-items/** - Liste des plats
- **POST /api/orders/** - Créer une commande
- **GET /api/tables/available/** - Tables disponibles
- **GET /api/orders/today/** - Commandes du jour
- **POST /api/tables/{id}/toggle_availability/** - Changer statut table

Documentation complète disponible à `/api/`

## 🔐 Authentification et Permissions

- **Authentification requise** pour toutes les fonctionnalités
- **Rôles du personnel** : Serveur, Chef, Manager, Caissier, Hôte
- **Permissions granulaires** basées sur les rôles
- **Session-based authentication** pour l'interface web
- **Token authentication** disponible pour l'API

## 🎨 Interface Utilisateur

- **Design moderne** avec Bootstrap 5
- **Interface responsive** adaptée aux mobiles et tablettes
- **Animations fluides** et transitions CSS
- **Thème cohérent** avec palette de couleurs professionnelle
- **Icônes Bootstrap Icons** pour une meilleure UX
- **Notifications en temps réel** pour les actions utilisateur

## 📱 Fonctionnalités Avancées

### AJAX et Temps Réel
- Mise à jour des statuts sans rechargement
- Notifications instantanées
- Actualisation automatique du tableau de bord

### Recherche et Filtrage
- Recherche en temps réel avec debounce
- Filtres avancés sur toutes les listes
- Pagination automatique

### Raccourcis Clavier
- `Ctrl+N` : Nouvelle commande
- `Ctrl+D` : Retour au tableau de bord

## 🚀 Déploiement

### Préparation pour la production
1. Configurez les variables d'environnement
2. Utilisez une base de données PostgreSQL/MySQL
3. Configurez un serveur web (Nginx/Apache)
4. Utilisez Gunicorn comme serveur WSGI
5. Configurez les fichiers statiques avec WhiteNoise

### Variables d'environnement de production
```
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://user:pass@host:port/dbname
SECRET_KEY=your-production-secret-key
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Pushez la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou support :
- Créez une issue sur GitHub
- Contactez l'équipe de développement

## 🔄 Mises à Jour

### Version 1.0.0
- ✅ Système de gestion complet
- ✅ Interface web moderne
- ✅ API REST complète
- ✅ Authentification et permissions
- ✅ Responsive design

### Prochaines fonctionnalités
- 📊 Rapports et analytics avancés
- 📱 Application mobile
- 💳 Intégration paiement
- 📧 Notifications par email
- 🔄 Synchronisation multi-restaurants

---

Développé avec ❤️ en Django pour la gestion moderne de restaurants.