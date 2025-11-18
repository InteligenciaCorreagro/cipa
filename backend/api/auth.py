"""
Módulo de autenticación con seguridad reforzada

Características:
- Hash bcrypt para contraseñas
- JWT con refresh tokens
- Rate limiting por IP
- Registro de intentos fallidos
- Bloqueo temporal después de intentos fallidos
"""

import os
import sqlite3
import bcrypt
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class AuthManager:
    """Gestiona autenticación y autorización"""

    def __init__(self, db_path: str = None):
        # Si no se proporciona db_path, usar variable de entorno o calcular ruta al proyecto raíz
        if db_path is None:
            # Intentar obtener desde variable de entorno
            db_path = os.getenv('DB_PATH')
            if db_path is None:
                # Calcular ruta al directorio raíz del proyecto
                # auth.py está en backend/api/, necesitamos subir 2 niveles
                project_root = Path(__file__).parent.parent.parent
                db_path = str(project_root / 'data' / 'notas_credito.db')

        self.db_path = db_path
        logger.info(f"AuthManager usando base de datos: {db_path}")
        self._inicializar_tablas()

    def _inicializar_tablas(self):
        """Inicializa tablas de autenticación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                email TEXT,
                rol TEXT DEFAULT 'viewer',
                activo INTEGER DEFAULT 1,
                intentos_fallidos INTEGER DEFAULT 0,
                bloqueado_hasta TIMESTAMP NULL,
                ultimo_acceso TIMESTAMP NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de sesiones/tokens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_jti TEXT NOT NULL UNIQUE,
                refresh_jti TEXT UNIQUE,
                ip_address TEXT,
                user_agent TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_expiracion TIMESTAMP NOT NULL,
                activa INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        ''')

        # Tabla de intentos de login
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intentos_login (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ip_address TEXT,
                exitoso INTEGER NOT NULL,
                razon_fallo TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sesiones_user ON sesiones(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sesiones_jti ON sesiones(token_jti)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_intentos_ip ON intentos_login(ip_address, fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_intentos_user ON intentos_login(username, fecha)')

        # Crear usuario admin por defecto si no existe
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO usuarios (username, password_hash, email, rol)
                VALUES (?, ?, ?, ?)
            ''', ('admin', password_hash.decode('utf-8'), 'admin@cipa.com', 'admin'))

            logger.warning("⚠️  Usuario admin creado con contraseña por defecto. CAMBIAR INMEDIATAMENTE!")

        conn.commit()
        conn.close()

    def crear_usuario(self, username: str, password: str, email: str = None, rol: str = 'viewer') -> bool:
        """
        Crea un nuevo usuario

        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano (se hashea automáticamente)
            email: Email opcional
            rol: Rol (admin, editor, viewer)

        Returns:
            True si se creó exitosamente
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Validar que el usuario no exista
            cursor.execute('SELECT id FROM usuarios WHERE username = ?', (username,))
            if cursor.fetchone():
                logger.warning(f"Intento de crear usuario duplicado: {username}")
                return False

            # Hash de contraseña
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            cursor.execute('''
                INSERT INTO usuarios (username, password_hash, email, rol)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash.decode('utf-8'), email, rol))

            conn.commit()
            logger.info(f"Usuario creado: {username} con rol {rol}")
            return True

        except Exception as e:
            logger.error(f"Error al crear usuario: {e}")
            return False
        finally:
            conn.close()

    def verificar_usuario_bloqueado(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """
        Verifica si un usuario está bloqueado temporalmente

        Returns:
            (bloqueado: bool, bloqueado_hasta: datetime)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT bloqueado_hasta, intentos_fallidos
            FROM usuarios
            WHERE username = ?
        ''', (username,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, None

        bloqueado_hasta_str, intentos = row

        if bloqueado_hasta_str:
            bloqueado_hasta = datetime.fromisoformat(bloqueado_hasta_str)
            if datetime.now() < bloqueado_hasta:
                return True, bloqueado_hasta
            else:
                # Desbloquear usuario
                self._desbloquear_usuario(username)

        return False, None

    def _desbloquear_usuario(self, username: str):
        """Desbloquea un usuario y resetea intentos fallidos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE usuarios
            SET bloqueado_hasta = NULL,
                intentos_fallidos = 0
            WHERE username = ?
        ''', (username,))

        conn.commit()
        conn.close()

    def autenticar(self, username: str, password: str, ip_address: str = None) -> Tuple[bool, Optional[Dict], str]:
        """
        Autentica un usuario

        Args:
            username: Nombre de usuario
            password: Contraseña
            ip_address: IP del cliente

        Returns:
            (autenticado: bool, datos_usuario: dict, mensaje: str)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verificar bloqueo
        bloqueado, bloqueado_hasta = self.verificar_usuario_bloqueado(username)
        if bloqueado:
            msg = f"Usuario bloqueado hasta {bloqueado_hasta.strftime('%Y-%m-%d %H:%M:%S')}"
            self._registrar_intento(username, ip_address, False, msg)
            return False, None, msg

        # Buscar usuario
        cursor.execute('''
            SELECT id, username, password_hash, email, rol, activo
            FROM usuarios
            WHERE username = ?
        ''', (username,))

        row = cursor.fetchone()

        if not row:
            self._registrar_intento(username, ip_address, False, "Usuario no existe")
            return False, None, "Credenciales inválidas"

        user_id, username_db, password_hash, email, rol, activo = row

        if not activo:
            self._registrar_intento(username, ip_address, False, "Usuario inactivo")
            return False, None, "Usuario inactivo"

        # Verificar contraseña
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            # Incrementar intentos fallidos
            self._incrementar_intentos_fallidos(username)
            self._registrar_intento(username, ip_address, False, "Contraseña incorrecta")
            return False, None, "Credenciales inválidas"

        # Autenticación exitosa
        self._resetear_intentos_fallidos(username)
        self._registrar_intento(username, ip_address, True, None)
        self._actualizar_ultimo_acceso(username)

        usuario = {
            'id': user_id,
            'username': username_db,
            'email': email,
            'rol': rol
        }

        conn.close()
        return True, usuario, "Autenticación exitosa"

    def _registrar_intento(self, username: str, ip_address: str, exitoso: bool, razon_fallo: str = None):
        """Registra un intento de login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO intentos_login (username, ip_address, exitoso, razon_fallo)
            VALUES (?, ?, ?, ?)
        ''', (username, ip_address, 1 if exitoso else 0, razon_fallo))

        conn.commit()
        conn.close()

    def _incrementar_intentos_fallidos(self, username: str, max_intentos: int = 5):
        """Incrementa contador de intentos fallidos y bloquea si es necesario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE usuarios
            SET intentos_fallidos = intentos_fallidos + 1
            WHERE username = ?
        ''', (username,))

        cursor.execute('SELECT intentos_fallidos FROM usuarios WHERE username = ?', (username,))
        intentos = cursor.fetchone()[0]

        # Bloquear si excede intentos
        if intentos >= max_intentos:
            bloqueado_hasta = datetime.now() + timedelta(minutes=15)
            cursor.execute('''
                UPDATE usuarios
                SET bloqueado_hasta = ?
                WHERE username = ?
            ''', (bloqueado_hasta.isoformat(), username))

            logger.warning(f"Usuario {username} bloqueado hasta {bloqueado_hasta} por exceso de intentos")

        conn.commit()
        conn.close()

    def _resetear_intentos_fallidos(self, username: str):
        """Resetea el contador de intentos fallidos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE usuarios
            SET intentos_fallidos = 0,
                bloqueado_hasta = NULL
            WHERE username = ?
        ''', (username,))

        conn.commit()
        conn.close()

    def _actualizar_ultimo_acceso(self, username: str):
        """Actualiza fecha de último acceso"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE usuarios
            SET ultimo_acceso = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (username,))

        conn.commit()
        conn.close()

    def registrar_sesion(self, user_id: int, token_jti: str, refresh_jti: str,
                        ip_address: str, user_agent: str, expires_in: int = 3600) -> bool:
        """Registra una sesión JWT"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            fecha_expiracion = datetime.now() + timedelta(seconds=expires_in)

            cursor.execute('''
                INSERT INTO sesiones
                (user_id, token_jti, refresh_jti, ip_address, user_agent, fecha_expiracion)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, token_jti, refresh_jti, ip_address, user_agent,
                  fecha_expiracion.isoformat()))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error al registrar sesión: {e}")
            return False
        finally:
            conn.close()

    def invalidar_sesion(self, token_jti: str) -> bool:
        """Invalida una sesión (logout)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sesiones
            SET activa = 0
            WHERE token_jti = ?
        ''', (token_jti,))

        conn.commit()
        conn.close()
        return True

    def verificar_sesion_activa(self, token_jti: str) -> bool:
        """Verifica si una sesión está activa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT activa, fecha_expiracion
            FROM sesiones
            WHERE token_jti = ?
        ''', (token_jti,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        activa, fecha_exp_str = row

        if not activa:
            return False

        fecha_exp = datetime.fromisoformat(fecha_exp_str)
        if datetime.now() > fecha_exp:
            return False

        return True

    def cambiar_contraseña(self, username: str, nueva_contraseña: str) -> bool:
        """Cambia la contraseña de un usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            password_hash = bcrypt.hashpw(nueva_contraseña.encode('utf-8'), bcrypt.gensalt())

            cursor.execute('''
                UPDATE usuarios
                SET password_hash = ?,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE username = ?
            ''', (password_hash.decode('utf-8'), username))

            conn.commit()
            logger.info(f"Contraseña cambiada para usuario: {username}")
            return True

        except Exception as e:
            logger.error(f"Error al cambiar contraseña: {e}")
            return False
        finally:
            conn.close()

    def get_user(self, username: str) -> Optional[Dict]:
        """
        Obtiene los datos de un usuario por su username

        Args:
            username: Nombre de usuario

        Returns:
            Diccionario con datos del usuario o None si no existe
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, username, email, rol, activo
                FROM usuarios
                WHERE username = ?
            ''', (username,))

            row = cursor.fetchone()

            if not row:
                return None

            user_id, username_db, email, rol, activo = row

            return {
                'id': user_id,
                'username': username_db,
                'email': email,
                'role': rol,  # Usar 'role' en lugar de 'rol' para consistencia con JWT
                'activo': bool(activo)
            }

        except Exception as e:
            logger.error(f"Error al obtener usuario: {e}")
            return None
        finally:
            conn.close()
