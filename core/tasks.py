from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import RegistroBackup
import os
import subprocess
from django.conf import settings
import platform

@shared_task(bind=True)
def realizar_backup_automatico(self):
    """Tarea para realizar backup automático - Multiplataforma"""
    try:
        # Crear directorio de backups si no existe
        backup_dir = 'backups/automaticos'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Nombre del archivo
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_auto_{timestamp}.sql"
        filepath = os.path.join(backup_dir, filename)
        
        # Usuario administrador para el registro
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Crear registro
        backup = RegistroBackup.objects.create(
            nombre_archivo=filename,
            usuario_responsable=admin_user,
            tipo_backup='Completo',
            estado='En Progreso',
            ubicacion_almacenamiento=filepath,
            notas='Backup automático programado'
        )
        
        # Detectar plataforma
        sistema_operativo = platform.system()
        
        if sistema_operativo == 'Windows':
            pg_dump_path = r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe'
        else:
            # Linux/Ubuntu
            pg_dump_path = 'pg_dump'
            # Verificar si existe en el PATH
            which_result = subprocess.run(['which', 'pg_dump'], capture_output=True, text=True)
            if which_result.returncode != 0:
                # Intentar rutas comunes en Linux
                rutas_linux = [
                    '/usr/bin/pg_dump',
                    '/usr/local/bin/pg_dump',
                    '/usr/lib/postgresql/16/bin/pg_dump',
                    '/usr/lib/postgresql/15/bin/pg_dump',
                ]
                for ruta in rutas_linux:
                    if os.path.exists(ruta):
                        pg_dump_path = ruta
                        break
        
        # Realizar backup
        db_settings = settings.DATABASES['default']
        cmd = [
            pg_dump_path,
            '-h', db_settings.get('HOST', 'localhost'),
            '-p', db_settings.get('PORT', '5432'),
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-f', filepath,
            '-w',
            '--no-password'
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        # Para Linux
        if sistema_operativo != 'Windows':
            env['PGCLIENTENCODING'] = 'UTF-8'
            env['LANG'] = 'en_US.UTF-8'
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            backup.estado = 'Exitoso'
            backup.tamano_bytes = file_size
            backup.save()
            
            # Limpiar backups antiguos (mantener solo los últimos 7 días)
            self._limpiar_backups_antiguos(backup_dir)
            
            return {
                'status': 'success',
                'message': f'Backup automático exitoso: {filename}',
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'backup_id': backup.id
            }
        else:
            backup.estado = 'Fallido'
            backup.notas = f"Error: {result.stderr}"
            backup.save()
            return {
                'status': 'error',
                'message': f'Error en backup automático: {result.stderr}',
                'backup_id': backup.id
            }
            
    except subprocess.TimeoutExpired:
        backup.estado = 'Fallido'
        backup.notas = "Timeout: El backup tardó más de 5 minutos"
        backup.save()
        return {
            'status': 'error',
            'message': 'Timeout en backup automático'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error inesperado en backup automático: {str(e)}'
        }

def _limpiar_backups_antiguos(self, backup_dir, dias_retencion=7):
    """Eliminar backups más antiguos que los días de retención"""
    from datetime import datetime, timedelta
    
    try:
        fecha_limite = datetime.now() - timedelta(days=dias_retencion)
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_auto_') and filename.endswith('.sql'):
                filepath = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if file_time < fecha_limite:
                    os.remove(filepath)
                    print(f"Backup antiguo eliminado: {filename}")
    except Exception as e:
        print(f"Error limpiando backups antiguos: {str(e)}")