import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.utils import timezone
from datetime import datetime, time, timedelta
from core.models import *

fake = Faker('es_ES')

class Command(BaseCommand):
    help = 'Pobla la base de datos con componentes UI, permisos granulares y horarios médicos'

    def handle(self, *args, **kwargs):
        self.stdout.write("Poblando datos del sistema...")

        self.crear_tipos_componentes()
        self.crear_componentes_ui()
        self.crear_permisos_componentes()
        self.crear_horarios_medicos()
        self.crear_historias_clinicas()
        self.crear_citas_ejemplo()
        self.crear_consultas_medicas()
        self.crear_registros_backup()
        self.crear_bitacora()

        self.stdout.write(self.style.SUCCESS("¡Datos del sistema generados exitosamente!"))

    def crear_tipos_componentes(self):
        tipos = [
            ('Menú', 'Elementos de navegación principal'),
            ('Botón', 'Botones de acción en formularios'),
            ('Formulario', 'Formularios completos de entrada de datos'),
            ('Sección', 'Secciones de contenido en páginas'),
            ('Reporte', 'Reportes y visualizaciones de datos'),
            ('Modal', 'Ventanas modales y diálogos')
        ]

        for nombre, descripcion in tipos:
            TipoComponente.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion}
            )
        self.stdout.write(f"Tipos de componentes creados: {TipoComponente.objects.count()}")

    def crear_componentes_ui(self):
        tipo_menu = TipoComponente.objects.get(nombre='Menú')
        tipo_boton = TipoComponente.objects.get(nombre='Botón')
        tipo_form = TipoComponente.objects.get(nombre='Formulario')
        tipo_seccion = TipoComponente.objects.get(nombre='Sección')

        componentes = [
            # Menús principales
            (tipo_menu, 'menu_usuarios', 'Gestión de Usuarios', 'Administración', '/usuarios', 'users', 1),
            (tipo_menu, 'menu_medicos', 'Gestión de Médicos', 'Administración', '/medicos', 'user-md', 2),
            (tipo_menu, 'menu_pacientes', 'Gestión de Pacientes', 'Administración', '/pacientes', 'heart', 3),
            (tipo_menu, 'menu_especialidades', 'Especialidades', 'Administración', '/especialidades', 'stethoscope', 4),
            (tipo_menu, 'menu_agenda', 'Agenda Médica', 'Médicos', '/agenda', 'calendar', 5),
            (tipo_menu, 'menu_historias', 'Historias Clínicas', 'Médicos', '/historias', 'file-medical', 6),
            (tipo_menu, 'menu_reportes', 'Reportes', 'Administración', '/reportes', 'chart-bar', 7),
            
            # Botones de acción
            (tipo_boton, 'btn_crear_usuario', 'Crear Usuario', 'Usuarios', None, 'plus', 10),
            (tipo_boton, 'btn_editar_usuario', 'Editar Usuario', 'Usuarios', None, 'edit', 11),
            (tipo_boton, 'btn_eliminar_usuario', 'Eliminar Usuario', 'Usuarios', None, 'trash', 12),
            (tipo_boton, 'btn_exportar_usuario', 'Exportar Usuarios', 'Usuarios', None, 'download', 13),
            
            (tipo_boton, 'btn_crear_medico', 'Crear Médico', 'Médicos', None, 'plus', 20),
            (tipo_boton, 'btn_editar_medico', 'Editar Médico', 'Médicos', None, 'edit', 21),
            
            (tipo_boton, 'btn_crear_cita', 'Solicitar Cita', 'Agenda', None, 'calendar-plus', 30),
            (tipo_boton, 'btn_cancelar_cita', 'Cancelar Cita', 'Agenda', None, 'calendar-times', 31),
            (tipo_boton, 'btn_confirmar_cita', 'Confirmar Cita', 'Agenda', None, 'calendar-check', 32),
            
            # Formularios
            (tipo_form, 'form_usuario_completo', 'Formulario Completo Usuario', 'Usuarios', None, 'user-edit', 40),
            (tipo_form, 'form_medico_completo', 'Formulario Completo Médico', 'Médicos', None, 'user-md', 41),
            (tipo_form, 'form_consulta_medica', 'Formulario Consulta Médica', 'Consultas', None, 'notes-medical', 42),
            (tipo_form, 'form_historia_clinica', 'Formulario Historia Clínica', 'Historias', None, 'file-medical-alt', 43),
            
            # Secciones
            (tipo_seccion, 'seccion_datos_personales', 'Datos Personales', 'Perfil', None, 'user-circle', 50),
            (tipo_seccion, 'seccion_datos_medicos', 'Datos Médicos', 'Perfil', None, 'heartbeat', 51),
            (tipo_seccion, 'seccion_contacto_emergencia', 'Contacto de Emergencia', 'Perfil', None, 'phone-alt', 52),
        ]

        for tipo, codigo, nombre, modulo, ruta, icono, orden in componentes:
            ComponenteUI.objects.get_or_create(
                codigo_componente=codigo,
                defaults={
                    'tipo_componente': tipo,
                    'nombre_componente': nombre,
                    'modulo': modulo,
                    'ruta': ruta,
                    'icono': icono,
                    'orden': orden
                }
            )
        self.stdout.write(f"Componentes UI creados: {ComponenteUI.objects.count()}")

    def crear_permisos_componentes(self):
        # Obtener permisos y componentes
        permiso_admin = Permiso.objects.get(codigo='admin_full')
        permiso_ver_usuarios = Permiso.objects.get(codigo='ver_usuarios')
        permiso_crear_usuarios = Permiso.objects.get(codigo='crear_usuarios')
        permiso_editar_usuarios = Permiso.objects.get(codigo='editar_usuarios')
        
        # Asignar permisos completos al administrador
        componentes = ComponenteUI.objects.all()
        for componente in componentes:
            PermisoComponente.objects.get_or_create(
                permiso=permiso_admin,
                componente=componente,
                accion_permitida='todos'
            )
        
        # Permisos específicos para ver usuarios
        componentes_ver = ComponenteUI.objects.filter(
            codigo_componente__in=['menu_usuarios', 'seccion_datos_personales']
        )
        for componente in componentes_ver:
            PermisoComponente.objects.get_or_create(
                permiso=permiso_ver_usuarios,
                componente=componente,
                accion_permitida='ver'
            )
        
        self.stdout.write(f"Permisos de componentes creados: {PermisoComponente.objects.count()}")

    def crear_horarios_medicos(self):
        medicos = Medico.objects.all()
        
        # Mapeo de días en español
        dias_semana_espanol = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        
        # Horarios típicos de consulta
        horarios_tipicos = [
            (time(8, 0), time(12, 0)),   # Mañana
            (time(14, 0), time(18, 0)),  # Tarde
            (time(9, 0), time(13, 0)),   # Mañana alternativo
            (time(15, 0), time(19, 0)),  # Tarde alternativo
        ]

        for medico in medicos:
            # Cada médico tiene entre 3 y 5 días de atención
            dias_atencion = random.sample(dias_semana_espanol, k=random.randint(3, 5))
            
            for dia in dias_atencion:
                hora_inicio, hora_fin = random.choice(horarios_tipicos)
                
                HorarioMedico.objects.get_or_create(
                    medico=medico,
                    dia_semana=dia,
                    defaults={
                        'hora_inicio': hora_inicio,
                        'hora_fin': hora_fin,
                        'activo': True
                    }
                )
        
        self.stdout.write(f"Horarios médicos creados: {HorarioMedico.objects.count()}")

    def crear_historias_clinicas(self):
        pacientes = Paciente.objects.all()
        
        for paciente in pacientes:
            HistoriaClinica.objects.get_or_create(
                paciente=paciente,
                activo=True,
                defaults={
                    'observaciones_generales': fake.paragraph()
                }
            )
        
        self.stdout.write(f"Historias clínicas creadas: {HistoriaClinica.objects.count()}")

    def crear_citas_ejemplo(self):
        medicos = Medico.objects.all()[:4]  # Tomar primeros 4 médicos
        pacientes = Paciente.objects.all()[:6]  # Tomar primeros 6 pacientes
        
        if not medicos.exists():
            self.stdout.write(self.style.WARNING("No hay médicos para crear citas"))
            return
            
        if not pacientes.exists():
            self.stdout.write(self.style.WARNING("No hay pacientes para crear citas"))
            return

        estados = ['pendiente', 'confirmada', 'realizada']
        motivos = [
            "Consulta general", "Control rutinario", "Seguimiento tratamiento",
            "Chequeo anual", "Dolor persistente", "Segunda opinión"
        ]

        # Mapeo de días numérico a español
        dias_semana_map = {
            0: 'Lunes',
            1: 'Martes', 
            2: 'Miércoles',
            3: 'Jueves',
            4: 'Viernes',
            5: 'Sábado',
            6: 'Domingo'
        }

        citas_creadas = 0

        # Crear citas para los próximos 15 días
        for i in range(30):  # Intentar crear más citas
            medico = random.choice(list(medicos))
            paciente = random.choice(list(pacientes))
            
            # Fecha en los próximos 15 días
            fecha_cita = timezone.now().date() + timedelta(days=random.randint(1, 15))
            
            # Obtener el día de la semana en español
            dia_semana_num = fecha_cita.weekday()
            dia_semana_espanol = dias_semana_map[dia_semana_num]
            
            # Verificar horario disponible del médico
            horarios_medico = HorarioMedico.objects.filter(
                medico=medico, 
                dia_semana=dia_semana_espanol,
                activo=True
            )
            
            if horarios_medico.exists():
                horario = horarios_medico.first()
                
                # Generar hora aleatoria dentro del horario del médico
                hora_inicio = horario.hora_inicio
                hora_fin = horario.hora_fin
                
                # Asegurar que hay al menos 1 hora de diferencia
                if hora_fin.hour - hora_inicio.hour >= 1:
                    hora_cita = time(
                        random.randint(hora_inicio.hour, hora_fin.hour - 1),
                        random.choice([0, 15, 30, 45])
                    )
                    
                    # Verificar que no exista ya una cita en ese horario
                    cita_existente = AgendaCita.objects.filter(
                        medico=medico,
                        fecha_cita=fecha_cita,
                        hora_cita=hora_cita
                    ).exists()
                    
                    if not cita_existente:
                        AgendaCita.objects.create(
                            paciente=paciente,
                            medico=medico,
                            fecha_cita=fecha_cita,
                            hora_cita=hora_cita,
                            estado=random.choice(estados),
                            motivo=random.choice(motivos),
                            notas=fake.sentence() if random.random() > 0.5 else None
                        )
                        citas_creadas += 1
        
        self.stdout.write(f"Citas de ejemplo creadas: {citas_creadas}")

        # Si no se crearon citas, mostrar diagnóstico
        if citas_creadas == 0:
            self.stdout.write(self.style.WARNING("No se pudieron crear citas. Diagnóstico:"))
            self.stdout.write(f"- Médicos disponibles: {medicos.count()}")
            self.stdout.write(f"- Pacientes disponibles: {pacientes.count()}")
            self.stdout.write(f"- Horarios médicos creados: {HorarioMedico.objects.count()}")
            
            # Mostrar horarios de los médicos
            for medico in medicos:
                horarios = HorarioMedico.objects.filter(medico=medico)
                self.stdout.write(f"  - Dr. {medico.usuario.nombre}: {horarios.count()} horarios")
                for horario in horarios:
                    self.stdout.write(f"    * {horario.dia_semana}: {horario.hora_inicio} - {horario.hora_fin}")

    def crear_citas_ejemplo(self):
        medicos = Medico.objects.all()[:4]
        pacientes = Paciente.objects.all()[:6]
        
        if not medicos.exists():
            self.stdout.write(self.style.WARNING("No hay médicos para crear citas"))
            return
            
        if not pacientes.exists():
            self.stdout.write(self.style.WARNING("No hay pacientes para crear citas"))
            return

        estados = ['pendiente', 'confirmada', 'realizada']
        motivos = [
            "Consulta general", "Control rutinario", "Seguimiento tratamiento",
            "Chequeo anual", "Dolor persistente", "Segunda opinión"
        ]

        dias_semana_map = {
            0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 
            4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
        }

        citas_creadas = 0

        for i in range(30):
            medico = random.choice(list(medicos))
            paciente = random.choice(list(pacientes))
            
            fecha_cita = timezone.now().date() + timedelta(days=random.randint(1, 15))
            dia_semana_num = fecha_cita.weekday()
            dia_semana_espanol = dias_semana_map[dia_semana_num]
            
            horarios_medico = HorarioMedico.objects.filter(
                medico=medico, 
                dia_semana=dia_semana_espanol,
                activo=True
            )
            
            if horarios_medico.exists():
                horario = horarios_medico.first()
                hora_inicio = horario.hora_inicio
                hora_fin = horario.hora_fin
                
                if hora_fin.hour - hora_inicio.hour >= 1:
                    hora_cita = time(
                        random.randint(hora_inicio.hour, hora_fin.hour - 1),
                        random.choice([0, 15, 30, 45])
                    )
                    
                    cita_existente = AgendaCita.objects.filter(
                        medico=medico,
                        fecha_cita=fecha_cita,
                        hora_cita=hora_cita
                    ).exists()
                    
                    if not cita_existente:
                        AgendaCita.objects.create(
                            paciente=paciente,
                            medico=medico,
                            fecha_cita=fecha_cita,
                            hora_cita=hora_cita,
                            estado=random.choice(estados),
                            motivo=random.choice(motivos),
                            notas=fake.sentence() if random.random() > 0.5 else None
                        )
                        citas_creadas += 1
        
        self.stdout.write(f"Citas de ejemplo creadas: {citas_creadas}")

    def crear_consultas_medicas(self):
        """Crear consultas médicas realistas basadas en citas realizadas"""
        citas_realizadas = AgendaCita.objects.filter(estado='realizada')
        
        if not citas_realizadas.exists():
            self.stdout.write(self.style.WARNING("No hay citas realizadas para crear consultas"))
            return

        # Síntomas comunes por especialidad
        sintomas_por_especialidad = {
            'CARD': [
                "Dolor en el pecho", "Palpitaciones", "Falta de aire", "Mareos",
                "Hinchazón en piernas", "Presión arterial elevada"
            ],
            'DERM': [
                "Erupción cutánea", "Picazón", "Manchas en la piel", "Acné severo",
                "Caída de cabello", "Uñas quebradizas"
            ],
            'PED': [
                "Fiebre", "Tos persistente", "Dolor abdominal", "Vómitos",
                "Diarrea", "Falta de apetito"
            ],
            'NEUR': [
                "Dolor de cabeza intenso", "Mareos frecuentes", "Pérdida de memoria",
                "Temblores", "Problemas de visión", "Debilidad muscular"
            ],
            'TRAU': [
                "Dolor en articulaciones", "Hinchazón después de caída", "Limitación de movimiento",
                "Dolor lumbar", "Esguince de tobillo", "Fractura sospechada"
            ]
        }

        # Diagnósticos comunes
        diagnosticos = [
            "Hipertensión arterial controlada",
            "Infección respiratoria alta",
            "Lumbalgia mecánica",
            "Síndrome metabólico",
            "Ansiedad generalizada",
            "Diabetes tipo 2 compensada",
            "Artrosis de rodilla",
            "Reflujo gastroesofágico",
            "Migraña crónica",
            "Dermatitis atópica"
        ]

        # Tratamientos comunes
        tratamientos = [
            "Reposo y analgésicos. Control en 1 semana.",
            "Antibiótico por 7 días. Volver si no mejora.",
            "Terapia física 2 veces por semana durante 1 mes.",
            "Medicamento diario. Control mensual.",
            "Cambios en estilo de vida y dieta. Seguimiento en 3 meses.",
            "Cirugía programada. Preparación preoperatoria.",
            "Medicamento tópico. Aplicar 2 veces al día.",
            "Ejercicios de rehabilitación en casa.",
            "Control estricto de signos vitales.",
            "Derivación a especialista para evaluación."
        ]

        consultas_creadas = 0

        for cita in citas_realizadas:
            # Obtener especialidad del médico
            especialidades_medico = cita.medico.especialidades.all()
            if especialidades_medico.exists():
                especialidad_principal = especialidades_medico.first()
                
                # Obtener síntomas según especialidad
                sintomas_especialidad = sintomas_por_especialidad.get(
                    especialidad_principal.codigo, 
                    ["Malestar general", "Dolor", "Fiebre"]
                )
                
                # Crear consulta médica
                historia_clinica = HistoriaClinica.objects.get(paciente=cita.paciente)
                
                Consulta.objects.create(
                    historia_clinica=historia_clinica,
                    medico=cita.medico,
                    fecha_consulta=cita.fecha_cita,
                    motivo_consulta=cita.motivo,
                    sintomas=', '.join(random.sample(sintomas_especialidad, k=random.randint(1, 3))),
                    diagnostico=random.choice(diagnosticos),
                    tratamiento=random.choice(tratamientos),
                    observaciones=fake.paragraph() if random.random() > 0.3 else None
                )
                consultas_creadas += 1

        self.stdout.write(f"Consultas médicas creadas: {consultas_creadas}")

    def crear_registros_backup(self):
        """Crear registros de backup de ejemplo"""
        administradores = Administrador.objects.all()
        
        if not administradores.exists():
            self.stdout.write(self.style.WARNING("No hay administradores para crear backups"))
            return

        admin = administradores.first()
        
        backups_data = [
            {
                'nombre_archivo': 'backup_completo_20240115_143000.sql',
                'tamano_bytes': 524288000,  # 500 MB
                'tipo_backup': 'Completo',
                'estado': 'Exitoso',
                'ubicacion_almacenamiento': '/backups/automaticos/',
                'notas': 'Backup automático nocturno. Todos los sistemas operativos correctamente.'
            },
            {
                'nombre_archivo': 'backup_incremental_20240116_020000.sql',
                'tamano_bytes': 104857600,  # 100 MB
                'tipo_backup': 'Incremental',
                'estado': 'Exitoso',
                'ubicacion_almacenamiento': '/backups/incremental/',
                'notas': 'Backup incremental. Solo cambios desde el último backup completo.'
            }
        ]

        for backup_data in backups_data:
            # Fecha de backup en el pasado
            fecha_backup = timezone.now() - timedelta(days=random.randint(1, 30))
            
            RegistroBackup.objects.create(
                nombre_archivo=backup_data['nombre_archivo'],
                tamano_bytes=backup_data['tamano_bytes'],
                fecha_backup=fecha_backup,
                usuario_responsable=admin.usuario,
                tipo_backup=backup_data['tipo_backup'],
                estado=backup_data['estado'],
                ubicacion_almacenamiento=backup_data['ubicacion_almacenamiento'],
                notas=backup_data['notas']
            )

        self.stdout.write(f"Registros de backup creados: {RegistroBackup.objects.count()}")

    def crear_bitacora(self):
        """Crear registros de bitácora del sistema"""
        usuarios = Usuario.objects.all()[:5]  # Tomar algunos usuarios
        
        if not usuarios.exists():
            self.stdout.write(self.style.WARNING("No hay usuarios para crear bitácora"))
            return

        acciones_comunes = [
            "Inicio de sesión exitoso",
            "Cierre de sesión",
            "Creación de nuevo usuario",
            "Actualización de perfil médico",
            "Registro de nueva consulta médica",
            "Solicitud de cita médica",
            "Cancelación de cita",
            "Exportación de reporte de pacientes",
            "Modificación de horario médico",
            "Acceso a historia clínica",
            "Actualización de datos personales",
            "Configuración del sistema"
        ]

        modulos = [
            "Autenticación",
            "Usuarios", 
            "Médicos",
            "Pacientes",
            "Agenda",
            "Historias Clínicas",
            "Consultas",
            "Reportes",
            "Configuración"
        ]

        bitacora_creada = 0

        for i in range(12):  # Crear 12 registros como solicitaste
            usuario = random.choice(list(usuarios))
            fecha_hora = timezone.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            Bitacora.objects.create(
                usuario=usuario,
                ip_address=fake.ipv4(),
                accion_realizada=random.choice(acciones_comunes),
                modulo_afectado=random.choice(modulos),
                fecha_hora=fecha_hora,
                detalles=fake.sentence() if random.random() > 0.4 else None
            )
            bitacora_creada += 1

        self.stdout.write(f"Registros de bitácora creados: {bitacora_creada}")