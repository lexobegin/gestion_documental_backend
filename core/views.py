from rest_framework import viewsets, status, generics, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta, time

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.contrib.auth import authenticate
from django.db import transaction

from .models import *
from .serializers import *

# VISTA PERSONALIZADA DE LOGIN
@api_view(['POST'])
@permission_classes([AllowAny])
def login_personalizado(request):
    """
    Vista personalizada para login que registra en bitácora
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'detail': 'Email y contraseña son requeridos'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Autenticar usuario - Usamos username field que debería ser el email
    user = authenticate(request, username=email, password=password)
    
    if user is not None and user.is_active:
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        # Registrar en bitácora
        try:
            with transaction.atomic():
                Bitacora.objects.create(
                    usuario=user,
                    ip_address=get_client_ip(request),
                    accion_realizada='Inicio de sesión exitoso',
                    modulo_afectado='autenticacion',
                    detalles=f'Usuario {email} inició sesión correctamente'
                )
        except Exception as e:
            print(f"Error al registrar en bitácora: {str(e)}")
            # Continuamos aunque falle la bitácora
        
        # Serializar datos del usuario
        from .serializers import UsuarioSerializer
        user_data = UsuarioSerializer(user).data
        
        # Devolver respuesta similar a SimpleJWT
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data
        })
    else:
        # Registrar intento fallido
        try:
            usuario_admin = Usuario.objects.filter(is_superuser=True).first()
            if usuario_admin:
                Bitacora.objects.create(
                    usuario=usuario_admin,
                    ip_address=get_client_ip(request),
                    accion_realizada='Intento fallido de inicio de sesión',
                    modulo_afectado='autenticacion',
                    detalles=f'Intento fallido para usuario: {email}'
                )
        except Exception as e:
            print(f"Error al registrar intento fallido: {str(e)}")
        
        return Response(
            {'detail': 'Credenciales inválidas'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

# VISTA PERSONALIZADA DE LOGOUT
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_personalizado(request):
    """
    Vista personalizada para logout que invalida el token y registra en bitácora
    """
    try:
        refresh_token = request.data.get('refresh_token')
        
        if refresh_token:
            # Invalidar el refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # También invalidar el access token actual
        # En SimpleJWT, los access tokens no se pueden blacklistear por defecto
        # pero podemos registrar el logout en bitácora
        
        # Registrar en bitácora
        Bitacora.objects.create(
            usuario=request.user,
            ip_address=get_client_ip(request),
            accion_realizada='Cierre de sesión exitoso',
            modulo_afectado='autenticacion',
            detalles=f'Usuario {request.user.email} cerró sesión correctamente'
        )
        
        return Response({
            'detail': 'Sesión cerrada correctamente'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Registrar error en bitácora
        Bitacora.objects.create(
            usuario=request.user,
            ip_address=get_client_ip(request),
            accion_realizada='Error en cierre de sesión',
            modulo_afectado='autenticacion',
            detalles=f'Error al cerrar sesión: {str(e)}'
        )
        
        return Response({
            'detail': 'Error al cerrar sesión'
        }, status=status.HTTP_400_BAD_REQUEST)

def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip

#TOKEN (Mantengo por si acaso, pero usaremos login_personalizado)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# EL ENDPOINT PUBLICO registrar_acceso HA SIDO ELIMINADO
# Y REEMPLAZADO POR login_personalizado y logout_personalizado

# Views
class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all().order_by('-id')
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nombre', 'codigo']
    search_fields = ['nombre', 'codigo', 'descripcion']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Creó permiso: {instance.nombre}",
            modulo="permisos",
            detalles=f"Permiso {instance.codigo} creado"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Actualizó permiso: {instance.nombre}",
            modulo="permisos",
            detalles=f"Permiso {instance.codigo} actualizado"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Eliminó permiso: {instance.nombre}",
            modulo="permisos",
            detalles=f"Permiso {instance.codigo} eliminado"
        )
        instance.delete()

class RegistroPacienteView(generics.CreateAPIView):
    serializer_class = RegistroPacienteSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=instance,
            request=self.request,
            accion="Registro de nuevo paciente",
            modulo="pacientes",
            detalles=f"Paciente {instance.email} registrado en el sistema"
        )

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related('id_rol').all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['email', 'nombre', 'apellido', 'telefono', 'activo', 'genero', 'id_rol']
    search_fields = ['email', 'nombre', 'apellido', 'telefono']
    ordering_fields = ['id', 'email', 'nombre', 'apellido', 'activo']
    ordering = ['-id']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Creó usuario: {instance.email}",
            modulo="usuarios",
            detalles=f"Usuario {instance.nombre} {instance.apellido} creado con rol {instance.id_rol.nombre_rol}"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Actualizó usuario: {instance.email}",
            modulo="usuarios",
            detalles=f"Usuario {instance.nombre} {instance.apellido} actualizado"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Eliminó usuario: {instance.email}",
            modulo="usuarios",
            detalles=f"Usuario {instance.nombre} {instance.apellido} eliminado"
        )
        instance.delete()

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
        
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Cambió password de usuario: {user.email}",
            modulo="usuarios",
            detalles="Contraseña actualizada"
        )
        
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

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Actualizó su perfil",
            modulo="perfil",
            detalles="Información personal actualizada"
        )

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all().order_by('-id')
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['nombre_rol']
    search_fields = ['nombre_rol', 'descripcion']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Creó rol: {instance.nombre_rol}",
            modulo="roles",
            detalles=f"Rol {instance.nombre_rol} creado"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Actualizó rol: {instance.nombre_rol}",
            modulo="roles",
            detalles=f"Rol {instance.nombre_rol} actualizado"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Eliminó rol: {instance.nombre_rol}",
            modulo="roles",
            detalles=f"Rol {instance.nombre_rol} eliminado"
        )
        instance.delete()

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
            
            # Registrar cambio de permisos
            permisos_anteriores = set(rol.permisos.values_list('id', flat=True))
            permisos_nuevos = set(ids)
            
            rol.permisos.set(ids)
            rol.save()
            
            # Registrar en bitácora
            Bitacora.registrar_accion(
                usuario=self.request.user,
                request=self.request,
                accion=f"Actualizó permisos del rol: {rol.nombre_rol}",
                modulo="roles",
                detalles=f"Permisos modificados: {len(permisos_nuevos - permisos_anteriores)} agregados, {len(permisos_anteriores - permisos_nuevos)} removidos"
            )
            
            return Response({'detail': 'Permisos actualizados correctamente.'})

class EspecialidadViewSet(viewsets.ModelViewSet):
    queryset = Especialidad.objects.all().order_by('-id')
    serializer_class = EspecialidadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['nombre']
    search_fields = ['nombre', 'codigo', 'descripcion']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Creó especialidad: {instance.nombre}",
            modulo="especialidades",
            detalles=f"Especialidad {instance.codigo} creada"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Actualizó especialidad: {instance.nombre}",
            modulo="especialidades",
            detalles=f"Especialidad {instance.codigo} actualizada"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Eliminó especialidad: {instance.nombre}",
            modulo="especialidades",
            detalles=f"Especialidad {instance.codigo} eliminada"
        )
        instance.delete()

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

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Creó tipo componente: {instance.nombre}",
            modulo="componentes",
            detalles=f"Tipo componente {instance.nombre} creado"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Actualizó tipo componente: {instance.nombre}",
            modulo="componentes",
            detalles=f"Tipo componente {instance.nombre} actualizado"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Eliminó tipo componente: {instance.nombre}",
            modulo="componentes",
            detalles=f"Tipo componente {instance.nombre} eliminado"
        )
        instance.delete()

class ComponenteUIViewSet(viewsets.ModelViewSet):
    queryset = ComponenteUI.objects.select_related('tipo_componente').all().order_by('orden')
    serializer_class = ComponenteUISerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['modulo', 'tipo_componente', 'activo']
    search_fields = ['nombre_componente', 'codigo_componente', 'modulo']
    ordering_fields = ['orden', 'nombre_componente']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Creó componente UI: {instance.nombre_componente}",
            modulo="componentes",
            detalles=f"Componente {instance.codigo_componente} creado"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Actualizó componente UI: {instance.nombre_componente}",
            modulo="componentes",
            detalles=f"Componente {instance.codigo_componente} actualizado"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Eliminó componente UI: {instance.nombre_componente}",
            modulo="componentes",
            detalles=f"Componente {instance.codigo_componente} eliminado"
        )
        instance.delete()

class PermisoComponenteViewSet(viewsets.ModelViewSet):
    queryset = PermisoComponente.objects.select_related('permiso', 'componente').all().order_by('id')
    serializer_class = PermisoComponenteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['permiso', 'componente', 'accion_permitida']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Creó permiso componente: {instance.permiso.nombre} - {instance.componente.nombre_componente}",
            modulo="permisos_componentes",
            detalles=f"Permiso {instance.accion_permitida} asignado"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Actualizó permiso componente: {instance.permiso.nombre} - {instance.componente.nombre_componente}",
            modulo="permisos_componentes",
            detalles=f"Permiso {instance.accion_permitida} actualizado"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Eliminó permiso componente: {instance.permiso.nombre} - {instance.componente.nombre_componente}",
            modulo="permisos_componentes",
            detalles=f"Permiso {instance.accion_permitida} eliminado"
        )
        instance.delete()

class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bitacora.objects.select_related('usuario').all().order_by('-fecha_hora')
    serializer_class = BitacoraSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['modulo_afectado', 'usuario']
    search_fields = ['accion_realizada', 'modulo_afectado', 'usuario__email', 'detalles']
    ordering_fields = ['fecha_hora', 'accion_realizada']
    ordering = ['-fecha_hora']

    # ✅ EXPORTAR A PDF
    @action(detail=False, methods=['get'], url_path='exportar-pdf')
    def exportar_pdf(self, request):
        """
        Exportar bitácora a PDF
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Exportó bitácora a PDF",
            modulo="bitacora",
            detalles="Exportación de registros de bitácora en formato PDF"
        )
        
        # Usa tu método existente de exportación PDF
        return self._exportar_pdf(queryset, "Reporte_Bitacora")

    # ✅ EXPORTAR A EXCEL
    @action(detail=False, methods=['get'], url_path='exportar-excel')
    def exportar_excel(self, request):
        """
        Exportar bitácora a Excel
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Exportó bitácora a Excel",
            modulo="bitacora",
            detalles="Exportación de registros de bitácora en formato Excel"
        )
        
        # Usa tu método existente de exportación Excel
        return self._exportar_excel(queryset, "Reporte_Bitacora")

    # ✅ EXPORTAR A HTML
    @action(detail=False, methods=['get'], url_path='exportar-html')
    def exportar_html(self, request):
        """
        Exportar bitácora a HTML
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Exportó bitácora a HTML",
            modulo="bitacora",
            detalles="Exportación de registros de bitácora en formato HTML"
        )
        
        # Usa tu método existente de exportación HTML
        return self._exportar_html(queryset, "Reporte_Bitacora")

    # ✅ ENDPOINT PARA VER DETALLES COMPLETOS
    @action(detail=True, methods=['get'], url_path='detalle-completo')
    def detalle_completo(self, request, pk=None):
        """
        Endpoint para ver detalles completos de un registro de bitácora
        """
        registro = self.get_object()
        
        # Datos detallados del registro
        datos_detallados = {
            'id': registro.id,
            'fecha_hora': registro.fecha_hora,
            'fecha_hora_formateada': registro.fecha_hora.strftime('%d/%m/%Y %H:%M:%S'),
            'usuario': {
                'id': registro.usuario.id if registro.usuario else None,
                'email': registro.usuario.email if registro.usuario else 'N/A',
                'nombre_completo': f"{registro.usuario.nombre} {registro.usuario.apellido}" if registro.usuario else 'N/A',
                'rol': registro.usuario.id_rol.nombre_rol if registro.usuario and registro.usuario.id_rol else 'N/A'
            },
            'accion_realizada': registro.accion_realizada,
            'modulo_afectado': registro.modulo_afectado,
            'ip_address': registro.ip_address,
            'detalles': registro.detalles,
            'ubicacion_aproximada': self._get_ubicacion_aproximada(registro.ip_address),
            'navegador_info': self._extraer_info_navegador(registro)
        }
        
        return Response(datos_detallados)

    def _get_ubicacion_aproximada(self, ip):
        """Obtener ubicación aproximada basada en IP"""
        if ip in ['127.0.0.1', 'localhost']:
            return 'Localhost (Servidor Local)'
        elif ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
            return 'Red Interna'
        elif ip == '0.0.0.0':
            return 'IP No Disponible'
        else:
            return 'Red Externa'

    def _extraer_info_navegador(self, registro):
        """Extraer información del navegador si está disponible"""
        # Si tienes campo user_agent en tu modelo Bitacora
        if hasattr(registro, 'user_agent') and registro.user_agent:
            user_agent = registro.user_agent.lower()
            if 'chrome' in user_agent:
                return 'Google Chrome'
            elif 'firefox' in user_agent:
                return 'Mozilla Firefox'
            elif 'safari' in user_agent and 'chrome' not in user_agent:
                return 'Safari'
            elif 'edge' in user_agent:
                return 'Microsoft Edge'
            else:
                return 'Navegador no identificado'
        return 'No disponible'

    # ✅ MÉTODOS DE EXPORTACIÓN (ajusta según tus métodos existentes)
    def _exportar_pdf(self, queryset, nombre_archivo):
        """Método para exportar a PDF - ajusta según tu implementación existente"""
        from django.http import HttpResponse
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
        
        # Tu código de generación PDF aquí (como lo tienes en otros ViewSets)
        # ...
        
        return response

    def _exportar_excel(self, queryset, nombre_archivo):
        """Método para exportar a Excel - ajusta según tu implementación existente"""
        from django.http import HttpResponse
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
        
        # Tu código de generación Excel aquí (como lo tienes en otros ViewSets)
        # ...
        
        return response

    def _exportar_html(self, queryset, nombre_archivo):
        """Método para exportar a HTML - ajusta según tu implementación existente"""
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}_{timezone.now().strftime("%Y%m%d_%H%M")}.html"'
        
        # Tu código de generación HTML aquí (como lo tienes en otros ViewSets)
        # ...
        
        return response

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

    def perform_create(self, serializer):
        instance = serializer.save()
        medico = instance.medico_especialidad.medico
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Creó horario para médico",
            modulo="horarios",
            detalles=f"Horario {instance.dia_semana} {instance.hora_inicio}-{instance.hora_fin} para Dr. {medico.usuario.nombre} {medico.usuario.apellido}"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        medico = instance.medico_especialidad.medico
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Actualizó horario de médico",
            modulo="horarios",
            detalles=f"Horario {instance.dia_semana} {instance.hora_inicio}-{instance.hora_fin} actualizado para Dr. {medico.usuario.nombre} {medico.usuario.apellido}"
        )

    def perform_destroy(self, instance):
        medico = instance.medico_especialidad.medico
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion=f"Eliminó horario de médico",
            modulo="horarios",
            detalles=f"Horario {instance.dia_semana} {instance.hora_inicio}-{instance.hora_fin} eliminado para Dr. {medico.usuario.nombre} {medico.usuario.apellido}"
        )
        instance.delete()

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

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Agendó nueva cita",
            modulo="citas",
            detalles=f"Cita para {instance.paciente.usuario.nombre} con Dr. {instance.medico_especialidad.medico.usuario.nombre} - {instance.fecha_cita} {instance.hora_cita}"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Actualizó cita",
            modulo="citas",
            detalles=f"Cita {instance.id} actualizada - Estado: {instance.estado}"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Canceló/Eliminó cita",
            modulo="citas",
            detalles=f"Cita {instance.id} eliminada - Paciente: {instance.paciente.usuario.nombre}"
        )
        instance.delete()

    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        cita = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado not in dict(AgendaCita.ESTADO_CHOICES):
            return Response(
                {'detail': 'Estado inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        estado_anterior = cita.estado
        cita.estado = nuevo_estado
        cita.save()
        
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Cambió estado de cita",
            modulo="citas",
            detalles=f"Cita {cita.id} cambió de {estado_anterior} a {nuevo_estado}"
        )
        
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

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Creó historia clínica",
            modulo="historias_clinicas",
            detalles=f"Historia clínica creada para {instance.paciente.usuario.nombre}"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Actualizó historia clínica",
            modulo="historias_clinicas",
            detalles=f"Historia clínica {instance.id} actualizada"
        )

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

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Registró nueva consulta",
            modulo="consultas",
            detalles=f"Consulta para {instance.historia_clinica.paciente.usuario.nombre} - Motivo: {instance.motivo_consulta[:50]}..."
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Actualizó consulta",
            modulo="consultas",
            detalles=f"Consulta {instance.id} actualizada"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Eliminó consulta",
            modulo="consultas",
            detalles=f"Consulta {instance.id} eliminada"
        )
        instance.delete()

class RegistroBackupViewSet(viewsets.ModelViewSet):
    queryset = RegistroBackup.objects.select_related('usuario_responsable').all().order_by('-fecha_backup')
    serializer_class = RegistroBackupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo_backup', 'estado', 'usuario_responsable']
    search_fields = ['nombre_archivo']
    ordering_fields = ['fecha_backup']
    ordering = ['-fecha_backup']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Creó registro de backup",
            modulo="backups",
            detalles=f"Backup {instance.nombre_archivo} - Tipo: {instance.tipo_backup}"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Actualizó registro de backup",
            modulo="backups",
            detalles=f"Backup {instance.nombre_archivo} actualizado"
        )

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
        
        # Registrar inicio de backup
        Bitacora.registrar_accion(
            usuario=request.user,
            request=request,
            accion="Inició proceso de backup",
            modulo="backups",
            detalles=f"Backup {backup.nombre_archivo} iniciado"
        )
        
        # Simular proceso de backup
        backup.estado = 'Exitoso'
        backup.tamano_bytes = 1024000  # 1MB simulado
        backup.save()
        
        # Registrar finalización de backup
        Bitacora.registrar_accion(
            usuario=request.user,
            request=request,
            accion="Completó proceso de backup",
            modulo="backups",
            detalles=f"Backup {backup.nombre_archivo} completado exitosamente"
        )
        
        return Response({
            'detail': 'Backup realizado exitosamente.',
            'backup': RegistroBackupSerializer(backup).data
        })

class MedicoEspecialidadSelectView(generics.ListAPIView):
    """
    Endpoint para select de MedicoEspecialidad - sin paginación
    Filtrable por médico y especialidad
    """
    serializer_class = MedicoEspecialidadSelectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = MedicoEspecialidad.objects.select_related(
            'medico__usuario', 
            'especialidad'
        ).filter(
            medico__usuario__activo=True,
            medico__estado='Activo'
        ).order_by('medico__usuario__nombre', 'medico__usuario__apellido', 'especialidad__nombre')
        
        # Filtro por médico (id del médico)
        medico_id = self.request.query_params.get('medico_id', None)
        if medico_id:
            queryset = queryset.filter(medico__usuario__id=medico_id)
        
        # Filtro por especialidad (id de especialidad)
        especialidad_id = self.request.query_params.get('especialidad_id', None)
        if especialidad_id:
            queryset = queryset.filter(especialidad__id=especialidad_id)
        
        # Búsqueda por nombre de médico o especialidad
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(medico__usuario__nombre__icontains=search) |
                Q(medico__usuario__apellido__icontains=search) |
                Q(especialidad__nombre__icontains=search) |
                Q(especialidad__codigo__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Deshabilitar paginación
        self.pagination_class = None
        return super().list(request, *args, **kwargs)

#-----------------Prueba-------
class AutoViewSet(viewsets.ModelViewSet):
    queryset = Auto.objects.all().order_by('-id')
    serializer_class = AutoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['marca', 'modelo']
    search_fields = ['marca', 'modelo']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Creó auto",
            modulo="autos",
            detalles=f"Auto {instance.marca} {instance.modelo} creado"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        # Registrar en bitácora
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Actualizó auto",
            modulo="autos",
            detalles=f"Auto {instance.marca} {instance.modelo} actualizado"
        )

    def perform_destroy(self, instance):
        # Registrar en bitácora antes de eliminar
        Bitacora.registrar_accion(
            usuario=self.request.user,
            request=self.request,
            accion="Eliminó auto",
            modulo="autos",
            detalles=f"Auto {instance.marca} {instance.modelo} eliminado"
        )
        instance.delete()