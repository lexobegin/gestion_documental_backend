from django.contrib import admin
from .models import Usuario, Medico, Paciente, Administrador, Especialidad, Auto, Rol, MedicoEspecialidad, Permiso,Consulta,HistoriaClinica

admin.site.register(Usuario)
admin.site.register(Medico)
admin.site.register(Paciente)
admin.site.register(Administrador)
admin.site.register(Especialidad)
admin.site.register(Auto)
admin.site.register(Permiso)
admin.site.register(Rol)
admin.site.register(MedicoEspecialidad)

admin.site.register(Consulta)
admin.site.register(HistoriaClinica)


# Register your models here.  # ← ESTA LÍNEA DEBE ESTAR FUERA DE LA CLASE
