import os
from celery import Celery
from django.conf import settings

# Establecer la configuración de Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_documental_backend.settings')

app = Celery('gestion_documental_backend')

# Usar la configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas de todas las apps instaladas
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')