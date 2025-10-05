import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.utils import timezone
from datetime import datetime, time
from core.models import *

fake = Faker('es_ES')

class Command(BaseCommand):
    help = 'Pobla la base de datos con usuarios, roles y perfiles'

    def handle(self, *args, **kwargs):
        self.stdout.write("Poblando base de datos...")

        self.crear_roles()
        self.crear_permisos_basicos()
        self.crear_administradores()
        self.crear_especialidades()
        self.crear_medicos()
        self.crear_pacientes()

        self.stdout.write(self.style.SUCCESS("¡Datos generados exitosamente!"))

    def crear_roles(self):
        roles = [
            ('Administrador', 'Acceso completo al sistema'),
            ('Medico', 'Personal médico con acceso a historias clínicas'),
            ('Paciente', 'Pacientes del sistema')
        ]
        
        for nombre, descripcion in roles:
            Rol.objects.get_or_create(
                nombre_rol=nombre,
                defaults={'descripcion': descripcion}
            )
        self.stdout.write(f"Roles creados: {Rol.objects.count()}")

    def crear_permisos_basicos(self):
        permisos_base = [
            # Permisos de administración
            ('admin_full', 'Acceso completo administrativo', 'Administración'),
            ('ver_usuarios', 'Ver lista de usuarios', 'Usuarios'),
            ('crear_usuarios', 'Crear nuevos usuarios', 'Usuarios'),
            ('editar_usuarios', 'Editar usuarios existentes', 'Usuarios'),
            ('eliminar_usuarios', 'Eliminar usuarios', 'Usuarios'),
            
            # Permisos médicos
            ('ver_pacientes', 'Ver lista de pacientes', 'Pacientes'),
            ('ver_historias', 'Ver historias clínicas', 'Historias'),
            ('editar_historias', 'Editar historias clínicas', 'Historias'),
            ('crear_consultas', 'Crear nuevas consultas', 'Consultas'),
            ('ver_agenda', 'Ver agenda de citas', 'Agenda'),
            ('gestionar_citas', 'Gestionar citas médicas', 'Agenda'),
            
            # Permisos pacientes
            ('ver_mi_historia', 'Ver propia historia clínica', 'Pacientes'),
            ('solicitar_citas', 'Solicitar citas médicas', 'Agenda'),
            ('ver_mis_citas', 'Ver citas propias', 'Agenda'),
        ]

        for codigo, nombre, modulo in permisos_base:
            Permiso.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'descripcion': f'Permiso para {nombre.lower()}'
                }
            )
        self.stdout.write(f"Permisos básicos creados: {Permiso.objects.count()}")

    def crear_administradores(self):
        rol_admin = Rol.objects.get(nombre_rol='Administrador')
        permisos_admin = Permiso.objects.all()

        administradores_data = [
            {
                'email': 'admin@salud.com',
                'nombre': 'Carlos',
                'apellido': 'Rodríguez',
                'telefono': '+34 912 345 678'
            },
            {
                'email': 'soporte@salud.com', 
                'nombre': 'Ana',
                'apellido': 'Martínez',
                'telefono': '+34 913 456 789'
            },
            {
                'email': 'sistema@salud.com',
                'nombre': 'David',
                'apellido': 'García',
                'telefono': '+34 914 567 890'
            }
        ]

        for i, admin_data in enumerate(administradores_data, 1):
            email = admin_data['email']
            if not Usuario.objects.filter(email=email).exists():
                usuario = Usuario(
                    email=email,
                    nombre=admin_data['nombre'],
                    apellido=admin_data['apellido'],
                    telefono=admin_data['telefono'],
                    id_rol=rol_admin,
                    is_staff=True,
                    is_superuser=True,
                    is_active=True
                )
                usuario.set_password("admin123")
                usuario.save()
                
                # Asignar todos los permisos al rol administrador
                rol_admin.permisos.set(permisos_admin)
                
                Administrador.objects.create(usuario=usuario)
                
        self.stdout.write(f"Administradores creados: {Administrador.objects.count()}")
    
    def crear_especialidades(self):
        especialidades_base = [
            ('CARD', 'Cardiología', 'Especialidad en enfermedades del corazón y sistema circulatorio'),
            ('DERM', 'Dermatología', 'Especialidad en enfermedades de la piel, pelo y uñas'),
            ('PED', 'Pediatría', 'Atención médica para niños y adolescentes'),
            ('NEUR', 'Neurología', 'Especialidad en enfermedades del sistema nervioso'),
            ('TRAU', 'Traumatología', 'Especialidad en lesiones óseas y musculares'),
            ('PSIQ', 'Psiquiatría', 'Diagnóstico y tratamiento de trastornos mentales'),
            ('GINE', 'Ginecología', 'Salud femenina y sistema reproductivo'),
            ('OFTA', 'Oftalmología', 'Enfermedades de los ojos y visión'),
            ('ORTO', 'Ortopedia', 'Corrección de deformidades óseas'),
            ('UROL', 'Urología', 'Sistema urinario y reproductor masculino'),
            ('ENDO', 'Endocrinología', 'Trastornos hormonales y metabólicos'),
            ('GAST', 'Gastroenterología', 'Enfermedades del sistema digestivo'),
        ]

        for codigo, nombre, descripcion in especialidades_base:
            Especialidad.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'descripcion': descripcion
                }
            )

        self.stdout.write(f"Especialidades creadas: {Especialidad.objects.count()}")

    def crear_medicos(self):
        rol_medico = Rol.objects.get(nombre_rol='Medico')
        especialidades = list(Especialidad.objects.all())
        
        # Permisos básicos para médicos
        permisos_medico = Permiso.objects.filter(
            codigo__in=['ver_pacientes', 'ver_historias', 'editar_historias', 'crear_consultas', 'ver_agenda', 'gestionar_citas']
        )
        rol_medico.permisos.set(permisos_medico)

        medicos_data = [
            {
                'email': 'dr.garcia@salud.com',
                'nombre': 'Luis',
                'apellido': 'García',
                'especialidades': ['CARD', 'NEUR']
            },
            {
                'email': 'dra.martinez@salud.com',
                'nombre': 'Elena', 
                'apellido': 'Martínez',
                'especialidades': ['PED', 'GINE']
            },
            {
                'email': 'dr.rodriguez@salud.com',
                'nombre': 'Javier',
                'apellido': 'Rodríguez', 
                'especialidades': ['TRAU', 'ORTO']
            },
            {
                'email': 'dra.lopez@salud.com',
                'nombre': 'Carmen',
                'apellido': 'López',
                'especialidades': ['DERM']
            },
            {
                'email': 'dr.hernandez@salud.com',
                'nombre': 'Miguel',
                'apellido': 'Hernández',
                'especialidades': ['PSIQ', 'NEUR']
            },
            {
                'email': 'dra.gomez@salud.com',
                'nombre': 'Sofia',
                'apellido': 'Gómez',
                'especialidades': ['OFTA']
            },
            {
                'email': 'dr.diaz@salud.com', 
                'nombre': 'Roberto',
                'apellido': 'Díaz',
                'especialidades': ['UROL']
            },
            {
                'email': 'dra.fernandez@salud.com',
                'nombre': 'Isabel',
                'apellido': 'Fernández',
                'especialidades': ['ENDO', 'GAST']
            }
        ]

        for i, medico_data in enumerate(medicos_data, 1):
            email = medico_data['email']
            if not Usuario.objects.filter(email=email).exists():
                usuario = Usuario(
                    email=email,
                    nombre=medico_data['nombre'],
                    apellido=medico_data['apellido'],
                    telefono=fake.phone_number(),
                    id_rol=rol_medico,
                    is_staff=True,
                    is_active=True
                )
                usuario.set_password("medico123")
                usuario.save()

                medico = Medico.objects.create(
                    usuario=usuario,
                    numero_licencia=f"M-{2023000 + i}",
                    estado='Activo',
                    firma_digital=f"Firma digital del Dr. {medico_data['nombre']} {medico_data['apellido']}"
                )

                # Asignar especialidades específicas
                for codigo_especialidad in medico_data['especialidades']:
                    especialidad = Especialidad.objects.get(codigo=codigo_especialidad)
                    MedicoEspecialidad.objects.create(medico=medico, especialidad=especialidad)

        self.stdout.write(f"Médicos creados: {Medico.objects.count()}")

    def crear_pacientes(self):
        rol_paciente = Rol.objects.get(nombre_rol='Paciente')
        
        # Permisos básicos para pacientes
        permisos_paciente = Permiso.objects.filter(
            codigo__in=['ver_mi_historia', 'solicitar_citas', 'ver_mis_citas']
        )
        rol_paciente.permisos.set(permisos_paciente)

        enfermedades_cronicas = [
            "Diabetes tipo 2", "Hipertensión arterial", "Asma bronquial", "Epilepsia",
            "Enfermedad celíaca", "Artritis reumatoide", "Enfermedad de Parkinson",
            "Esclerosis múltiple", "Hipercolesterolemia", "Migraña crónica",
            "Enfermedad pulmonar obstructiva crónica", "Insuficiencia cardíaca",
            "Hipotiroidismo", "Enfermedad de Crohn", "Lupus eritematoso"
        ]

        alergias = [
            "Penicilina", "Lactosa", "Frutos secos", "Polen", "Mariscos",
            "Ácaros del polvo", "Gluten", "Pelo de gato", "Latex", "Huevo",
            "Soja", "Aspirina", "Yodo", "Anestésicos locales"
        ]

        medicamentos = [
            "Paracetamol 500mg", "Ibuprofeno 600mg", "Metformina 850mg", "Amlodipino 5mg",
            "Losartán 50mg", "Omeprazol 20mg", "Insulina glargina", "Levotiroxina 50mcg",
            "Atorvastatina 20mg", "Salbutamol inhalador", "Warfarina 5mg", "Metoprolol 50mg"
        ]

        parentescos = ['Padre', 'Madre', 'Hermano', 'Hermana', 'Pareja', 'Hijo', 'Hija']
        tipos_sangre = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
        generos = ['M', 'F']

        # Crear pacientes con datos más realistas
        pacientes_data = [
            {
                'nombre': 'María', 'apellido': 'González', 'email': 'maria.gonzalez@email.com',
                'edad': 45, 'genero': 'F'
            },
            {
                'nombre': 'Carlos', 'apellido': 'López', 'email': 'carlos.lopez@email.com', 
                'edad': 62, 'genero': 'M'
            },
            {
                'nombre': 'Ana', 'apellido': 'Rodríguez', 'email': 'ana.rodriguez@email.com',
                'edad': 28, 'genero': 'F'
            },
            {
                'nombre': 'Javier', 'apellido': 'Martínez', 'email': 'javier.martinez@email.com',
                'edad': 35, 'genero': 'M'
            },
            {
                'nombre': 'Laura', 'apellido': 'Sánchez', 'email': 'laura.sanchez@email.com',
                'edad': 51, 'genero': 'F'
            },
            {
                'nombre': 'Diego', 'apellido': 'Pérez', 'email': 'diego.perez@email.com',
                'edad': 67, 'genero': 'M'
            },
            {
                'nombre': 'Elena', 'apellido': 'Fernández', 'email': 'elena.fernandez@email.com',
                'edad': 39, 'genero': 'F'
            },
            {
                'nombre': 'Roberto', 'apellido': 'Gómez', 'email': 'roberto.gomez@email.com',
                'edad': 42, 'genero': 'M'
            }
        ]

        for paciente_data in pacientes_data:
            if not Usuario.objects.filter(email=paciente_data['email']).exists():
                usuario = Usuario(
                    email=paciente_data['email'],
                    nombre=paciente_data['nombre'],
                    apellido=paciente_data['apellido'],
                    genero=paciente_data['genero'],
                    fecha_nacimiento=fake.date_of_birth(minimum_age=paciente_data['edad'], maximum_age=paciente_data['edad']),
                    direccion=fake.address(),
                    telefono=fake.phone_number(),
                    id_rol=rol_paciente,
                    is_active=True
                )
                usuario.set_password("paciente123")
                usuario.save()

                # Datos médicos realistas según edad y género
                enfermedades = random.sample(enfermedades_cronicas, k=random.randint(0, 2))
                alergias_pac = random.sample(alergias, k=random.randint(0, 2))
                medicamentos_pac = random.sample(medicamentos, k=random.randint(0, 3))

                Paciente.objects.create(
                    usuario=usuario,
                    tipo_sangre=random.choice(tipos_sangre),
                    alergias=', '.join(alergias_pac) if alergias_pac else 'Ninguna conocida',
                    enfermedades_cronicas=', '.join(enfermedades) if enfermedades else 'Ninguna',
                    medicamentos_actuales=', '.join(medicamentos_pac) if medicamentos_pac else 'Ninguno',
                    contacto_emergencia_nombre=fake.name(),
                    contacto_emergencia_telefono=fake.phone_number(),
                    contacto_emergencia_parentesco=random.choice(parentescos),
                    estado='Activo'
                )

        self.stdout.write(f"Pacientes creados: {Paciente.objects.count()}")