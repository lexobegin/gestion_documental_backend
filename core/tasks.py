# core/tasks.py
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import RegistroBackup, Bitacora, Usuario
import os
import subprocess
import platform
from datetime import timedelta

@shared_task
def realizar_backup_automatico():
    """
    Tarea Celery para realizar backup automático - Funciona en Windows y Linux
    """
    try:
        admin_user = Usuario.objects.filter(is_superuser=True).first()
        
        # Crear directorio si no existe
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Nombre del archivo
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_auto_{timestamp}.sql"
        filepath = os.path.join(backup_dir, filename)
        
        # Configuración de la base de datos
        db_settings = settings.DATABASES['default']
        
        # DETECCIÓN AUTOMÁTICA DE PLATAFORMA Y RUTAS
        sistema_operativo = platform.system()
        
        if sistema_operativo == 'Windows':
            # Rutas para Windows
            pg_dump_path = r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe'
            # Verificar existencia en Windows
            if not os.path.exists(pg_dump_path):
                # Intentar detectar automáticamente en Windows
                pg_dump_path = _encontrar_pg_dump_windows()
        else:
            # Linux/Ubuntu - pg_dump normalmente está en el PATH
            pg_dump_path = 'pg_dump'
        
        # VERIFICACIÓN FINAL DE pg_dump
        if sistema_operativo != 'Windows':
            # En Linux, verificar si pg_dump está en el PATH
            from shutil import which
            pg_dump_path = which('pg_dump')
            
            if not pg_dump_path or not os.path.exists(pg_dump_path):
                # Intentar rutas comunes manualmente
                rutas_linux = [
                    '/usr/bin/pg_dump',
                    '/usr/local/bin/pg_dump',
                    '/usr/lib/postgresql/16/bin/pg_dump',
                    '/usr/lib/postgresql/15/bin/pg_dump',
                    '/usr/lib/postgresql/14/bin/pg_dump',
                ]
                for ruta in rutas_linux:
                    if os.path.exists(ruta):
                        pg_dump_path = ruta
                        break
                else:
                    raise Exception('pg_dump no encontrado en el sistema')
        
        # Verificar que pg_dump existe y es ejecutable
        if not os.path.exists(pg_dump_path):
            raise Exception(f'Herramienta de backup no encontrada en: {pg_dump_path}')
        
        # Comando para pg_dump (compatible con ambos sistemas)
        cmd = [
            pg_dump_path,
            '-h', db_settings.get('HOST', 'localhost'),
            '-p', db_settings.get('PORT', '5432'),
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-f', filepath,
            '-w',  # No pedir password
            '--no-password'  # Asegurar que no pida password interactivo
        ]
        
        # Configurar variables de entorno
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        # Para Linux, asegurar el locale
        if sistema_operativo != 'Windows':
            env['PGCLIENTENCODING'] = 'UTF-8'
            env['LANG'] = 'en_US.UTF-8'
        
        # Ejecutar backup
        result = subprocess.run(
            cmd, 
            env=env, 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5 minutos timeout
            shell=False
        )
        
        if result.returncode == 0 and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            
            # Crear registro en la base de datos
            backup = RegistroBackup.objects.create(
                nombre_archivo=filename,
                tamano_bytes=file_size,
                usuario_responsable=admin_user,
                tipo_backup='Completo',
                estado='Exitoso',
                ubicacion_almacenamiento=filepath,
                notas='Backup automático programado'
            )
            
            # Registrar en bitácora
            if admin_user:
                Bitacora.objects.create(
                    usuario=admin_user,
                    ip_address='0.0.0.0',
                    accion_realizada='Backup automático ejecutado',
                    modulo_afectado='Backup/Restore',
                    detalles=f'Backup automático exitoso: {filename} - Tamaño: {round(file_size / (1024 * 1024), 2)} MB - SO: {sistema_operativo}'
                )
            
            # Limpieza automática
            realizar_limpieza_backups.delay()
            
            return f'Backup automático exitoso: {filename} - SO: {sistema_operativo}'
        else:
            raise Exception(f"Error en pg_dump: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        error_msg = "Timeout: El backup tardó más de 5 minutos"
        _registrar_error_backup(admin_user, error_msg)
        raise Exception(error_msg)
        
    except Exception as e:
        error_msg = f"Error en backup automático: {str(e)}"
        _registrar_error_backup(admin_user, error_msg)
        raise e

def _encontrar_pg_dump_windows():
    """Buscar pg_dump automáticamente en Windows"""
    rutas_posibles = [
        r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe',
        r'C:\Program Files\PostgreSQL\15\bin\pg_dump.exe',
        r'C:\Program Files\PostgreSQL\14\bin\pg_dump.exe',
        r'C:\Program Files\PostgreSQL\13\bin\pg_dump.exe',
    ]
    
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta
    
    # Si no se encuentra, devolver la ruta por defecto
    return r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe'

def _registrar_error_backup(admin_user, error_msg):
    """Registrar error en bitácora"""
    if admin_user:
        Bitacora.objects.create(
            usuario=admin_user,
            ip_address='0.0.0.0',
            accion_realizada='Error en backup automático',
            modulo_afectado='Backup/Restore',
            detalles=error_msg
        )

@shared_task
def realizar_limpieza_backups():
    """
    Limpiar backups antiguos (mantener solo los últimos 7 días) - Universal
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=7)
        
        # Eliminar registros de backups antiguos
        backups_antiguos = RegistroBackup.objects.filter(
            fecha_backup__lt=cutoff_date
        )
        
        count = backups_antiguos.count()
        
        if count > 0:
            # Eliminar archivos físicos
            for backup in backups_antiguos:
                if os.path.exists(backup.ubicacion_almacenamiento):
                    try:
                        os.remove(backup.ubicacion_almacenamiento)
                        print(f"Archivo eliminado: {backup.ubicacion_almacenamiento}")
                    except Exception as e:
                        print(f"Error eliminando archivo: {str(e)}")
            
            backups_antiguos.delete()
            return f'Limpieza completada: {count} backups antiguos eliminados'
        
        return 'No hay backups antiguos para limpiar'
        
    except Exception as e:
        print(f"Error en limpieza de backups: {str(e)}")
        return f"Error en limpieza: {str(e)}"