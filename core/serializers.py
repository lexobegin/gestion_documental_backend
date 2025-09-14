from rest_framework import serializers
from .models import *

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

#-----------------Prueba-------
class AutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auto
        fields = '__all__'

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

