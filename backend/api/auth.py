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
import bcrypt
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple
try:
    from db import get_connection, get_engine, get_sqlite_path
except ImportError:
    from backend.db import get_connection, get_engine, get_sqlite_path

logger = logging.getLogger(__name__)


class AuthManager:
    """Gestiona autenticación y autorización"""

    def __init__(self, db_path: Optional[str] = None):
        if get_engine() == 'mysql':
            self.db_path = None
            logger.info("AuthManager usando base de datos: MySQL")
        else:
            if db_path is None:
                project_root = Path(__file__).parent.parent.parent
                db_path = get_sqlite_path(str(project_root / 'data' / 'notas_credito.db'))
            self.db_path = db_path
            logger.info(f"AuthManager usando base de datos: {db_path}")
        self._inicializar_tablas()

    def _inicializar_tablas(self):
        """Inicializa tablas de autenticación"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        if get_engine(self.db_path) == 'mysql':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    email VARCHAR(255),
                    rol VARCHAR(20) DEFAULT 'viewer',
                    activo INT DEFAULT 1,
                    intentos_fallidos INT DEFAULT 0,
                    bloqueado_hasta TIMESTAMP NULL,
                    ultimo_acceso TIMESTAMP NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sesiones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token_jti VARCHAR(255) NOT NULL UNIQUE,
                    refresh_jti VARCHAR(255) UNIQUE,
                    ip_address VARCHAR(100),
                    user_agent TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_expiracion TIMESTAMP NULL,
                    activa INT DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intentos_login (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    ip_address VARCHAR(100),
                    exitoso INT NOT NULL,
                    razon_fallo TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios_2fa (
                    user_id INT PRIMARY KEY,
                    secreto VARCHAR(255) NOT NULL,
                    habilitado INT DEFAULT 0,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
        else:
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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios_2fa (
                    user_id INTEGER PRIMARY KEY,
                    secreto TEXT NOT NULL,
                    habilitado INTEGER DEFAULT 0,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                )
            ''')

        if get_engine(self.db_path) == 'mysql':
            def _create_index(name: str, table: str, columns: str):
                try:
                    cursor.execute(f"CREATE INDEX {name} ON {table}({columns})")
                except Exception:
                    pass
            _create_index('idx_sesiones_user', 'sesiones', 'user_id')
            _create_index('idx_sesiones_jti', 'sesiones', 'token_jti')
            _create_index('idx_intentos_ip', 'intentos_login', 'ip_address, fecha')
            _create_index('idx_intentos_user', 'intentos_login', 'username, fecha')
        else:
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
        conn = get_connection(self.db_path)
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
        conn = get_connection(self.db_path)
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

        if isinstance(row, dict):
            bloqueado_hasta_value = row.get('bloqueado_hasta')
            intentos = row.get('intentos_fallidos')
        else:
            bloqueado_hasta_value, intentos = row

        if bloqueado_hasta_value:
            if isinstance(bloqueado_hasta_value, datetime):
                bloqueado_hasta = bloqueado_hasta_value
            else:
                bloqueado_hasta = datetime.fromisoformat(str(bloqueado_hasta_value))
            if datetime.now() < bloqueado_hasta:
                return True, bloqueado_hasta
            else:
                # Desbloquear usuario
                self._desbloquear_usuario(username)

        return False, None

    def _desbloquear_usuario(self, username: str):
        """Desbloquea un usuario y resetea intentos fallidos"""
        conn = get_connection(self.db_path)
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
        conn = get_connection(self.db_path)
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

        if isinstance(row, dict):
            user_id = row.get('id')
            username_db = row.get('username')
            password_hash = row.get('password_hash')
            email = row.get('email')
            rol = row.get('rol')
            activo = row.get('activo')
        else:
            user_id, username_db, password_hash, email, rol, activo = row

        if not activo:
            self._registrar_intento(username, ip_address, False, "Usuario inactivo")
            return False, None, "Usuario inactivo"

        # Verificar contraseña
        if isinstance(password_hash, bytes):
            hash_bytes = password_hash
        else:
            hash_bytes = str(password_hash or '').encode('utf-8')

        if not bcrypt.checkpw(password.encode('utf-8'), hash_bytes):
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
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO intentos_login (username, ip_address, exitoso, razon_fallo)
            VALUES (?, ?, ?, ?)
        ''', (username, ip_address, 1 if exitoso else 0, razon_fallo))

        conn.commit()
        conn.close()

    def _incrementar_intentos_fallidos(self, username: str, max_intentos: int = 5):
        """Incrementa contador de intentos fallidos y bloquea si es necesario"""
        conn = get_connection(self.db_path)
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
        conn = get_connection(self.db_path)
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
        conn = get_connection(self.db_path)
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
        conn = get_connection(self.db_path)
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
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sesiones
            SET activa = 0
            WHERE token_jti = ? OR refresh_jti = ?
        ''', (token_jti, token_jti))

        conn.commit()
        conn.close()
        return True

    def invalidar_sesiones_usuario(self, user_id: int) -> bool:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE sesiones SET activa = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al invalidar sesiones: {e}")
            return False
        finally:
            conn.close()

    def verificar_sesion_activa(self, token_jti: str) -> bool:
        """Verifica si una sesión está activa"""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT activa, fecha_expiracion
            FROM sesiones
            WHERE token_jti = ? OR refresh_jti = ?
        ''', (token_jti, token_jti))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        if isinstance(row, dict):
            activa = row.get('activa')
            fecha_exp_str = row.get('fecha_expiracion')
        else:
            activa = row[0] if len(row) > 0 else 0
            fecha_exp_str = row[1] if len(row) > 1 else None

        if not activa:
            return False

        if not fecha_exp_str:
            return False

        try:
            fecha_exp = datetime.fromisoformat(str(fecha_exp_str))
        except ValueError:
            logger.warning(f"Formato inválido de fecha_expiracion para sesión {token_jti}: {fecha_exp_str}")
            return False

        if datetime.now() > fecha_exp:
            return False

        return True

    def obtener_2fa(self, user_id: int) -> Optional[Dict]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT secreto, habilitado FROM usuarios_2fa WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'secreto': row['secreto'] if isinstance(row, dict) else row[0],
                'habilitado': (row['habilitado'] if isinstance(row, dict) else row[1]) == 1
            }
        finally:
            conn.close()

    def guardar_2fa(self, user_id: int, secreto: str, habilitado: bool = False) -> bool:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT user_id FROM usuarios_2fa WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone() is not None
            if exists:
                cursor.execute(
                    'UPDATE usuarios_2fa SET secreto = ?, habilitado = ? WHERE user_id = ?',
                    (secreto, 1 if habilitado else 0, user_id)
                )
            else:
                cursor.execute(
                    'INSERT INTO usuarios_2fa (user_id, secreto, habilitado) VALUES (?, ?, ?)',
                    (user_id, secreto, 1 if habilitado else 0)
                )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al guardar 2FA: {e}")
            return False
        finally:
            conn.close()

    def actualizar_2fa(self, user_id: int, habilitado: bool) -> bool:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE usuarios_2fa SET habilitado = ? WHERE user_id = ?', (1 if habilitado else 0, user_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar 2FA: {e}")
            return False
        finally:
            conn.close()

    def cambiar_contraseña(self, username: str, nueva_contraseña: str) -> bool:
        """Cambia la contraseña de un usuario"""
        conn = get_connection(self.db_path)
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
        conn = get_connection(self.db_path)
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
