from django.core.management.base import BaseCommand
from core.services.notificaciones import ServicioNotificaciones

class Command(BaseCommand):
    help = 'Prueba rápida de Firebase'
    
    def handle(self, *args, **options):
        self.stdout.write('Probando Firebase...')
        
        # Reemplaza con un token FCM real de tu app Flutter
        token_prueba = "fCuUtZvMTUSungzCcRRkcp:APA91bGoRAmoHfIw_Mu5Ymxs56n4iYM1BH7luORBL5KvC9UEZUd4Adhbi-yAS0NEI9pfx9CHK0o_Zy29bRTu09oXoHOTG1o6W-asXR1FQDahq_TEvG4K4B8"  
        
        if token_prueba == "TOKEN_FCM_DE_PRUEBA":
            self.stdout.write(
                self.style.WARNING('Reemplaza TOKEN_FCM_DE_PRUEBA con un token real')
            )
            return
        
        try:
            resultado = ServicioNotificaciones.enviar_notificacion_individual_fcm(
                token_prueba,
                "Prueba Firebase",
                "¡Notificación de prueba del sistema médico!"
            )
            
            if resultado:
                self.stdout.write(
                    self.style.SUCCESS('Notificación enviada correctamente')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Error enviando notificación')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )