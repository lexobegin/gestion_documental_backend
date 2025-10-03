from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Permiso(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        from .models import Rol
        rol_admin, created = Rol.objects.get_or_create(
            nombre_rol='Administrador',
            defaults={'descripcion': 'Rol administrativo'}
        )
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('id_rol', rol_admin)  # Asignar rol automáticamente

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    GENERO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino')]

    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True, null=True)
    activo = models.BooleanField(default=True)

    id_rol = models.ForeignKey('Rol', on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    #REQUIRED_FIELDS = ['nombre', 'apellido', 'id_rol']
    REQUIRED_FIELDS = ['nombre']

    objects = UsuarioManager()

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"
    
    @property
    def tipo_usuario(self):
        if hasattr(self, 'medico'):
            return 'Medico'
        elif hasattr(self, 'paciente'):
            return 'Paciente'
        elif hasattr(self, 'administrador'):
            return 'Administrador'
        return 'Desconocido'

    @property
    def permisos(self):
        """Retorna los permisos del rol asignado al usuario"""
        if self.id_rol:
            return self.id_rol.permisos.all()
        return Permiso.objects.none()


class Rol(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    permisos = models.ManyToManyField(Permiso, related_name='roles', blank=True)

    def __str__(self):
        return self.nombre_rol
    
class Medico(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True)
    numero_licencia = models.CharField(max_length=50, unique=True)
    firma_digital = models.TextField(blank=True, null=True)
    
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('Vacaciones', 'Vacaciones'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Activo')

    especialidades = models.ManyToManyField(
        'Especialidad',
        through='MedicoEspecialidad',
        related_name='medicos'
    )

    def __str__(self):
        return f"Dr. {self.usuario.nombre} {self.usuario.apellido} ({self.numero_licencia})"
    
class Paciente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True)
    tipo_sangre = models.CharField(max_length=5, blank=True, null=True)
    alergias = models.TextField(blank=True, null=True)
    enfermedades_cronicas = models.TextField(blank=True, null=True)
    medicamentos_actuales = models.TextField(blank=True, null=True)
    
    contacto_emergencia_nombre = models.CharField(max_length=200, blank=True, null=True)
    contacto_emergencia_telefono = models.CharField(max_length=20, blank=True, null=True)
    contacto_emergencia_parentesco = models.CharField(max_length=50, blank=True, null=True)

    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Activo')

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido} - Paciente"
    
class Administrador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return f"Administrador: {self.usuario.nombre} {self.usuario.apellido}"

#-----------------Prueba-------
class Auto(models.Model):
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    anio = models.PositiveIntegerField()
    color = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.anio})"

class Especialidad(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class MedicoEspecialidad(models.Model):
    medico = models.ForeignKey('Medico', on_delete=models.CASCADE)
    especialidad = models.ForeignKey('Especialidad', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('medico', 'especialidad')
        db_table = 'medico_especialidad'

    def __str__(self):
        return f"{self.medico} - {self.especialidad}"