from django.contrib import admin
from .models import Usuario, Medico, Paciente, Administrador, Especialidad, Auto, Rol, MedicoEspecialidad, Permiso

admin.site.register(Usuario)
admin.site.register(Medico)
admin.site.register(Paciente)
admin.site.register(Administrador)
admin.site.register(Especialidad)
admin.site.register(Auto)
admin.site.register(Permiso)
admin.site.register(Rol)
admin.site.register(MedicoEspecialidad)
# Register your models here.
