from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *

# Usuarios
class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

# Pacientes
class PacienteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Paciente.objects.select_related('usuario')
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]

# Médicos
class MedicoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medico.objects.select_related('usuario')
    serializer_class = MedicoSerializer
    permission_classes = [IsAuthenticated]

# Administradores
class AdministradorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Administrador.objects.select_related('usuario')
    serializer_class = AdministradorSerializer
    permission_classes = [IsAuthenticated]

# Roles
class RolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

#-----------------Prueba-------
class AutoViewSet(viewsets.ModelViewSet):
    queryset = Auto.objects.all().order_by('-id')
    serializer_class = AutoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['marca', 'modelo']
    search_fields = ['marca', 'modelo']