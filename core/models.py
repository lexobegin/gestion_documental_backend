from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class ClienteSuscriptor(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Permiso(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

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

    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    objects = UsuarioManager()

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.nombre} {self.apellido}"
    
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

    def tiene_permiso_componente(self, codigo_componente, accion='ver'):
        """
        Verifica si el usuario tiene permiso para un componente específico
        """
        try:
            componente = ComponenteUI.objects.get(codigo_componente=codigo_componente, activo=True)
            permiso_componente = PermisoComponente.objects.filter(
                componente=componente,
                accion_permitida__in=[accion, 'todos'],
                permiso__in=self.permisos
            ).exists()
            return permiso_componente
        except ComponenteUI.DoesNotExist:
            return False

    @property
    def edad(self):
        """Calcula la edad del usuario basado en la fecha de nacimiento"""
        if self.fecha_nacimiento:
            today = timezone.now().date()
            born = self.fecha_nacimiento
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return None

class Rol(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    permisos = models.ManyToManyField(Permiso, related_name='roles', blank=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre_rol
    
class Medico(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True)
    numero_licencia = models.CharField(max_length=50, unique=True)
    firma_digital = models.TextField(blank=True, null=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)
    
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
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Activo')

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido} - Paciente"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del paciente"""
        return self.usuario.nombre_completo
    
    @property
    def email(self):
        """Retorna el email del paciente"""
        return self.usuario.email
    
    @property
    def telefono(self):
        """Retorna el teléfono del paciente"""
        return self.usuario.telefono
    
    @property
    def edad(self):
        """Retorna la edad del paciente"""
        return self.usuario.edad
    
    @property
    def tiene_alergias(self):
        """Indica si el paciente tiene alergias registradas"""
        return bool(self.alergias and self.alergias.strip())
    
    @property
    def tiene_enfermedades_cronicas(self):
        """Indica si el paciente tiene enfermedades crónicas registradas"""
        return bool(self.enfermedades_cronicas and self.enfermedades_cronicas.strip())
    
    @property
    def tiene_medicamentos_actuales(self):
        """Indica si el paciente tiene medicamentos actuales registrados"""
        return bool(self.medicamentos_actuales and self.medicamentos_actuales.strip())
    
    @property
    def tiene_contacto_emergencia(self):
        """Indica si el paciente tiene contacto de emergencia registrado"""
        return bool(self.contacto_emergencia_nombre and self.contacto_emergencia_telefono)
    
    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['tipo_sangre']),
        ]

class Administrador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)
    def __str__(self):
        return f"Administrador: {self.usuario.nombre} {self.usuario.apellido}"

class Especialidad(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class MedicoEspecialidad(models.Model):
    id = models.AutoField(primary_key=True)
    medico = models.ForeignKey('Medico', on_delete=models.CASCADE)
    especialidad = models.ForeignKey('Especialidad', on_delete=models.CASCADE)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('medico', 'especialidad')
        db_table = 'medico_especialidad'

    def __str__(self):
        return f"{self.medico} - {self.especialidad}"

# NUEVOS MODELOS PARA SPRINT 2

class TipoComponente(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

class ComponenteUI(models.Model):
    tipo_componente = models.ForeignKey(TipoComponente, on_delete=models.CASCADE)
    codigo_componente = models.CharField(max_length=100, unique=True)
    nombre_componente = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    modulo = models.CharField(max_length=50)
    ruta = models.CharField(max_length=200, blank=True, null=True)  # Para menús
    icono = models.CharField(max_length=100, blank=True, null=True)
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre_componente} ({self.codigo_componente})"

    class Meta:
        verbose_name = "Componente UI"
        verbose_name_plural = "Componentes UI"

class PermisoComponente(models.Model):
    ACCIONES_PERMITIDAS = [
        ('ver', 'Ver'),
        ('crear', 'Crear'),
        ('editar', 'Editar'),
        ('eliminar', 'Eliminar'),
        ('exportar', 'Exportar'),
        ('todos', 'Todos'),
    ]
    
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)
    componente = models.ForeignKey(ComponenteUI, on_delete=models.CASCADE)
    accion_permitida = models.CharField(max_length=10, choices=ACCIONES_PERMITIDAS)
    condiciones = models.TextField(blank=True, null=True)  # JSON field para condiciones
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('permiso', 'componente', 'accion_permitida')
        verbose_name = "Permiso Componente"
        verbose_name_plural = "Permisos Componentes"

    def __str__(self):
        return f"{self.permiso} - {self.componente} - {self.accion_permitida}"

class Bitacora(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    accion_realizada = models.CharField(max_length=200)
    modulo_afectado = models.CharField(max_length=50)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    detalles = models.TextField(blank=True, null=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.usuario.email} - {self.accion_realizada} - {self.fecha_hora}"

    class Meta:
        verbose_name = "Bitácora"
        verbose_name_plural = "Bitácoras"

    @classmethod
    def registrar_accion(cls, usuario, request, accion, modulo, cliente, detalles=None):
        """
        Método helper para registrar acciones en la bitácora
        """
        ip_address = None
        if request:
            # Obtener IP del cliente
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        return cls.objects.create(
            usuario=usuario,
            ip_address=ip_address,
            accion_realizada=accion,
            modulo_afectado=modulo,
            detalles=detalles,
            cliente=cliente
        )

class HorarioMedico(models.Model):
    DIA_SEMANA_CHOICES = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]
    
    medico_especialidad = models.ForeignKey(MedicoEspecialidad, on_delete=models.CASCADE)
    dia_semana = models.CharField(max_length=10, choices=DIA_SEMANA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('medico_especialidad', 'dia_semana', 'hora_inicio', 'hora_fin')
        verbose_name = "Horario Médico"
        verbose_name_plural = "Horarios Médicos"

    def __str__(self):
        return f"{self.medico_especialidad.medico} - {self.medico_especialidad.especialidad} - {self.dia_semana} {self.hora_inicio}-{self.hora_fin}"

class AgendaCita(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('realizada', 'Realizada'),
    ]
    
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    medico_especialidad = models.ForeignKey(MedicoEspecialidad, on_delete=models.CASCADE)  # NUEVA RELACIÓN
    fecha_cita = models.DateField()
    hora_cita = models.TimeField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    motivo = models.TextField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    def __str__(self):
        medico_esp = self.medico_especialidad
        return f"Cita {self.paciente} con {medico_esp.medico} - {medico_esp.especialidad} - {self.fecha_cita} {self.hora_cita}"

    class Meta:
        verbose_name = "Agenda Cita"
        verbose_name_plural = "Agenda Citas"

class HistoriaClinica(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    observaciones_generales = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['paciente', 'activo'],
                condition=models.Q(activo=True),
                name='unique_paciente_activo'
            )
        ]
        verbose_name = "Historia Clínica"
        verbose_name_plural = "Historias Clínicas"

    def __str__(self):
        return f"Historia Clínica - {self.paciente}"

class Consulta(models.Model):
    historia_clinica = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    motivo_consulta = models.TextField()
    sintomas = models.TextField(blank=True, null=True)
    diagnostico = models.TextField(blank=True, null=True)
    tratamiento = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"Consulta {self.historia_clinica.paciente} - {self.fecha_consulta}"

    class Meta:
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"

class RegistroBackup(models.Model):
    TIPO_BACKUP_CHOICES = [
        ('Completo', 'Completo'),
        ('Incremental', 'Incremental'),
        ('Diferencial', 'Diferencial'),
    ]
    
    ESTADO_CHOICES = [
        ('Exitoso', 'Exitoso'),
        ('Fallido', 'Fallido'),
        ('En Progreso', 'En Progreso'),
    ]
    
    nombre_archivo = models.CharField(max_length=255)
    tamano_bytes = models.BigIntegerField(blank=True, null=True)
    fecha_backup = models.DateTimeField(auto_now_add=True)
    usuario_responsable = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo_backup = models.CharField(max_length=15, choices=TIPO_BACKUP_CHOICES)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES)
    ubicacion_almacenamiento = models.CharField(max_length=500, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    cliente = models.ForeignKey(ClienteSuscriptor, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"Backup {self.nombre_archivo} - {self.fecha_backup}"

    class Meta:
        verbose_name = "Registro Backup"
        verbose_name_plural = "Registros Backup"

# -------------------------------
# EXÁMENES MÉDICOS 
# -------------------------------

class TipoExamen(models.Model):
    URGENCIA_CHOICES = [
        ('Rutina', 'Rutina'),
        ('Urgente', 'Urgente'),
        ('Emergencia', 'Emergencia'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    indicaciones = models.TextField(blank=True, null=True)
    urgencia_default = models.CharField(max_length=15, choices=URGENCIA_CHOICES, default='Rutina')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class SolicitudExamen(models.Model):
    ESTADO_CHOICES = [
        ('solicitado', 'Solicitado'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    URGENCIA_CHOICES = [
        ('Rutina', 'Rutina'),
        ('Urgente', 'Urgente'),
        ('Emergencia', 'Emergencia'),
    ]
    
    # Relaciones
    consulta = models.ForeignKey('Consulta', on_delete=models.CASCADE, related_name='solicitudes_examen')
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE)
    medico = models.ForeignKey('Medico', on_delete=models.CASCADE)
    tipo_examen = models.ForeignKey('TipoExamen', on_delete=models.CASCADE)
    
    # Campos principales
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    urgencia = models.CharField(max_length=15, choices=URGENCIA_CHOICES)
    indicaciones_especificas = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='solicitado')
    
    # Resultados
    resultados = models.TextField(blank=True, null=True)
    fecha_resultado = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Solicitud de Examen"
        verbose_name_plural = "Solicitudes de Exámenes"

    def __str__(self):
        return f"Examen {self.tipo_examen.nombre} - {self.paciente}"        

#-----------------Prueba-------
class Auto(models.Model):
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    anio = models.PositiveIntegerField()
    color = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.anio})"