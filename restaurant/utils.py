from django.core.mail import send_mail

def send_confirmation_email(to_email, reservation):
    subject = "Confirmation de votre réservation"
    message = f"""Bonjour {reservation.client.username},

Votre réservation du {reservation.date} a été confirmée.
Table attribuée : {reservation.table.numero}.

Merci de votre confiance.
"""
    send_mail(subject, message, 'noreply@restaurant.com', [to_email])