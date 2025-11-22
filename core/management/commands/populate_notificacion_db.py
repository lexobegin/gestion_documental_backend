import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.utils import timezone
from datetime import datetime, time, timedelta
from core.models import *

fake = Faker('es_ES')

class Command(BaseCommand):
    help = 'Pobla la base de datos con notificaciones, documentos, recetas y seguimientos'

    def handle(self, *args, **kwargs):
        self.stdout.write("Poblando datos de notificaciones y documentos...")

        self.crear_documentos_medicos()
        self.crear_recetas_medicas()
        self.crear_seguimientos_pacientes()
        self.crear_notificaciones_sistema()
        self.crear_dispositivos_fcm()
        self.crear_tipos_examen()
        self.crear_solicitudes_examen()

        self.stdout.write(self.style.SUCCESS("¡Datos de notificaciones y documentos generados exitosamente!"))

    def crear_documentos_medicos(self):
        """Crear documentos médicos realistas"""
        consultas = Consulta.objects.all()[:20]  # Tomar primeras 20 consultas
        
        if not consultas.exists():
            self.stdout.write(self.style.WARNING("No hay consultas para crear documentos"))
            return

        tipos_documentos = [
            ('receta', 'Receta Médica'),
            ('laboratorio', 'Resultado de Laboratorio'),
            ('imagen', 'Imagen Médica'),
            ('consentimiento', 'Consentimiento Informado'),
            ('otro', 'Otro Documento')
        ]

        nombres_documentos = {
            'receta': [
                'Receta_Control_Regular.pdf',
                'Prescripción_Medicamentos.pdf',
                'Tratamiento_Farmacológico.pdf'
            ],
            'laboratorio': [
                'Hemograma_Completo.pdf',
                'Perfil_Bioquímico.pdf',
                'Análisis_Orina.pdf',
                'Prueba_Embarazo.pdf',
                'Niveles_Glucosa.pdf'
            ],
            'imagen': [
                'Radiografía_Tórax.dcm',
                'Ecografía_Abdominal.dcm',
                'Tomografía_Cráneo.dcm',
                'Resonancia_Columna.dcm'
            ],
            'consentimiento': [
                'Consentimiento_Procedimiento.pdf',
                'Autorización_Tratamiento.pdf',
                'Consentimiento_Cirugía.pdf'
            ],
            'otro': [
                'Informe_Evoulción.pdf',
                'Certificado_Medico.pdf',
                'Justificante_Ausencia.pdf'
            ]
        }

        documentos_creados = 0

        for consulta in consultas:
            # Crear 1-3 documentos por consulta
            for _ in range(random.randint(1, 3)):
                tipo_doc, nombre_tipo = random.choice(tipos_documentos)
                nombre_archivo = random.choice(nombres_documentos[tipo_doc])
                
                Documento.objects.create(
                    historia_clinica=consulta.historia_clinica,
                    consulta=consulta,
                    tipo_documento=tipo_doc,
                    nombre_archivo=nombre_archivo,
                    url_archivo=f"/media/documentos/{nombre_archivo}",
                    hash_archivo=fake.sha256(raw_output=False),
                    fecha_subida=consulta.fecha_consulta + timedelta(hours=random.randint(1, 24))
                )
                documentos_creados += 1

        self.stdout.write(f"Documentos médicos creados: {documentos_creados}")

    def crear_recetas_medicas(self):
        """Crear recetas médicas con medicamentos realistas"""
        consultas = Consulta.objects.filter(
            diagnostico__isnull=False
        )[:15]  # Tomar consultas con diagnóstico
        
        if not consultas.exists():
            self.stdout.write(self.style.WARNING("No hay consultas para crear recetas"))
            return

        medicamentos_reales = [
            # Analgésicos y antiinflamatorios
            {'nombre': 'Paracetamol 500mg', 'dosis': '1 comprimido', 'frecuencia': 'Cada 8 horas', 'duracion': '5 días'},
            {'nombre': 'Ibuprofeno 600mg', 'dosis': '1 comprimido', 'frecuencia': 'Cada 12 horas', 'duracion': '7 días'},
            {'nombre': 'Naproxeno 500mg', 'dosis': '1 comprimido', 'frecuencia': 'Cada 12 horas', 'duracion': '5 días'},
            
            # Antibióticos
            {'nombre': 'Amoxicilina 500mg', 'dosis': '1 cápsula', 'frecuencia': 'Cada 8 horas', 'duracion': '7 días'},
            {'nombre': 'Azitromicina 500mg', 'dosis': '1 comprimido', 'frecuencia': 'Una vez al día', 'duracion': '3 días'},
            {'nombre': 'Ciprofloxacino 500mg', 'dosis': '1 comprimido', 'frecuencia': 'Cada 12 horas', 'duracion': '7 días'},
            
            # Gastrointestinales
            {'nombre': 'Omeprazol 20mg', 'dosis': '1 cápsula', 'frecuencia': 'Una vez al día', 'duracion': '30 días'},
            {'nombre': 'Domperidona 10mg', 'dosis': '1 comprimido', 'frecuencia': 'Cada 8 horas', 'duracion': '7 días'},
            
            # Cardiovasculares
            {'nombre': 'Losartán 50mg', 'dosis': '1 comprimido', 'frecuencia': 'Una vez al día', 'duracion': '30 días'},
            {'nombre': 'Atorvastatina 20mg', 'dosis': '1 comprimido', 'frecuencia': 'Una vez al día', 'duracion': '30 días'},
            
            # Respiratorios
            {'nombre': 'Salbutamol inhalador', 'dosis': '2 inhalaciones', 'frecuencia': 'Cada 6 horas', 'duracion': '15 días'},
            {'nombre': 'Montelukast 10mg', 'dosis': '1 comprimido', 'frecuencia': 'Una vez al día', 'duracion': '30 días'},
            
            # Neurológicos
            {'nombre': 'Sumatriptán 50mg', 'dosis': '1 comprimido', 'frecuencia': 'Al inicio migraña', 'duracion': '6 comprimidos'},
            {'nombre': 'Gabapentina 300mg', 'dosis': '1 cápsula', 'frecuencia': 'Cada 8 horas', 'duracion': '30 días'},
        ]

        indicaciones_comunes = [
            "Tomar con alimentos",
            "No tomar con alcohol",
            "Completar el tratamiento completo",
            "Suspender si aparece erupción cutánea",
            "Tomar con un vaso de agua",
            "Evitar manejar maquinaria pesada",
            "No tomar con antiácidos",
            "Conservar en lugar fresco y seco",
            "Agitar bien antes de usar",
            "Aplicar en zona afectada"
        ]

        recetas_creadas = 0

        for consulta in consultas:
            receta = Receta.objects.create(
                consulta=consulta,
                fecha_receta=consulta.fecha_consulta.date(),
                observaciones=fake.paragraph() if random.random() > 0.5 else None
            )

            # Agregar 2-4 medicamentos por receta
            medicamentos_receta = random.sample(medicamentos_reales, k=random.randint(2, 4))
            
            for med in medicamentos_receta:
                DetalleReceta.objects.create(
                    receta=receta,
                    medicamento=med['nombre'],
                    dosis=med['dosis'],
                    frecuencia=med['frecuencia'],
                    duracion=med['duracion'],
                    indicaciones=random.choice(indicaciones_comunes)
                )

            recetas_creadas += 1

        self.stdout.write(f"Recetas médicas creadas: {recetas_creadas}")
        self.stdout.write(f"Detalles de recetas creados: {DetalleReceta.objects.count()}")

    def crear_seguimientos_pacientes(self):
        """Crear seguimientos médicos realistas"""
        consultas = Consulta.objects.all()[:10]  # Tomar primeras 10 consultas
        
        if not consultas.exists():
            self.stdout.write(self.style.WARNING("No hay consultas para crear seguimientos"))
            return

        evoluciones_positivas = [
            "Paciente evoluciona favorablemente",
            "Mejoría significativa de los síntomas",
            "Tratamiento efectivo, continuar igual",
            "Signos vitales dentro de parámetros normales",
            "Disminución del dolor reportado",
            "Incremento en movilidad",
            "Mejoría en parámetros de laboratorio"
        ]

        recomendaciones_comunes = [
            "Continuar tratamiento actual",
            "Control en 1 semana",
            "Realizar estudios de laboratorio",
            "Modificar dosis según tolerancia",
            "Iniciar terapia física",
            "Cambios en estilo de vida",
            "Seguir dieta específica",
            "Evitar esfuerzos físicos",
            "Reposo relativo",
            "Aumentar hidratación"
        ]

        seguimientos_creados = 0

        for consulta in consultas:
            # Crear 1-2 seguimientos por consulta
            for i in range(random.randint(1, 2)):
                Seguimiento.objects.create(
                    consulta=consulta,
                    fecha_seguimiento=consulta.fecha_consulta.date() + timedelta(days=7 * (i + 1)),
                    observaciones=random.choice(evoluciones_positivas),
                    recomendaciones=random.choice(recomendaciones_comunes)
                )
                seguimientos_creados += 1

        self.stdout.write(f"Seguimientos médicos creados: {seguimientos_creados}")

    def crear_notificaciones_sistema(self):
        """Crear notificaciones del sistema realistas"""
        pacientes = Paciente.objects.all()[:8]
        medicos = Medico.objects.all()[:4]
        administradores = Administrador.objects.all()[:2]
        
        if not pacientes.exists():
            self.stdout.write(self.style.WARNING("No hay usuarios para crear notificaciones"))
            return

        # Notificaciones de citas para pacientes
        citas = AgendaCita.objects.all()[:10]
        for cita in citas:
            Notificacion.objects.create(
                usuario=cita.paciente.usuario,
                tipo='cita',
                titulo='Recordatorio de Cita',
                mensaje=f"Tiene cita con Dr. {cita.medico_especialidad.medico.usuario.nombre} el {cita.fecha_cita.strftime('%d/%m/%Y')} a las {cita.hora_cita.strftime('%H:%M')}",
                leida=random.choice([True, False]),
                fecha_envio=cita.fecha_creacion - timedelta(days=1),
                datos_adicionales={
                    'cita_id': cita.id,
                    'medico': cita.medico_especialidad.medico.usuario.nombre_completo,
                    'fecha': cita.fecha_cita.strftime('%d/%m/%Y'),
                    'hora': cita.hora_cita.strftime('%H:%M')
                }
            )

        # Notificaciones de sistema para administradores
        for admin in administradores:
            Notificacion.objects.create(
                usuario=admin.usuario,
                tipo='sistema',
                titulo='Mantenimiento Programado',
                mensaje='Se programó mantenimiento del sistema para el próximo sábado de 2:00 a 4:00 AM',
                leida=False,
                fecha_envio=timezone.now() - timedelta(hours=2)
            )

        # Notificaciones de resultados para pacientes
        for paciente in pacientes[:4]:
            Notificacion.objects.create(
                usuario=paciente.usuario,
                tipo='resultado',
                titulo='Resultados Disponibles',
                mensaje='Los resultados de sus últimos exámenes de laboratorio están disponibles',
                leida=random.choice([True, False]),
                fecha_envio=timezone.now() - timedelta(days=random.randint(1, 3))
            )

        self.stdout.write(f"Notificaciones creadas: {Notificacion.objects.count()}")

    def crear_dispositivos_fcm(self):
        """Crear dispositivos FCM de ejemplo (simulados)"""
        usuarios = Usuario.objects.all()[:6]  # Algunos usuarios tendrán dispositivos
        
        if not usuarios.exists():
            self.stdout.write(self.style.WARNING("No hay usuarios para crear dispositivos"))
            return

        plataformas = ['android', 'ios', 'web']
        dispositivos_creados = 0

        for usuario in usuarios:
            # 70% de probabilidad de tener dispositivo
            if random.random() < 0.7:
                Dispositivo.objects.create(
                    usuario=usuario,
                    token_fcm=f"fcm_token_{usuario.id}_{fake.sha1()}"[:100],  # Token simulado
                    plataforma=random.choice(plataformas),
                    activo=random.choice([True, True, True, False])  # 75% activos
                )
                dispositivos_creados += 1

        self.stdout.write(f"Dispositivos FCM creados: {dispositivos_creados}")

    def crear_tipos_examen(self):
        """Crear tipos de examen médico realistas"""
        tipos_examen = [
            {
                'codigo': 'HEMO',
                'nombre': 'Hemograma Completo',
                'descripcion': 'Análisis de células sanguíneas: glóbulos rojos, blancos y plaquetas',
                'indicaciones': 'Ayuno de 8 horas recomendado',
                'urgencia_default': 'Rutina'
            },
            {
                'codigo': 'GLUC',
                'nombre': 'Glucosa en Sangre',
                'descripcion': 'Medición de niveles de glucosa en sangre',
                'indicaciones': 'Ayuno de 8-12 horas requerido',
                'urgencia_default': 'Rutina'
            },
            {
                'codigo': 'COLEST',
                'nombre': 'Perfil Lipídico',
                'descripcion': 'Análisis de colesterol total, HDL, LDL y triglicéridos',
                'indicaciones': 'Ayuno de 12 horas requerido',
                'urgencia_default': 'Rutina'
            },
            {
                'codigo': 'TSH',
                'nombre': 'Hormona Estimulante de Tiroides',
                'descripcion': 'Evaluación de función tiroidea',
                'indicaciones': 'No requiere ayuno',
                'urgencia_default': 'Rutina'
            },
            {
                'codigo': 'RAD_TORAX',
                'nombre': 'Radiografía de Tórax',
                'descripcion': 'Estudio imagenológico del tórax',
                'indicaciones': 'Remover objetos metálicos',
                'urgencia_default': 'Urgente'
            },
            {
                'codigo': 'ECO_ABD',
                'nombre': 'Ecografía Abdominal',
                'descripcion': 'Estudio ultrasonográfico de órganos abdominales',
                'indicaciones': 'Ayuno de 6 horas y vejiga llena',
                'urgencia_default': 'Rutina'
            },
            {
                'codigo': 'UROCULT',
                'nombre': 'Urocultivo',
                'descripcion': 'Cultivo de orina para detectar infecciones',
                'indicaciones': 'Primera orina de la mañana',
                'urgencia_default': 'Urgente'
            },
            {
                'codigo': 'PCR',
                'nombre': 'Proteína C Reactiva',
                'descripcion': 'Marcador de inflamación e infección',
                'indicaciones': 'No requiere ayuno',
                'urgencia_default': 'Urgente'
            }
        ]

        for tipo in tipos_examen:
            TipoExamen.objects.get_or_create(
                codigo=tipo['codigo'],
                defaults={
                    'nombre': tipo['nombre'],
                    'descripcion': tipo['descripcion'],
                    'indicaciones': tipo['indicaciones'],
                    'urgencia_default': tipo['urgencia_default'],
                    'activo': True
                }
            )

        self.stdout.write(f"Tipos de examen creados: {TipoExamen.objects.count()}")

    def crear_solicitudes_examen(self):
        """Crear solicitudes de examen realistas"""
        consultas = Consulta.objects.all()[:8]
        tipos_examen = TipoExamen.objects.filter(activo=True)
        
        if not consultas.exists() or not tipos_examen.exists():
            self.stdout.write(self.style.WARNING("No hay consultas o tipos de examen para crear solicitudes"))
            return

        urgencias = ['Rutina', 'Urgente', 'Emergencia']
        estados = ['solicitado', 'completado']
        
        solicitudes_creadas = 0

        for consulta in consultas:
            # 50% de probabilidad de tener solicitud de examen
            if random.random() < 0.5:
                tipo_examen = random.choice(list(tipos_examen))
                estado = random.choice(estados)
                
                solicitud = SolicitudExamen.objects.create(
                    consulta=consulta,
                    paciente=consulta.historia_clinica.paciente,
                    medico=consulta.medico,
                    tipo_examen=tipo_examen,
                    urgencia=random.choice(urgencias),
                    indicaciones_especificas=fake.sentence() if random.random() > 0.3 else None,
                    estado=estado
                )

                # Si está completado, agregar resultados
                if estado == 'completado':
                    solicitud.resultados = fake.paragraph()
                    solicitud.observaciones = "Resultados dentro de parámetros normales" if random.random() > 0.3 else "Se recomienda seguimiento"
                    solicitud.fecha_resultado = consulta.fecha_consulta + timedelta(days=random.randint(1, 3))
                    solicitud.save()

                solicitudes_creadas += 1

        self.stdout.write(f"Solicitudes de examen creadas: {solicitudes_creadas}")