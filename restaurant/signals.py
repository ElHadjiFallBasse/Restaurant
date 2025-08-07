from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import ProfilUtilisateur, Panier

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        ProfilUtilisateur.objects.get_or_create(user=instance)
        Panier.objects.get_or_create(utilisateur=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profilutilisateur'):
        instance.profilutilisateur.save()