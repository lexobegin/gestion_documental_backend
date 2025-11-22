import os
import json
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from ..models import Notificacion, Dispositivo

# Inicializar Firebase Admin SDK
def inicializar_firebase():
    try:
        # Ruta al archivo JSON de servicio de Firebase
        cred_path = os.path.join(settings.BASE_DIR, 'firebase', 'service-account-key.json')
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(" Firebase Admin SDK inicializado correctamente")
            return True
        else:
            print(" Archivo de credenciales de Firebase no encontrado")
            return False
    except Exception as e:
        print(f" Error inicializando Firebase: {str(e)}")
        return False

# Inicializar al importar el módulo
firebase_initialized = inicializar_firebase()

class ServicioNotificaciones:
    """
    Servicio para manejar notificaciones push (FCM) y correos electrónicos
    """
    
    @staticmethod
    def enviar_notificacion_fcm(tokens, titulo, mensaje, datos_adicionales=None):
        """
        Enviar notificación push mediante Firebase Cloud Messaging
        Usando Firebase Admin SDK
        """
        if not firebase_initialized:
            print("Firebase no está inicializado")
            return False
        
        if not tokens:
            print("No hay tokens FCM para enviar")
            return False
        
        # Preparar el mensaje para múltiples dispositivos
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje,
            ),
            data=datos_adicionales or {},
            tokens=tokens,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1
                    )
                )
            ),
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    channel_id='default'
                )
            )
        )
        
        try:
            # Enviar mensaje a múltiples dispositivos
            response = messaging.send_multicast(message)
            
            print(f" Notificaciones enviadas: {response.success_count} exitosas, {response.failure_count} fallidas")
            
            # Log de respuestas individuales
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        print(f" Error en token {tokens[idx]}: {resp.exception}")
            
            return response.success_count > 0
            
        except Exception as e:
            print(f" Error enviando notificación FCM: {str(e)}")
            return False
    
    @staticmethod
    def enviar_notificacion_individual_fcm(token, titulo, mensaje, datos_adicionales=None):
        """
        Enviar notificación a un solo dispositivo
        """
        if not firebase_initialized:
            print("Firebase no está inicializado")
            return False
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje,
            ),
            data=datos_adicionales or {},
            token=token,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1
                    )
                )
            ),
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    channel_id='default'
                )
            )
        )
        
        try:
            response = messaging.send(message)
            print(f" Notificación individual enviada: {response}")
            return True
        except Exception as e:
            print(f" Error enviando notificación individual: {str(e)}")
            return False
    
    @staticmethod
    def enviar_correo(destinatario, asunto, mensaje_html, mensaje_texto=None):
        """
        Enviar correo electrónico mediante Gmail
        """
        try:
            send_mail(
                subject=asunto,
                message=mensaje_texto or asunto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                html_message=mensaje_html,
                fail_silently=False
            )
            print(f" Correo enviado a: {destinatario}")
            return True
        except Exception as e:
            print(f" Error enviando correo a {destinatario}: {str(e)}")
            return False
    
    @staticmethod
    def crear_y_enviar_notificacion(usuario, tipo, titulo, mensaje, datos_adicionales=None):
        """
        Crear notificación en BD y enviar push/email
        """
        # Crear registro en base de datos
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            datos_adicionales=datos_adicionales
        )
        
        # Enviar notificación push si tiene dispositivos registrados
        dispositivos = Dispositivo.objects.filter(usuario=usuario, activo=True)
        tokens_fcm = [dispositivo.token_fcm for dispositivo in dispositivos]
        
        push_exitoso = False
        if tokens_fcm:
            print(f" Enviando notificación push a {len(tokens_fcm)} dispositivos")
            push_exitoso = ServicioNotificaciones.enviar_notificacion_fcm(
                tokens_fcm, titulo, mensaje, datos_adicionales
            )
        else:
            print(" No hay dispositivos registrados para notificaciones push")
        
        # Si no hay dispositivos o falló FCM, enviar por correo
        if not push_exitoso:
            print(" Enviando notificación por correo...")
            correo_exitoso = ServicioNotificaciones.enviar_correo(
                usuario.email,
                titulo,
                f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c5aa0;">{titulo}</h2>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <p style="margin: 0; color: #333;">{mensaje}</p>
                    </div>
                    <p style="color: #666; font-size: 12px; margin-top: 20px;">
                        Fecha: {timezone.now().strftime('%d/%m/%Y %H:%M')}<br>
                        Sistema de Gestión Médica
                    </p>
                </div>
                """,
                mensaje_texto=f"{titulo}\n\n{mensaje}\n\nFecha: {timezone.now().strftime('%d/%m/%Y %H:%M')}"
            )
            
            if not correo_exitoso:
                print(f" No se pudo enviar notificación a {usuario.email}")
        
        return notificacion

class NotificacionesCitas:
    """
    Servicio específico para notificaciones de citas
    """
    
    @staticmethod
    def notificar_cambio_estado_cita(cita, estado_anterior, estado_nuevo, usuario_actor):
        """
        Notificar cambio de estado de cita (confirmada, cancelada, reprogramada)
        """
        paciente = cita.paciente.usuario
        medico_nombre = cita.medico_especialidad.medico.usuario.nombre_completo
        fecha_cita = cita.fecha_cita.strftime('%d/%m/%Y')
        hora_cita = cita.hora_cita.strftime('%H:%M')
        
        if estado_nuevo == 'confirmada':
            titulo = " Cita Confirmada"
            mensaje = f"Su cita con Dr. {medico_nombre} para el {fecha_cita} a las {hora_cita} ha sido confirmada."
        elif estado_nuevo == 'cancelada':
            titulo = " Cita Cancelada"
            mensaje = f"Su cita con Dr. {medico_nombre} para el {fecha_cita} a las {hora_cita} ha sido cancelada."
        else:
            titulo = " Cita Actualizada"
            mensaje = f"Su cita con Dr. {medico_nombre} ha sido actualizada. Nueva fecha: {fecha_cita} a las {hora_cita}."
        
        datos_adicionales = {
            'tipo': 'cita',
            'cita_id': str(cita.id),
            'estado': estado_nuevo,
            'accion': 'cambio_estado',
            'medico': medico_nombre,
            'fecha': fecha_cita,
            'hora': hora_cita
        }
        
        return ServicioNotificaciones.crear_y_enviar_notificacion(
            paciente, 'cita', titulo, mensaje, datos_adicionales
        )
    
    @staticmethod
    def notificar_reprogramacion_cita(cita, fecha_anterior, hora_anterior, usuario_actor):
        """
        Notificar reprogramación de cita
        """
        paciente = cita.paciente.usuario
        medico_nombre = cita.medico_especialidad.medico.usuario.nombre_completo
        nueva_fecha = cita.fecha_cita.strftime('%d/%m/%Y')
        nueva_hora = cita.hora_cita.strftime('%H:%M')
        
        titulo = " Cita Reprogramada"
        mensaje = f"Su cita con Dr. {medico_nombre} ha sido reprogramada. Nueva fecha: {nueva_fecha} a las {nueva_hora}."
        
        datos_adicionales = {
            'tipo': 'cita',
            'cita_id': str(cita.id),
            'estado': cita.estado,
            'accion': 'reprogramacion',
            'medico': medico_nombre,
            'fecha': nueva_fecha,
            'hora': nueva_hora
        }
        
        return ServicioNotificaciones.crear_y_enviar_notificacion(
            paciente, 'cita', titulo, mensaje, datos_adicionales
        )
    
    @staticmethod
    def notificar_nueva_cita(cita):
        """
        Notificar creación de nueva cita
        """
        paciente = cita.paciente.usuario
        medico_nombre = cita.medico_especialidad.medico.usuario.nombre_completo
        fecha_cita = cita.fecha_cita.strftime('%d/%m/%Y')
        hora_cita = cita.hora_cita.strftime('%H:%M')
        
        titulo = " Nueva Cita Agendada"
        mensaje = f"Se ha agendado una cita con Dr. {medico_nombre} para el {fecha_cita} a las {hora_cita}. Estado: Pendiente."
        
        datos_adicionales = {
            'tipo': 'cita',
            'cita_id': str(cita.id),
            'estado': cita.estado,
            'accion': 'nueva_cita',
            'medico': medico_nombre,
            'fecha': fecha_cita,
            'hora': hora_cita
        }
        
        return ServicioNotificaciones.crear_y_enviar_notificacion(
            paciente, 'cita', titulo, mensaje, datos_adicionales
        )

# Servicio para notificaciones de exámenes
class NotificacionesExamenes:
    """
    Servicio para notificaciones de exámenes médicos
    """
    
    @staticmethod
    def notificar_nuevo_examen(solicitud_examen):
        """
        Notificar nueva solicitud de examen
        """
        paciente = solicitud_examen.paciente.usuario
        tipo_examen = solicitud_examen.tipo_examen.nombre
        
        titulo = " Nuevo Examen Solicitado"
        mensaje = f"Se ha solicitado un examen de {tipo_examen}. Estado: Pendiente."
        
        datos_adicionales = {
            'tipo': 'examen',
            'examen_id': str(solicitud_examen.id),
            'tipo_examen': tipo_examen,
            'estado': 'solicitado'
        }
        
        return ServicioNotificaciones.crear_y_enviar_notificacion(
            paciente, 'resultado', titulo, mensaje, datos_adicionales
        )
    
    @staticmethod
    def notificar_resultado_examen(solicitud_examen):
        """
        Notificar que hay resultados de examen disponibles
        """
        paciente = solicitud_examen.paciente.usuario
        tipo_examen = solicitud_examen.tipo_examen.nombre
        
        titulo = " Resultados de Examen Disponibles"
        mensaje = f"Los resultados de su examen de {tipo_examen} están disponibles."
        
        datos_adicionales = {
            'tipo': 'examen',
            'examen_id': str(solicitud_examen.id),
            'tipo_examen': tipo_examen,
            'estado': 'completado'
        }
        
        return ServicioNotificaciones.crear_y_enviar_notificacion(
            paciente, 'resultado', titulo, mensaje, datos_adicionales
        )