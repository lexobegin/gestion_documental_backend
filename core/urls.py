from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

router = DefaultRouter()

router.register(r'usuarios', UsuarioViewSet)
router.register(r'pacientes', PacienteViewSet)  # AHORA CON CRUD COMPLETO
router.register(r'medicos', MedicoViewSet)
router.register(r'administradores', AdministradorViewSet)
router.register(r'roles', RolViewSet)
router.register(r'permisos', PermisoViewSet)
router.register(r'especialidades', EspecialidadViewSet)

# Nuevos routers para Sprint 2
router.register(r'tipos-componente', TipoComponenteViewSet)
router.register(r'componentes-ui', ComponenteUIViewSet)
router.register(r'permisos-componentes', PermisoComponenteViewSet)

router.register(r'bitacora', BitacoraViewSet)
router.register(r'horarios-medico', HorarioMedicoViewSet)
router.register(r'agenda-citas', AgendaCitaViewSet)
router.register(r'historias-clinicas', HistoriaClinicaViewSet)
router.register(r'consultas', ConsultaViewSet)
router.register(r'backups', RegistroBackupViewSet)

#---prueba---
router.register(r'autos', AutoViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # Registro (Movil)
    path('registro/paciente/', RegistroPacienteView.as_view(), name='registro-paciente'),

    # ENDPOINTS PERSONALIZADOS DE AUTENTICACIÓN
    path('login/', login_personalizado, name='login_personalizado'),
    path('logout/', logout_personalizado, name='logout_personalizado'),

    # Endpoints JWT (mantenidos por compatibilidad)
    path('token/', login_personalizado, name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Perfil (Web/Movil)
    path('mi-perfil/', MiPerfilView.as_view(), name='mi-perfil'),

    # ENDPOINTS PARA SELECTS
    path('select/pacientes/', PacienteSelectView.as_view(), name='select-pacientes'),
    path('select/medicos/', MedicoSelectView.as_view(), name='select-medicos'),
    path('select/medico-especialidades/', MedicoEspecialidadSelectView.as_view(), name='select-medico-especialidades'),

    # NUEVOS ENDPOINTS PARA GESTIÓN AVANZADA DE PACIENTES
    path('pacientes/busqueda-avanzada/', PacienteBusquedaAvanzadaView.as_view(), name='pacientes-busqueda-avanzada'),
    
    # ENDPOINTS PARA HORARIOS DISPONIBLES
    path('horarios-disponibles/mi-horario/', HorariosDisponiblesMedicoLogueadoView.as_view(), name='mis-horarios-disponibles'),
    path('horarios-disponibles/', HorariosDisponiblesPorMedicoEspecialidadView.as_view(), name='horarios-disponibles'),
    
]

# URLs AUTOMÁTICAS DE CONSULTAVIEWSET MEJORADO (CRUD COMPLETO + NUEVOS ENDPOINTS)
# /consultas/ - GET (listar), POST (crear)
# /consultas/{id}/ - GET (detalle), PUT (actualizar), PATCH (actualización parcial), DELETE (eliminar)
# /consultas/por-cita/{cita_id}/ - GET (consulta por cita)
# /consultas/por-paciente/{paciente_id}/ - GET (historial de paciente)
# /consultas/hoy/ - GET (consultas del día para médico)
# /consultas/crear-desde-cita/ - POST (crear desde cita existente)
# /consultas/estadisticas/ - GET (estadísticas de consultas)