from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Prueba rápida de envío de correo'
    
    def handle(self, *args, **options):
        self.stdout.write(' Probando envío de correo...')
        
        try:
            # Envío MUY simple
            """send_mail(
                subject=' Prueba de Correo - Sistema Médico',
                message='¡Hola! Este es un correo de prueba del sistema médico.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['lex8.aoa@gmail.com'],  # CAMBIA ESTO
                fail_silently=False,
            )"""
            send_mail(
                subject="Prueba de Alerta",
                message="Este es un mensaje de prueba.",
                from_email="Sistema Médico <alex.orellana.dev@gmail.com>",
                recipient_list=["lex8.aoa@gmail.com"],
                html_message="<h1>📩 Nuevo mensaje del sistema médico</h1><p>Esto es solo una prueba.</p>",
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(' ¡Correo enviado correctamente!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f' Error: {e}')
            )