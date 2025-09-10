from rest_framework import viewsets, status, generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from .serializers import *

# Registro paciente
class RegistroPacienteView(generics.CreateAPIView):
    serializer_class = RegistroPacienteSerializer
    permission_classes = [permissions.AllowAny]  # acceso público

# Usuarios
class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Usuario.objects.all().order_by('-id')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

# Pacientes
class PacienteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Paciente.objects.select_related('usuario').order_by('-usuario__id')
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]

# Médicos
class MedicoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medico.objects.select_related('usuario').order_by('-usuario__id')
    serializer_class = MedicoSerializer
    permission_classes = [IsAuthenticated]

# Administradores
class AdministradorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Administrador.objects.select_related('usuario').order_by('-usuario__id')
    serializer_class = AdministradorSerializer
    permission_classes = [IsAuthenticated]

class MiPerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

# Roles
class RolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rol.objects.all().order_by('-id')
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

#-----------------Prueba-------
class AutoViewSet(viewsets.ModelViewSet):
    queryset = Auto.objects.all().order_by('-id')
    serializer_class = AutoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['marca', 'modelo']
    search_fields = ['marca', 'modelo']

class EspecialidadViewSet(viewsets.ModelViewSet):
    queryset = Especialidad.objects.all().order_by('-id')
    serializer_class = EspecialidadSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['nombre']
    search_fields = ['nombre']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Verificar si hay médicos asociados
        if instance.medicos.exists():
            return Response(
                {"detail": "No se puede eliminar la especialidad porque está asociada a uno o más médicos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)