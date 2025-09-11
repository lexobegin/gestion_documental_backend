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


# Mantén tus demás serializers tal como los tenías:
class MedicoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()
    class Meta:
        model = Medico
        fields = ['usuario', 'numero_licencia', 'firma_digital', 'estado']

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
