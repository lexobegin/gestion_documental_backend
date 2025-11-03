from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import time
from django.utils import timezone

from .models import *

# TOKEN
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar datos del usuario al response del token
        user = self.user
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'nombre': user.nombre,
            'apellido': user.apellido,
            'tipo_usuario': user.tipo_usuario,
            'rol': RolSerializer(user.id_rol).data if user.id_rol else None
        }
        return data

class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = ['id', 'nombre', 'codigo', 'descripcion']

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre_rol', 'descripcion']

class UsuarioSerializer(serializers.ModelSerializer):
    # Lectura: objeto rol anidado (como "detalle")
    rol = RolSerializer(read_only=True, source='id_rol')
    # Escritura: id del rol (FK)
    id_rol = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        write_only=True
    )
    # Escritura: password segura
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'password', 'nombre', 'apellido', 'telefono', 'direccion',
            'fecha_nacimiento', 'genero', 'activo', 'rol', 'id_rol'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'nombre': {'required': True},
            'apellido': {'required': True},
        }

    def create(self, validated_data):
        rol = validated_data.pop('id_rol')
        password = validated_data.pop('password')
        user = Usuario(**validated_data, id_rol=rol)
        user.set_password(password)  # <- diferencia vs Auto
        user.save()
        return user

    def update(self, instance, validated_data):
        rol = validated_data.pop('id_rol', None)
        password = validated_data.pop('password', None)
        # comportamiento tipo Auto: asignar campos simples
        for k, v in validated_data.items():
            setattr(instance, k, v)
        # extras de Usuario:
        if rol:
            instance.id_rol = rol
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class UsuarioSelectSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para selects
    """
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre', 'apellido', 'nombre_completo']

    def get_nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"

class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ['id', 'codigo', 'nombre', 'descripcion']

class MedicoEspecialidadSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.CharField(source='medico.usuario.nombre_completo', read_only=True)
    especialidad_nombre = serializers.CharField(source='especialidad.nombre', read_only=True)

    class Meta:
        model = MedicoEspecialidad
        fields = ['id', 'medico', 'medico_nombre', 'especialidad', 'especialidad_nombre']

class MedicoEspecialidadSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para select de MedicoEspecialidad
    """
    medico_nombre_completo = serializers.SerializerMethodField()
    especialidad_nombre = serializers.CharField(source='especialidad.nombre', read_only=True)
    especialidad_codigo = serializers.CharField(source='especialidad.codigo', read_only=True)

    class Meta:
        model = MedicoEspecialidad
        fields = [
            'id', 
            'medico', 
            'medico_nombre_completo',
            'especialidad', 
            'especialidad_nombre',
            'especialidad_codigo'
        ]

    def get_medico_nombre_completo(self, obj):
        return f"Dr. {obj.medico.usuario.nombre} {obj.medico.usuario.apellido}"

class MedicoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    especialidades = EspecialidadSerializer(many=True, read_only=True)

    class Meta:
        model = Medico
        fields = ['usuario', 'numero_licencia', 'firma_digital', 'estado', 'especialidades']
    
    def get_especialidades(self, obj):
        relaciones = MedicoEspecialidad.objects.filter(medico=obj).select_related('especialidad')
        return MedicoEspecialidadSerializer(relaciones, many=True).data

class MedicoSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para select de médicos
    """
    usuario = UsuarioSelectSerializer(read_only=True)
    nombre_completo = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    especialidades = EspecialidadSerializer(many=True, read_only=True)

    class Meta:
        model = Medico
        fields = ['usuario', 'nombre_completo', 'numero_licencia', 'estado', 'especialidades']

# SERIALIZERS COMPLETOS PARA GESTIÓN DE PACIENTES
class PacienteSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    nombre_completo = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    email = serializers.CharField(source='usuario.email', read_only=True)
    telefono = serializers.CharField(source='usuario.telefono', read_only=True)
    direccion = serializers.CharField(source='usuario.direccion', read_only=True)
    fecha_nacimiento = serializers.DateField(source='usuario.fecha_nacimiento', read_only=True)
    genero = serializers.CharField(source='usuario.genero', read_only=True)
    
    # Campos para escritura
    id_usuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        write_only=True,
        source='usuario',
        required=False
    )

    class Meta:
        model = Paciente
        fields = [
            'usuario', 'id_usuario', 'nombre_completo', 'email', 'telefono', 
            'direccion', 'fecha_nacimiento', 'genero', 'tipo_sangre', 'alergias', 
            'enfermedades_cronicas', 'medicamentos_actuales', 'contacto_emergencia_nombre',
            'contacto_emergencia_telefono', 'contacto_emergencia_parentesco', 'estado'
        ]
        read_only_fields = ['usuario', 'nombre_completo', 'email', 'telefono', 
                           'direccion', 'fecha_nacimiento', 'genero']

    def create(self, validated_data):
        usuario_data = validated_data.pop('usuario', None)
        if usuario_data:
            # Si se proporciona un usuario existente
            paciente = Paciente.objects.create(usuario=usuario_data, **validated_data)
        else:
            # Crear nuevo usuario para el paciente
            rol_paciente = Rol.objects.get(nombre_rol='Paciente')
            usuario = Usuario.objects.create(
                id_rol=rol_paciente,
                **{k: v for k, v in validated_data.items() if hasattr(Usuario, k)}
            )
            paciente = Paciente.objects.create(usuario=usuario, **validated_data)
        return paciente

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', None)
        
        # Actualizar campos del paciente
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar usuario si se proporciona
        if usuario_data:
            usuario = instance.usuario
            for attr, value in usuario_data.items():
                setattr(usuario, attr, value)
            usuario.save()
        
        return instance

class PacienteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para creación de pacientes
    Incluye campos de usuario para crear ambos
    """
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    nombre = serializers.CharField(write_only=True, required=True)
    apellido = serializers.CharField(write_only=True, required=True)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    direccion = serializers.CharField(write_only=True, required=False, allow_blank=True)
    fecha_nacimiento = serializers.DateField(write_only=True, required=False)
    genero = serializers.ChoiceField(
        choices=Usuario.GENERO_CHOICES, 
        write_only=True, 
        required=False
    )

    class Meta:
        model = Paciente
        fields = [
            'email', 'password', 'nombre', 'apellido', 'telefono', 'direccion',
            'fecha_nacimiento', 'genero', 'tipo_sangre', 'alergias', 
            'enfermedades_cronicas', 'medicamentos_actuales', 'contacto_emergencia_nombre',
            'contacto_emergencia_telefono', 'contacto_emergencia_parentesco', 'estado'
        ]

    def create(self, validated_data):
        # Extraer datos de usuario
        usuario_data = {
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'nombre': validated_data.pop('nombre'),
            'apellido': validated_data.pop('apellido'),
            'telefono': validated_data.pop('telefono', ''),
            'direccion': validated_data.pop('direccion', ''),
            'fecha_nacimiento': validated_data.pop('fecha_nacimiento', None),
            'genero': validated_data.pop('genero', ''),
        }
        
        # Crear usuario
        rol_paciente = Rol.objects.get(nombre_rol='Paciente')
        usuario = Usuario.objects.create_user(
            id_rol=rol_paciente,
            **usuario_data
        )
        
        # Crear paciente
        paciente = Paciente.objects.create(usuario=usuario, **validated_data)
        return paciente

class PacienteUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para actualización de pacientes
    Permite actualizar tanto datos del paciente como del usuario
    """
    nombre = serializers.CharField(source='usuario.nombre', required=False)
    apellido = serializers.CharField(source='usuario.apellido', required=False)
    telefono = serializers.CharField(source='usuario.telefono', required=False)
    direccion = serializers.CharField(source='usuario.direccion', required=False)
    fecha_nacimiento = serializers.DateField(source='usuario.fecha_nacimiento', required=False)
    genero = serializers.ChoiceField(
        choices=Usuario.GENERO_CHOICES, 
        source='usuario.genero', 
        required=False
    )

    class Meta:
        model = Paciente
        fields = [
            'nombre', 'apellido', 'telefono', 'direccion', 'fecha_nacimiento', 'genero',
            'tipo_sangre', 'alergias', 'enfermedades_cronicas', 'medicamentos_actuales',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono', 
            'contacto_emergencia_parentesco', 'estado'
        ]

    def update(self, instance, validated_data):
        usuario_data = {}
        
        # Extraer datos de usuario si están presentes
        if 'usuario' in validated_data:
            usuario_data = validated_data.pop('usuario')
        
        # Actualizar campos del paciente
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar usuario si hay datos
        if usuario_data:
            usuario = instance.usuario
            for attr, value in usuario_data.items():
                setattr(usuario, attr, value)
            usuario.save()
        
        return instance

class PacienteSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para select de pacientes
    """
    usuario = UsuarioSelectSerializer(read_only=True)
    nombre_completo = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta:
        model = Paciente
        fields = ['usuario', 'nombre_completo', 'email', 'estado', 'tipo_sangre']

class PacienteResumenSerializer(serializers.ModelSerializer):
    """
    Serializer para resumen de pacientes (listados, dashboards)
    """
    nombre_completo = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    email = serializers.CharField(source='usuario.email', read_only=True)
    telefono = serializers.CharField(source='usuario.telefono', read_only=True)
    edad = serializers.SerializerMethodField()
    tiene_alergias = serializers.SerializerMethodField()
    tiene_enfermedades = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'usuario', 'nombre_completo', 'email', 'telefono', 'edad',
            'tipo_sangre', 'estado', 'tiene_alergias', 'tiene_enfermedades'
        ]

    def get_edad(self, obj):
        if obj.usuario.fecha_nacimiento:
            today = timezone.now().date()
            born = obj.usuario.fecha_nacimiento
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return None

    def get_tiene_alergias(self, obj):
        return bool(obj.alergias and obj.alergias.strip())

    def get_tiene_enfermedades(self, obj):
        return bool(obj.enfermedades_cronicas and obj.enfermedades_cronicas.strip())

class AdministradorSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    class Meta:
        model = Administrador
        fields = ['usuario']

class PerfilSerializer(serializers.ModelSerializer):
    tipo_usuario = serializers.CharField()
    datos_medico = serializers.SerializerMethodField()
    datos_paciente = serializers.SerializerMethodField()
    datos_admin = serializers.SerializerMethodField()
    rol = RolSerializer(read_only=True, source='id_rol')

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'apellido', 'telefono', 'direccion',
            'fecha_nacimiento', 'genero', 'activo', 'rol', 'tipo_usuario',
            'datos_medico', 'datos_paciente', 'datos_admin'
        ]
        read_only_fields = ['email', 'tipo_usuario', 'rol']

    def get_datos_medico(self, obj):
        if hasattr(obj, 'medico'):
            medico = obj.medico
            return {
                'numero_licencia': medico.numero_licencia,
                'estado': medico.estado,
                'firma_digital': medico.firma_digital,
                'especialidades': EspecialidadSerializer(medico.especialidades.all(), many=True).data
            }
        return None

    def get_datos_paciente(self, obj):
        if hasattr(obj, 'paciente'):
            paciente = obj.paciente
            return {
                'tipo_sangre': paciente.tipo_sangre,
                'alergias': paciente.alergias,
                'enfermedades_cronicas': paciente.enfermedades_cronicas,
                'medicamentos_actuales': paciente.medicamentos_actuales,
                'contacto_emergencia_nombre': paciente.contacto_emergencia_nombre,
                'contacto_emergencia_telefono': paciente.contacto_emergencia_telefono,
                'contacto_emergencia_parentesco': paciente.contacto_emergencia_parentesco,
                'estado': paciente.estado
            }
        return None

    def get_datos_admin(self, obj):
        if hasattr(obj, 'administrador'):
            return {'admin': True}
        return None

class RegistroPacienteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['email', 'password', 'nombre', 'apellido', 'telefono']

    def create(self, validated_data):
        rol_paciente = Rol.objects.get(nombre_rol='Paciente')
        validated_data['id_rol'] = rol_paciente

        password = validated_data.pop('password')
        usuario = Usuario.objects.create_user(password=password, **validated_data)

        Paciente.objects.create(usuario=usuario)
        return usuario

# NUEVOS SERIALIZERS PARA SPRINT 2

class TipoComponenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoComponente
        fields = ['id', 'nombre', 'descripcion']

class ComponenteUISerializer(serializers.ModelSerializer):
    tipo_componente = TipoComponenteSerializer(read_only=True)
    
    class Meta:
        model = ComponenteUI
        fields = [
            'id', 'tipo_componente', 'codigo_componente', 'nombre_componente',
            'descripcion', 'modulo', 'ruta', 'icono', 'orden', 'activo'
        ]

class PermisoComponenteSerializer(serializers.ModelSerializer):
    permiso = PermisoSerializer(read_only=True)
    componente = ComponenteUISerializer(read_only=True)
    id_permiso = serializers.PrimaryKeyRelatedField(
        queryset=Permiso.objects.all(),
        write_only=True,
        source='permiso'
    )
    id_componente = serializers.PrimaryKeyRelatedField(
        queryset=ComponenteUI.objects.all(),
        write_only=True,
        source='componente'
    )

    class Meta:
        model = PermisoComponente
        fields = [
            'id', 'permiso', 'componente', 'id_permiso', 'id_componente',
            'accion_permitida', 'condiciones'
        ]

class BitacoraSerializer(serializers.ModelSerializer):
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    usuario_apellido = serializers.CharField(source='usuario.apellido', read_only=True)
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Bitacora
        fields = [
            'id', 'usuario', 'usuario_email', 'usuario_nombre', 'usuario_apellido', 
            'nombre_completo', 'ip_address', 'accion_realizada', 'modulo_afectado', 
            'fecha_hora', 'detalles'
        ]
        read_only_fields = ['fecha_hora']

    def get_nombre_completo(self, obj):
        return f"{obj.usuario.nombre} {obj.usuario.apellido}"

class HorarioMedicoSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.CharField(source='medico_especialidad.medico.usuario.nombre', read_only=True)
    medico_apellido = serializers.CharField(source='medico_especialidad.medico.usuario.apellido', read_only=True)
    especialidad_nombre = serializers.CharField(source='medico_especialidad.especialidad.nombre', read_only=True)
    medico_id = serializers.IntegerField(source='medico_especialidad.medico.usuario.id', read_only=True)
    especialidad_id = serializers.IntegerField(source='medico_especialidad.especialidad.id', read_only=True)

    class Meta:
        model = HorarioMedico
        fields = [
            'id', 'medico_especialidad', 'medico_id', 'medico_nombre', 'medico_apellido',
            'especialidad_id', 'especialidad_nombre', 'dia_semana',
            'hora_inicio', 'hora_fin', 'activo', 'fecha_creacion'
        ]
        read_only_fields = ['fecha_creacion']

class HorarioDisponibleSerializer(serializers.Serializer):
    """
    Serializer para horarios disponibles
    """
    fecha = serializers.DateField()
    hora = serializers.TimeField()
    medico_especialidad_id = serializers.IntegerField()  # CAMBIADO: ahora usamos este ID
    medico_id = serializers.IntegerField()
    medico_nombre = serializers.CharField()
    especialidad_id = serializers.IntegerField()
    especialidad_nombre = serializers.CharField()

class MedicoHorarioSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para médicos en horarios
    """
    nombre_completo = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    especialidades = EspecialidadSerializer(many=True, read_only=True)

    class Meta:
        model = Medico
        fields = ['usuario', 'nombre_completo', 'especialidades']

class MedicoEspecialidadHorarioSerializer(serializers.ModelSerializer):
    """
    Serializer para médicos con sus especialidades (para selects de horarios)
    """
    medico_id = serializers.IntegerField(source='medico.usuario.id', read_only=True)
    medico_nombre_completo = serializers.CharField(source='medico.usuario.nombre_completo', read_only=True)
    especialidad_nombre = serializers.CharField(source='especialidad.nombre', read_only=True)
    
    # Horarios disponibles de esta combinación médico-especialidad
    horarios_disponibles = serializers.SerializerMethodField()

    class Meta:
        model = MedicoEspecialidad
        fields = [
            'id', 'medico_id', 'medico_nombre_completo', 
            'especialidad', 'especialidad_nombre', 'horarios_disponibles'
        ]

    def get_horarios_disponibles(self, obj):
        # Aquí podrías agregar lógica para obtener horarios disponibles
        # de esta combinación médico-especialidad
        horarios = HorarioMedico.objects.filter(
            medico_especialidad=obj,
            activo=True
        )
        return HorarioMedicoSerializer(horarios, many=True).data

class AgendaCitaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.usuario.nombre', read_only=True)
    paciente_apellido = serializers.CharField(source='paciente.usuario.apellido', read_only=True)
    medico_nombre = serializers.CharField(source='medico_especialidad.medico.usuario.nombre', read_only=True)
    medico_apellido = serializers.CharField(source='medico_especialidad.medico.usuario.apellido', read_only=True)
    especialidad_nombre = serializers.CharField(source='medico_especialidad.especialidad.nombre', read_only=True)
    medico_id = serializers.IntegerField(source='medico_especialidad.medico.usuario.id', read_only=True)
    especialidad_id = serializers.IntegerField(source='medico_especialidad.especialidad.id', read_only=True)

    class Meta:
        model = AgendaCita
        fields = [
            'id', 'paciente', 'paciente_nombre', 'paciente_apellido',
            'medico_especialidad', 'medico_id', 'medico_nombre', 'medico_apellido',
            'especialidad_id', 'especialidad_nombre',
            'fecha_cita', 'hora_cita', 'estado', 'motivo', 'notas',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def validate(self, data):
        """
        Validar que:
        - El médico atiende ese día (HorarioMedico).
        - La hora está dentro de un horario válido.
        - No existe otra cita en ese horario.
        """
        instance = self.instance  # En caso de actualización
        medico_especialidad = data.get('medico_especialidad') or (instance.medico_especialidad if instance else None)
        fecha_cita = data.get('fecha_cita') or (instance.fecha_cita if instance else None)
        hora_cita = data.get('hora_cita') or (instance.hora_cita if instance else None)

        # Si alguno falta, no validar aún (puede ser PATCH parcial)
        if not all([medico_especialidad, fecha_cita, hora_cita]):
            return data

        # Obtener día de la semana en español con primera mayúscula (ej: 'Lunes')
        dia_semana_ingles = fecha_cita.strftime('%A').capitalize()
        dias_map = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes', 
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        dia_semana = dias_map.get(dia_semana_ingles, dia_semana_ingles)

        # Buscar horarios del médico para ese día
        horarios = HorarioMedico.objects.filter(
            medico_especialidad=medico_especialidad,
            dia_semana=dia_semana,  # Ahora busca 'Martes' en lugar de 'Tuesday'
            activo=True
        )

        if not horarios.exists():
            raise serializers.ValidationError(
                f"El médico no tiene horarios disponibles para el día {dia_semana}."
            )

        # Verificar que hora_cita esté dentro de al menos uno de los horarios
        hora_valida = False
        for h in horarios:
            if h.hora_inicio <= hora_cita < h.hora_fin:
                hora_valida = True
                break

        if not hora_valida:
            raise serializers.ValidationError(
                f"La hora {hora_cita} no está dentro de los horarios disponibles del médico para el día {dia_semana}."
            )

        # Verificar que no haya otra cita en ese mismo horario
        conflicto = AgendaCita.objects.filter(
            medico_especialidad=medico_especialidad,
            fecha_cita=fecha_cita,
            hora_cita=hora_cita
        )
        if instance:
            conflicto = conflicto.exclude(id=instance.id)  # Excluirse a sí misma en actualización

        if conflicto.exists():
            raise serializers.ValidationError(
                f"Ya existe una cita agendada para este médico en {fecha_cita} a las {hora_cita}."
            )

        return data

class HistoriaClinicaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.usuario.nombre', read_only=True)
    paciente_apellido = serializers.CharField(source='paciente.usuario.apellido', read_only=True)
    paciente_email = serializers.CharField(source='paciente.usuario.email', read_only=True)

    class Meta:
        model = HistoriaClinica
        fields = [
            'id', 'paciente', 'paciente_nombre', 'paciente_apellido', 'paciente_email',
            'fecha_creacion', 'observaciones_generales', 'activo'
        ]
        read_only_fields = ['fecha_creacion']

class ConsultaSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.CharField(source='medico.usuario.nombre', read_only=True)
    medico_apellido = serializers.CharField(source='medico.usuario.apellido', read_only=True)
    paciente_nombre = serializers.CharField(source='historia_clinica.paciente.usuario.nombre', read_only=True)
    paciente_apellido = serializers.CharField(source='historia_clinica.paciente.usuario.apellido', read_only=True)

    class Meta:
        model = Consulta
        fields = [
            'id', 'historia_clinica', 'medico', 'medico_nombre', 'medico_apellido',
            'paciente_nombre', 'paciente_apellido', 'fecha_consulta', 'motivo_consulta', 'sintomas',
            'diagnostico', 'tratamiento', 'observaciones'
        ]
        read_only_fields = ['id', 'fecha_consulta']

class RegistroBackupSerializer(serializers.ModelSerializer):
    usuario_responsable_email = serializers.EmailField(source='usuario_responsable.email', read_only=True)
    usuario_responsable_nombre = serializers.CharField(source='usuario_responsable.nombre', read_only=True)
    usuario_responsable_apellido = serializers.CharField(source='usuario_responsable.apellido', read_only=True)
    nombre_completo_responsable = serializers.SerializerMethodField()

    class Meta:
        model = RegistroBackup
        fields = [
            'id', 'nombre_archivo', 'tamano_bytes', 'fecha_backup',
            'usuario_responsable', 'usuario_responsable_email', 
            'usuario_responsable_nombre', 'usuario_responsable_apellido',
            'nombre_completo_responsable', 'tipo_backup', 'estado', 
            'ubicacion_almacenamiento', 'notas'
        ]
        read_only_fields = ['fecha_backup']

    def get_nombre_completo_responsable(self, obj):
        return f"{obj.usuario_responsable.nombre} {obj.usuario_responsable.apellido}"


#-----------------Prueba-------
class AutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auto
        fields = '__all__'