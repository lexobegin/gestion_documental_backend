from rest_framework import viewsets, status, generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta, time

from rest_framework_simplejwt.views import TokenObtainPairView
#from .serializers import CustomTokenObtainPairSerializer

from .models import *
from .serializers import *

#TOKEN
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

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

class PacienteSelectView(generics.ListAPIView):
    """
    Endpoint para select de pacientes - sin paginación
    """
    serializer_class = PacienteSelectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Paciente.objects.select_related('usuario').filter(
            usuario__activo=True,
            estado='Activo'
        ).order_by('usuario__nombre', 'usuario__apellido')
        
        # Filtro por nombre o apellido
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(usuario__nombre__icontains=search) |
                Q(usuario__apellido__icontains=search) |
                Q(usuario__email__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Deshabilitar paginación
        self.pagination_class = None
        return super().list(request, *args, **kwargs)

class MedicoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medico.objects.select_related('usuario').order_by('-usuario__id')
    serializer_class = MedicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['estado', 'especialidades']
    search_fields = ['usuario__nombre', 'usuario__apellido', 'numero_licencia']

class MedicoSelectView(generics.ListAPIView):
    """
    Endpoint para select de médicos - sin paginación
    """
    serializer_class = MedicoSelectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Medico.objects.select_related('usuario').prefetch_related('especialidades').filter(
            usuario__activo=True,
            estado='Activo'
        ).order_by('usuario__nombre', 'usuario__apellido')
        
        # Filtro por nombre, apellido o especialidad
        search = self.request.query_params.get('search', None)
        especialidad_id = self.request.query_params.get('especialidad', None)
        
        if search:
            queryset = queryset.filter(
                Q(usuario__nombre__icontains=search) |
                Q(usuario__apellido__icontains=search) |
                Q(usuario__email__icontains=search) |
                Q(numero_licencia__icontains=search)
            )
        
        if especialidad_id:
            queryset = queryset.filter(especialidades__id=especialidad_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Deshabilitar paginación
        self.pagination_class = None
        return super().list(request, *args, **kwargs)

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
    queryset = HorarioMedico.objects.select_related(
        'medico_especialidad__medico__usuario',
        'medico_especialidad__especialidad'
    ).all().order_by('medico_especialidad__medico', 'dia_semana', 'hora_inicio')
    serializer_class = HorarioMedicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['medico_especialidad__medico', 'dia_semana', 'activo']
    ordering_fields = ['dia_semana', 'hora_inicio']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Si es médico, solo ver sus horarios
        if hasattr(self.request.user, 'medico'):
            return queryset.filter(medico_especialidad__medico=self.request.user.medico)
        return queryset

class HorariosDisponiblesMedicoLogueadoView(generics.ListAPIView):
    """
    Endpoint para horarios disponibles del médico logueado
    """
    permission_classes = [IsAuthenticated]
    serializer_class = HorarioDisponibleSerializer

    def get_queryset(self):
        # Verificar que el usuario sea médico
        if not hasattr(self.request.user, 'medico'):
            return []
        
        medico = self.request.user.medico
        return self._get_horarios_disponibles(medico)

    def _get_horarios_disponibles(self, medico, fecha_inicio=None, fecha_fin=None, especialidad_id=None):
        """
        Método común para obtener horarios disponibles
        """
        # Definir rango de fechas (por defecto próximos 15 días)
        if not fecha_inicio:
            fecha_inicio = timezone.now().date()
        if not fecha_fin:
            fecha_fin = fecha_inicio + timedelta(days=15)
        
        # Obtener las especialidades del médico
        medico_especialidades = MedicoEspecialidad.objects.filter(medico=medico)
        
        # Filtrar por especialidad si se especifica
        if especialidad_id:
            medico_especialidades = medico_especialidades.filter(especialidad_id=especialidad_id)
        
        # Obtener horarios configurados del médico
        horarios_config = HorarioMedico.objects.filter(
            medico_especialidad__in=medico_especialidades,
            activo=True
        )
        
        # Generar lista de horarios disponibles
        horarios_disponibles = []
        
        # Recorrer cada día en el rango
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            dia_semana = current_date.strftime('%A')
            # Mapear día en inglés a español
            dias_map = {
                'Monday': 'Lunes',
                'Tuesday': 'Martes',
                'Wednesday': 'Miércoles',
                'Thursday': 'Jueves',
                'Friday': 'Viernes',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }
            dia_semana_es = dias_map.get(dia_semana, dia_semana)
            
            # Buscar horarios para este día
            horarios_dia = horarios_config.filter(dia_semana=dia_semana_es)
            
            for horario in horarios_dia:
                # Generar slots de 30 minutos
                hora_actual = horario.hora_inicio
                while hora_actual < horario.hora_fin:
                    # Verificar si ya existe una cita en este horario
                    cita_existente = AgendaCita.objects.filter(
                        medico_especialidad=horario.medico_especialidad,  # NUEVO: relación directa
                        fecha_cita=current_date,
                        hora_cita=hora_actual,
                        estado__in=['pendiente', 'confirmada']
                    ).exists()
                    
                    # Crear datetime con timezone para comparación
                    fecha_hora_completa = timezone.make_aware(
                        datetime.combine(current_date, hora_actual)
                    )
                    
                    # Solo agregar si no hay cita y no es en el pasado
                    if not cita_existente and fecha_hora_completa > timezone.now():
                        horarios_disponibles.append({
                            'fecha': current_date,
                            'hora': hora_actual,
                            'medico_especialidad_id': horario.medico_especialidad.id,
                            'medico_id': medico.usuario.id,
                            'medico_nombre': f"Dr. {medico.usuario.nombre} {medico.usuario.apellido}",
                            'especialidad_id': horario.medico_especialidad.especialidad.id,
                            'especialidad_nombre': horario.medico_especialidad.especialidad.nombre
                        })
                    
                    # Incrementar 30 minutos
                    hora_dt = datetime.combine(current_date, hora_actual)
                    hora_dt += timedelta(minutes=30)
                    hora_actual = hora_dt.time()
            
            current_date += timedelta(days=1)
        
        return horarios_disponibles

    def list(self, request, *args, **kwargs):
        horarios = self.get_queryset()
        
        # Aplicar filtros desde query params
        fecha = self.request.query_params.get('fecha', None)
        especialidad_id = self.request.query_params.get('especialidad', None)
        
        if fecha:
            try:
                fecha_filtro = datetime.strptime(fecha, '%Y-%m-%d').date()
                horarios = [h for h in horarios if h['fecha'] == fecha_filtro]
            except ValueError:
                pass
        
        if especialidad_id:
            horarios = [h for h in horarios if any(
                esp['id'] == int(especialidad_id) for esp in h['especialidades']
            )]
        
        # Ordenar por fecha y hora
        horarios.sort(key=lambda x: (x['fecha'], x['hora']))
        
        return Response(horarios)

class HorariosDisponiblesPorMedicoEspecialidadView(generics.ListAPIView):
    """
    Endpoint para horarios disponibles por médico o especialidad
    """
    permission_classes = [IsAuthenticated]
    serializer_class = HorarioDisponibleSerializer

    def get_queryset(self):
        medico_id = self.request.query_params.get('medico_id', None)
        especialidad_id = self.request.query_params.get('especialidad_id', None)
        fecha_inicio = self.request.query_params.get('fecha_inicio', None)
        fecha_fin = self.request.query_params.get('fecha_fin', None)
        
        # Buscar médicos según los filtros
        medicos_query = Medico.objects.select_related('usuario').prefetch_related('especialidades').filter(
            usuario__activo=True,
            estado='Activo'
        )
        
        if medico_id:
            medicos_query = medicos_query.filter(usuario__id=medico_id)
        
        if especialidad_id:
            medicos_query = medicos_query.filter(especialidades__id=especialidad_id)
        
        # Obtener todos los horarios disponibles de los médicos filtrados
        todos_horarios = []
        for medico in medicos_query:
            # Convertir fechas string a date si vienen
            fecha_ini = None
            fecha_end = None
            
            if fecha_inicio:
                try:
                    fecha_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            if fecha_fin:
                try:
                    fecha_end = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            # Usar el mismo método helper
            horarios_medico = self._get_horarios_disponibles(
                medico, fecha_ini, fecha_end, especialidad_id
            )
            todos_horarios.extend(horarios_medico)
        
        return todos_horarios

    def _get_horarios_disponibles(self, medico, fecha_inicio=None, fecha_fin=None, especialidad_id=None):
        """
        Método común para obtener horarios disponibles
        """
        # Definir rango de fechas (por defecto próximos 15 días)
        if not fecha_inicio:
            fecha_inicio = timezone.now().date()
        if not fecha_fin:
            fecha_fin = fecha_inicio + timedelta(days=15)
        
        # Obtener las especialidades del médico
        medico_especialidades = MedicoEspecialidad.objects.filter(medico=medico)
        
        # Filtrar por especialidad si se especifica
        if especialidad_id:
            medico_especialidades = medico_especialidades.filter(especialidad_id=especialidad_id)
        
        # Obtener horarios configurados del médico
        horarios_config = HorarioMedico.objects.filter(
            medico_especialidad__in=medico_especialidades,
            activo=True
        )
        
        # Generar lista de horarios disponibles
        horarios_disponibles = []
        
        # Recorrer cada día en el rango
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            dia_semana = current_date.strftime('%A')
            # Mapear día en inglés a español
            dias_map = {
                'Monday': 'Lunes',
                'Tuesday': 'Martes',
                'Wednesday': 'Miércoles',
                'Thursday': 'Jueves',
                'Friday': 'Viernes',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }
            dia_semana_es = dias_map.get(dia_semana, dia_semana)
            
            # Buscar horarios para este día
            horarios_dia = horarios_config.filter(dia_semana=dia_semana_es)
            
            for horario in horarios_dia:
                # Generar slots de 30 minutos
                hora_actual = horario.hora_inicio
                while hora_actual < horario.hora_fin:
                    # Verificar si ya existe una cita en este horario
                    cita_existente = AgendaCita.objects.filter(
                        medico_especialidad=horario.medico_especialidad,  # NUEVO: relación directa
                        fecha_cita=current_date,
                        hora_cita=hora_actual,
                        estado__in=['pendiente', 'confirmada']
                    ).exists()
                    
                    # Crear datetime con timezone para comparación
                    fecha_hora_completa = timezone.make_aware(
                        datetime.combine(current_date, hora_actual)
                    )
                    
                    # Solo agregar si no hay cita y no es en el pasado
                    if not cita_existente and fecha_hora_completa > timezone.now():
                        horarios_disponibles.append({
                            'fecha': current_date,
                            'hora': hora_actual,
                            'medico_especialidad_id': horario.medico_especialidad.id,
                            'medico_id': medico.usuario.id,
                            'medico_nombre': f"Dr. {medico.usuario.nombre} {medico.usuario.apellido}",
                            'especialidad_id': horario.medico_especialidad.especialidad.id,
                            'especialidad_nombre': horario.medico_especialidad.especialidad.nombre
                        })
                    
                    # Incrementar 30 minutos
                    hora_dt = datetime.combine(current_date, hora_actual)
                    hora_dt += timedelta(minutes=30)
                    hora_actual = hora_dt.time()
            
            current_date += timedelta(days=1)
        
        return horarios_disponibles
    
    def list(self, request, *args, **kwargs):
        horarios = self.get_queryset()
        
        # Ordenar por fecha, hora y médico
        horarios.sort(key=lambda x: (x['fecha'], x['hora'], x['medico_nombre']))
        
        return Response(horarios)

class AgendaCitaViewSet(viewsets.ModelViewSet):
    queryset = AgendaCita.objects.select_related(
        'paciente__usuario', 
        'medico_especialidad__medico__usuario',
        'medico_especialidad__especialidad'
    ).all().order_by('-fecha_cita', '-hora_cita')
    serializer_class = AgendaCitaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'medico_especialidad__medico', 'paciente', 'fecha_cita']
    search_fields = [
        'paciente__usuario__nombre', 'paciente__usuario__apellido',
        'medico_especialidad__medico__usuario__nombre', 'medico_especialidad__medico__usuario__apellido'
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
            return queryset.filter(medico_especialidad__medico=user.medico)
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
        
        # Médico: solo ver sus consultas
        if hasattr(user, 'medico'):
            return queryset.filter(medico=user.medico)
        # Paciente: solo ver consultas de su historia clínica
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
