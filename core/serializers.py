from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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
    # Lectura: objeto rol anidado (como “detalle”)
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

class PacienteSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    class Meta:
        model = Paciente
        fields = [
            'usuario', 'tipo_sangre', 'alergias', 'enfermedades_cronicas',
            'medicamentos_actuales', 'contacto_emergencia_nombre',
            'contacto_emergencia_telefono', 'contacto_emergencia_parentesco',
            'estado'
        ]

class PacienteSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para select de pacientes
    """
    usuario = UsuarioSelectSerializer(read_only=True)
    nombre_completo = serializers.CharField(source='usuario.nombre_completo', read_only=True)

    class Meta:
        model = Paciente
        fields = ['usuario', 'nombre_completo', 'estado']

class AdministradorSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    class Meta:
        model = Administrador
        fields = ['usuario']

class PerfilSerializer(serializers.ModelSerializer):
    #tipo_usuario = serializers.CharField(source='tipo_usuario', read_only=True)
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

    class Meta:
        model = Bitacora
        fields = [
            'id', 'usuario', 'usuario_email', 'usuario_nombre', 'ip_address',
            'accion_realizada', 'modulo_afectado', 'fecha_hora', 'detalles'
        ]
        read_only_fields = ['fecha_hora']

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

class HistoriaClinicaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.usuario.nombre', read_only=True)
    paciente_apellido = serializers.CharField(source='paciente.usuario.apellido', read_only=True)

    class Meta:
        model = HistoriaClinica
        fields = [
            'id', 'paciente', 'paciente_nombre', 'paciente_apellido',
            'fecha_creacion', 'observaciones_generales', 'activo'
        ]
        read_only_fields = ['fecha_creacion']

class ConsultaSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.CharField(source='medico.usuario.nombre', read_only=True)
    medico_apellido = serializers.CharField(source='medico.usuario.apellido', read_only=True)
    paciente_nombre = serializers.CharField(source='historia_clinica.paciente.usuario.nombre', read_only=True)

    class Meta:
        model = Consulta
        fields = [
            'id', 'historia_clinica', 'medico', 'medico_nombre', 'medico_apellido',
            'paciente_nombre', 'fecha_consulta', 'motivo_consulta', 'sintomas',
            'diagnostico', 'tratamiento', 'observaciones'
        ]
        read_only_fields = ['fecha_consulta']

class RegistroBackupSerializer(serializers.ModelSerializer):
    usuario_responsable_email = serializers.EmailField(source='usuario_responsable.email', read_only=True)
    usuario_responsable_nombre = serializers.CharField(source='usuario_responsable.nombre', read_only=True)

    class Meta:
        model = RegistroBackup
        fields = [
            'id', 'nombre_archivo', 'tamano_bytes', 'fecha_backup',
            'usuario_responsable', 'usuario_responsable_email', 'usuario_responsable_nombre',
            'tipo_backup', 'estado', 'ubicacion_almacenamiento', 'notas'
        ]
        read_only_fields = ['fecha_backup']


#-----------------Prueba-------
class AutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auto
        fields = '__all__'