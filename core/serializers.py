from rest_framework import serializers
from .models import *
from rest_framework import serializers
from .models import *

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

class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ['id', 'codigo', 'nombre', 'descripcion']

class MedicoEspecialidadSerializer(serializers.ModelSerializer):
    especialidad = EspecialidadSerializer(read_only=True)

    class Meta:
        model = MedicoEspecialidad
        fields = ['especialidad']

class MedicoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    especialidades = EspecialidadSerializer(many=True, read_only=True)

    class Meta:
        model = Medico
        fields = ['usuario', 'numero_licencia', 'firma_digital', 'estado', 'especialidades']
    
    def get_especialidades(self, obj):
        relaciones = MedicoEspecialidad.objects.filter(medico=obj).select_related('especialidad')
        return MedicoEspecialidadSerializer(relaciones, many=True).data

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
    medico_nombre = serializers.CharField(source='medico.usuario.nombre', read_only=True)
    medico_apellido = serializers.CharField(source='medico.usuario.apellido', read_only=True)

    class Meta:
        model = HorarioMedico
        fields = [
            'id', 'medico', 'medico_nombre', 'medico_apellido', 'dia_semana',
            'hora_inicio', 'hora_fin', 'activo', 'fecha_creacion'
        ]
        read_only_fields = ['fecha_creacion']

class AgendaCitaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(source='paciente.usuario.nombre', read_only=True)
    paciente_apellido = serializers.CharField(source='paciente.usuario.apellido', read_only=True)
    medico_nombre = serializers.CharField(source='medico.usuario.nombre', read_only=True)
    medico_apellido = serializers.CharField(source='medico.usuario.apellido', read_only=True)
    especialidad_medico = serializers.SerializerMethodField()

    class Meta:
        model = AgendaCita
        fields = [
            'id', 'paciente', 'paciente_nombre', 'paciente_apellido',
            'medico', 'medico_nombre', 'medico_apellido', 'especialidad_medico',
            'fecha_cita', 'hora_cita', 'estado', 'motivo', 'notas',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']

    def get_especialidad_medico(self, obj):
        especialidades = obj.medico.especialidades.all()
        return EspecialidadSerializer(especialidades, many=True).data

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
    # Campos calculados/automáticos en backend
    historia_clinica = serializers.PrimaryKeyRelatedField(read_only=True)
    medico = serializers.PrimaryKeyRelatedField(read_only=True)

    # Campo de entrada desde el frontend
    paciente = serializers.IntegerField(write_only=True)

    class Meta:
        model = Consulta
        fields = [
            'id',
            'historia_clinica',
            'medico',
            'paciente',
            'motivo_consulta',
            'sintomas',
            'diagnostico',
            'tratamiento',
            'observaciones',
            'fecha_consulta',
        ]
        read_only_fields = ['id', 'fecha_consulta', 'historia_clinica', 'medico']

    def validate(self, attrs):
        # Validar que exista historia clínica activa para el paciente
        paciente_id = attrs.get('paciente')
        if paciente_id is None:
            raise ValidationError({'paciente': 'Este campo es requerido.'})

        historia = HistoriaClinica.objects.filter(paciente_id=paciente_id, activo=True).first()
        if historia is None:
            raise ValidationError({'paciente': 'El paciente no tiene una historia clínica activa.'})

        # Guardar para usar en create sin tener que reconsultar
        attrs['_historia'] = historia
        return attrs

    def create(self, validated_data):
        # Remover el campo que no pertenece al modelo
        validated_data.pop('paciente', None)

        # Recuperar historia precalculada en validate
        historia = validated_data.pop('_historia', None)

        # Usuario y médico asociado
        request = self.context.get('request')
        if request is None or not hasattr(request.user, 'medico'):
            raise PermissionDenied('Solo los médicos autenticados pueden crear consultas.')

        medico = request.user.medico

        # Crear instancia usando únicamente campos del modelo
        return Consulta.objects.create(
            historia_clinica=historia,
            medico=medico,
            **validated_data
        )



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