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

    def crear_medicos(self):
        rol_medico = Rol.objects.get(nombre_rol='Medico')

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
                Medico.objects.create(
                    usuario=usuario,
                    numero_licencia=f"M-{1000 + i}",
                    estado=random.choice(['Activo', 'Inactivo', 'Vacaciones']),
                    firma_digital=fake.text()
                )
        self.stdout.write(f"Médicos creados: {Medico.objects.count()}")

    def crear_pacientes(self):
        rol_paciente = Rol.objects.get(nombre_rol='Paciente')

        for i in range(1, 51):  # Puedes cambiar a 100 si deseas
            email = fake.unique.email()
            if not Usuario.objects.filter(email=email).exists():
                usuario = Usuario(
                    email=email,
                    nombre=fake.first_name(),
                    apellido=fake.last_name(),
                    id_rol=rol_paciente,
                    is_active=True
                )
                usuario.set_password("paciente123")
                usuario.save()
                Paciente.objects.create(
                    usuario=usuario,
                    tipo_sangre=random.choice(['A+', 'B-', 'O+', 'AB-']),
                    alergias=fake.word(),
                    enfermedades_cronicas=fake.word(),
                    medicamentos_actuales=fake.word(),
                    contacto_emergencia_nombre=fake.name(),
                    contacto_emergencia_telefono=fake.phone_number(),
                    contacto_emergencia_parentesco=random.choice(['Padre', 'Madre', 'Hermano', 'Pareja']),
                    estado='Activo'
                )
        self.stdout.write(f"Pacientes creados: {Paciente.objects.count()}")