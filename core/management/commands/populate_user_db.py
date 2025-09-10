import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.utils import timezone
from datetime import datetime
from core.models import *

fake = Faker('es_ES')

class Command(BaseCommand):
    help = 'Pobla la base de datos con usuarios, roles y perfiles'

    def handle(self, *args, **kwargs):
        self.stdout.write("Poblando base de datos...")

        self.crear_roles()
        self.crear_administradores()
        self.crear_especialidades()
        self.crear_medicos()
        self.crear_pacientes()

        self.stdout.write(self.style.SUCCESS("¡Datos generados exitosamente!"))

    def crear_roles(self):
        roles = ['Administrador', 'Medico', 'Paciente']
        for nombre in roles:
            Rol.objects.get_or_create(nombre_rol=nombre)
        self.stdout.write(f"Roles creados: {Rol.objects.count()}")

    def crear_administradores(self):
        rol_admin = Rol.objects.get(nombre_rol='Administrador')

        for i in range(1, 4):
            email = f"admin{i}@salud.com"
            if not Usuario.objects.filter(email=email).exists():
                usuario = Usuario(
                    email=email,
                    nombre=fake.first_name(),
                    apellido=fake.last_name(),
                    id_rol=rol_admin,
                    is_staff=True,
                    is_active=True
                )
                usuario.set_password("admin12345")
                usuario.save()
                Administrador.objects.create(usuario=usuario)
        self.stdout.write(f"Administradores creados: {Administrador.objects.count()}")
    
    def crear_especialidades(self):
        especialidades_base = [
            ('CARD', 'Cardiología'),
            ('DERM', 'Dermatología'),
            ('PED', 'Pediatría'),
            ('NEUR', 'Neurología'),
            ('TRAU', 'Traumatología'),
            ('PSIQ', 'Psiquiatría'),
        ]

        for codigo, nombre in especialidades_base:
            Especialidad.objects.get_or_create(
                codigo=codigo,
                nombre=nombre,
                defaults={'descripcion': fake.sentence()}
            )

        self.stdout.write(f"Especialidades creadas: {Especialidad.objects.count()}")

    def crear_medicos(self):
        rol_medico = Rol.objects.get(nombre_rol='Medico')
        especialidades = list(Especialidad.objects.all())

        for i in range(1, 11):
            email = f"medico{i}@salud.com"
            if not Usuario.objects.filter(email=email).exists():
                usuario = Usuario(
                    email=email,
                    nombre=fake.first_name(),
                    apellido=fake.last_name(),
                    id_rol=rol_medico,
                    is_staff=True,
                    is_active=True
                )
                usuario.set_password("medico123")
                usuario.save()

                medico = Medico.objects.create(
                    usuario=usuario,
                    numero_licencia=f"M-{1000 + i}",
                    estado=random.choice(['Activo', 'Inactivo', 'Vacaciones']),
                    firma_digital=fake.text()
                )

                # Asignar entre 1 y 3 especialidades aleatorias
                especialidades_random = random.sample(especialidades, k=random.randint(1, 3))
                for especialidad in especialidades_random:
                    MedicoEspecialidad.objects.create(medico=medico, especialidad=especialidad)

        self.stdout.write(f"Médicos creados: {Medico.objects.count()}")

    def crear_pacientes(self):
        rol_paciente = Rol.objects.get(nombre_rol='Paciente')

        enfermedades_cronicas = [
            "Diabetes tipo 2", "Hipertensión", "Asma", "Epilepsia",
            "Enfermedad celíaca", "Artritis reumatoide", "Parkinson",
            "Esclerosis múltiple", "Colesterol alto", "Migraña crónica"
        ]

        alergias = [
            "Penicilina", "Lactosa", "Frutos secos", "Polen", "Mariscos",
            "Ácaros", "Gluten", "Pelo de gato", "Latex"
        ]

        medicamentos = [
            "Paracetamol", "Ibuprofeno", "Metformina", "Amlodipino",
            "Losartán", "Omeprazol", "Insulina", "Levotiroxina", "Atorvastatina"
        ]

        parentescos = ['Padre', 'Madre', 'Hermano', 'Pareja', 'Tío', 'Amigo']
        tipos_sangre = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
        generos = ['M', 'F']

        for _ in range(50):
            email = fake.unique.email()
            if not Usuario.objects.filter(email=email).exists():
                nombre = fake.first_name()
                apellido = fake.last_name()
                genero = random.choice(generos)

                fecha_nacimiento = fake.date_of_birth(minimum_age=18, maximum_age=90)
                direccion = fake.address()
                telefono = fake.phone_number()

                usuario = Usuario(
                    email=email,
                    nombre=nombre,
                    apellido=apellido,
                    genero=genero,
                    fecha_nacimiento=fecha_nacimiento,
                    direccion=direccion,
                    telefono=telefono,
                    id_rol=rol_paciente,
                    is_active=True
                )
                usuario.set_password("paciente123")
                usuario.save()

                Paciente.objects.create(
                    usuario=usuario,
                    tipo_sangre=random.choice(tipos_sangre),
                    alergias=', '.join(random.sample(alergias, k=random.randint(0, 3))),
                    enfermedades_cronicas=', '.join(random.sample(enfermedades_cronicas, k=random.randint(0, 2))),
                    medicamentos_actuales=', '.join(random.sample(medicamentos, k=random.randint(0, 2))),
                    contacto_emergencia_nombre=fake.name(),
                    contacto_emergencia_telefono=fake.phone_number(),
                    contacto_emergencia_parentesco=random.choice(parentescos),
                    estado='Activo'
                )
        self.stdout.write(f"Pacientes creados: {Paciente.objects.count()}")