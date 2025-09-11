from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import *
from .serializers import *

# Usuarios  ✅ ahora acepta POST/PUT/PATCH/DELETE
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related('id_rol').all().order_by('id')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    # Filtros/orden/búsqueda al estilo de tu AutoViewSet
    filterset_fields = ['email', 'nombre', 'apellido', 'telefono', 'activo', 'genero', 'id_rol']
    search_fields = ['email', 'nombre', 'apellido', 'telefono']
    ordering_fields = ['id', 'email', 'nombre', 'apellido', 'activo']
    ordering = ['id']

    @action(detail=True, methods=['post'], url_path='cambiar-password', permission_classes=[IsAuthenticated])
    def cambiar_password(self, request, pk=None):
        """
        Cambia la contraseña del usuario {id}.
        Body: { "password": "NuevaClave123" }  (mínimo 6 caracteres)
        """
        new_password = request.data.get('password')
        if not new_password or len(new_password) < 6:
            return Response(
                {'detail': 'Password inválido (mínimo 6 caracteres).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = self.get_object()
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password actualizado correctamente.'}, status=status.HTTP_200_OK)

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
    queryset = Rol.objects.all().order_by('id')
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

#-----------------Prueba-------
class AutoViewSet(viewsets.ModelViewSet):
    queryset = Auto.objects.all().order_by('-id')
    serializer_class = AutoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['marca', 'modelo']
    search_fields = ['marca', 'modelo']
