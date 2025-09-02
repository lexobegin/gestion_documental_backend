from rest_framework import serializers
from .models import *

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre_rol', 'descripcion']

class UsuarioSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True, source='id_rol')

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'apellido', 'telefono', 'direccion',
            'fecha_nacimiento', 'genero', 'activo', 'rol'
        ]

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