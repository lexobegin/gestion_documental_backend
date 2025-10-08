from rest_framework import viewsets, status, generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import *
from .serializers import *

# Views
class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all().order_by('-id')
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nombre', 'codigo']
    search_fields = ['nombre', 'codigo', 'descripcion']

class RegistroPacienteView(generics.CreateAPIView):
    serializer_class = RegistroPacienteSerializer
    permission_classes = [permissions.AllowAny]

class UsuarioViewSet(viewsets.ModelViewSet):
    #queryset = Usuario.objects.select_related('id_rol').all().order_by('-id')
    queryset = Usuario.objects.select_related('id_rol').all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['email', 'nombre', 'apellido', 'telefono', 'activo', 'genero', 'id_rol']
    search_fields = ['email', 'nombre', 'apellido', 'telefono']
    ordering_fields = ['id', 'email', 'nombre', 'apellido', 'activo']
    ordering = ['-id']

    @action(detail=True, methods=['post'], url_path='cambiar-password', permission_classes=[IsAuthenticated])
    def cambiar_password(self, request, pk=None):
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

class PacienteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Paciente.objects.select_related('usuario').order_by('-usuario__id')
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['estado', 'tipo_sangre']
    search_fields = ['usuario__nombre', 'usuario__apellido', 'usuario__email']

class MedicoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medico.objects.select_related('usuario').order_by('-usuario__id')
    serializer_class = MedicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['estado', 'especialidades']
    search_fields = ['usuario__nombre', 'usuario__apellido', 'numero_licencia']

class AdministradorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Administrador.objects.select_related('usuario').order_by('-usuario__id')
    serializer_class = AdministradorSerializer
    permission_classes = [IsAuthenticated]

class MiPerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all().order_by('-id')
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['nombre_rol']
    search_fields = ['nombre_rol', 'descripcion']

    @action(detail=True, methods=['get', 'put'], url_path='permisos')
    def permisos(self, request, pk=None):
        rol = self.get_object()
        if request.method == 'GET':
            permisos = rol.permisos.all()
            return Response([
                {
                    'id': p.id,
                    'nombre': p.nombre,
                    'codigo': p.codigo,
                    'descripcion': p.descripcion
                } for p in permisos
            ])
        elif request.method == 'PUT':
            ids = request.data.get('permisos', [])
            if not isinstance(ids, list):
                return Response({'detail': 'El campo permisos debe ser una lista de IDs.'}, status=status.HTTP_400_BAD_REQUEST)
            rol.permisos.set(ids)
            rol.save()
            return Response({'detail': 'Permisos actualizados correctamente.'})

class EspecialidadViewSet(viewsets.ModelViewSet):
    queryset = Especialidad.objects.all().order_by('-id')
    serializer_class = EspecialidadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['nombre']
    search_fields = ['nombre', 'codigo', 'descripcion']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.medicos.exists():
            return Response(
                {"detail": "No se puede eliminar la especialidad porque está asociada a uno o más médicos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

# NUEVOS VIEWSETS PARA SPRINT 2

class TipoComponenteViewSet(viewsets.ModelViewSet):
    queryset = TipoComponente.objects.all().order_by('id')
    serializer_class = TipoComponenteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['nombre', 'descripcion']

class ComponenteUIViewSet(viewsets.ModelViewSet):
    queryset = ComponenteUI.objects.select_related('tipo_componente').all().order_by('orden')
    serializer_class = ComponenteUISerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['modulo', 'tipo_componente', 'activo']
    search_fields = ['nombre_componente', 'codigo_componente', 'modulo']
    ordering_fields = ['orden', 'nombre_componente']

class PermisoComponenteViewSet(viewsets.ModelViewSet):
    queryset = PermisoComponente.objects.select_related('permiso', 'componente').all().order_by('id')
    serializer_class = PermisoComponenteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['permiso', 'componente', 'accion_permitida']

class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bitacora.objects.select_related('usuario').all().order_by('-fecha_hora')
    serializer_class = BitacoraSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['modulo_afectado', 'usuario']
    search_fields = ['accion_realizada', 'modulo_afectado', 'usuario__email']
    ordering_fields = ['fecha_hora', 'accion_realizada']
    ordering = ['-fecha_hora']

class HorarioMedicoViewSet(viewsets.ModelViewSet):
    queryset = HorarioMedico.objects.select_related('medico__usuario').all().order_by('medico', 'dia_semana', 'hora_inicio')
    serializer_class = HorarioMedicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['medico', 'dia_semana', 'activo']
    ordering_fields = ['dia_semana', 'hora_inicio']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Si es médico, solo ver sus horarios
        if hasattr(self.request.user, 'medico'):
            return queryset.filter(medico=self.request.user.medico)
        return queryset

class AgendaCitaViewSet(viewsets.ModelViewSet):
    queryset = AgendaCita.objects.select_related(
        'paciente__usuario', 'medico__usuario'
    ).all().order_by('-fecha_cita', '-hora_cita')
    serializer_class = AgendaCitaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'medico', 'paciente', 'fecha_cita']
    search_fields = [
        'paciente__usuario__nombre', 'paciente__usuario__apellido',
        'medico__usuario__nombre', 'medico__usuario__apellido'
    ]
    ordering_fields = ['fecha_cita', 'hora_cita', 'fecha_creacion']
    ordering = ['-fecha_cita', '-hora_cita']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Paciente: solo ver sus citas
        if hasattr(user, 'paciente'):
            return queryset.filter(paciente=user.paciente)
        # Médico: solo ver sus citas
        elif hasattr(user, 'medico'):
            return queryset.filter(medico=user.medico)
        # Admin: ver todas las citas
        return queryset

    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        cita = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado not in dict(AgendaCita.ESTADO_CHOICES):
            return Response(
                {'detail': 'Estado inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cita.estado = nuevo_estado
        cita.save()
        
        return Response({
            'detail': f'Estado de cita actualizado a {nuevo_estado}.',
            'cita': AgendaCitaSerializer(cita).data
        })

class HistoriaClinicaViewSet(viewsets.ModelViewSet):
    queryset = HistoriaClinica.objects.select_related('paciente__usuario').all().order_by('-fecha_creacion')
    serializer_class = HistoriaClinicaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['paciente', 'activo']
    search_fields = ['paciente__usuario__nombre', 'paciente__usuario__apellido']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Paciente: solo ver su historia clínica
        if hasattr(user, 'paciente'):
            return queryset.filter(paciente=user.paciente)
        # Médico: ver historias de sus pacientes
        elif hasattr(user, 'medico'):
            # Aquí podrías agregar lógica para filtrar por pacientes del médico
            return queryset
        return queryset

class ConsultaViewSet(viewsets.ModelViewSet):
    queryset = Consulta.objects.select_related(
        'historia_clinica__paciente__usuario', 'medico__usuario'
    ).all().order_by('-fecha_consulta')
    serializer_class = ConsultaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['historia_clinica', 'medico']
    ordering_fields = ['fecha_consulta']
    ordering = ['-fecha_consulta']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if hasattr(user, 'medico'):
            return queryset.filter(medico=user.medico)
        elif hasattr(user, 'paciente'):
            return queryset.filter(historia_clinica__paciente=user.paciente)
        return queryset


class RegistroBackupViewSet(viewsets.ModelViewSet):
    queryset = RegistroBackup.objects.select_related('usuario_responsable').all().order_by('-fecha_backup')
    serializer_class = RegistroBackupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo_backup', 'estado', 'usuario_responsable']
    search_fields = ['nombre_archivo']
    ordering_fields = ['fecha_backup']
    ordering = ['-fecha_backup']

    @action(detail=False, methods=['post'], url_path='realizar-backup')
    def realizar_backup(self, request):
        # Lógica para realizar backup (simulada)
        backup = RegistroBackup.objects.create(
            nombre_archivo=f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sql",
            usuario_responsable=request.user,
            tipo_backup=request.data.get('tipo_backup', 'Completo'),
            estado='En Progreso',
            ubicacion_almacenamiento='/backups/'
        )
        
        # Simular proceso de backup
        backup.estado = 'Exitoso'
        backup.tamano_bytes = 1024000  # 1MB simulado
        backup.save()
        
        return Response({
            'detail': 'Backup realizado exitosamente.',
            'backup': RegistroBackupSerializer(backup).data
        })

#-----------------Prueba-------
class AutoViewSet(viewsets.ModelViewSet):
    queryset = Auto.objects.all().order_by('-id')
    serializer_class = AutoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['marca', 'modelo']
    search_fields = ['marca', 'modelo']
