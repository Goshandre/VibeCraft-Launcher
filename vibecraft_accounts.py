"""Локальные профили и ранги VibeCraft.

Это локальное хранилище для одного компьютера, а не серверная система аккаунтов.
Для общей защиты ролей между пользователями нужен доверенный backend.
"""
from __future__ import annotations
import hashlib, hmac, os, secrets, sqlite3, time
from pathlib import Path

DB_PATH = Path.home() / 'VibeCraft' / 'accounts.sqlite3'
RANKS = [
    (0, 'Новичок', '🪵'),
    (5, 'Игрок', '⚔️'),
    (25, 'Профи', '💎'),
    (100, 'Задрот', '🔥'),
]
SPECIAL_ROLES = {'moderator': 'Помощник (Модератор)', 'owner': 'Владелец VibeCraft'}
ITERATIONS = 310_000

class AccountError(Exception): pass

class AccountStore:
    def __init__(self, path: Path | str = DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS users(
                username TEXT PRIMARY KEY COLLATE NOCASE,
                salt BLOB NOT NULL, password_hash BLOB NOT NULL,
                role TEXT NOT NULL DEFAULT 'player',
                play_seconds INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')

    def _db(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _password(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)

    def register(self, username: str, password: str, bootstrap_key: str | None = None):
        username = username.strip()
        if not 3 <= len(username) <= 16 or not username.replace('_','').isalnum():
            raise AccountError('Никнейм: 3–16 символов, только буквы, цифры и _.')
        if len(password) < 8:
            raise AccountError('Пароль должен содержать минимум 8 символов.')
        salt = secrets.token_bytes(16)
        digest = self._password(password, salt)
        with self._db() as db:
            if db.execute('SELECT 1 FROM users LIMIT 1').fetchone() is None:
                expected = os.environ.get('VIBECRAFT_OWNER_KEY')
                if not expected:
                    raise AccountError('Первого владельца должен настроить разработчик: задайте VIBECRAFT_OWNER_KEY и повторите регистрацию.')
                if not bootstrap_key or not hmac.compare_digest(bootstrap_key, expected):
                    raise AccountError('Неверный ключ первоначальной настройки владельца.')
                role = 'owner'
                db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('owner_created','1')")
            else:
                role = 'player'
            try:
                db.execute('INSERT INTO users(username,salt,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                           (username, salt, digest, role, int(time.time())))
            except sqlite3.IntegrityError:
                raise AccountError('Такой никнейм уже зарегистрирован.')
        return self.get_user(username)

    def authenticate(self, username: str, password: str):
        with self._db() as db:
            row = db.execute('SELECT * FROM users WHERE username=?', (username.strip(),)).fetchone()
        if not row or not hmac.compare_digest(self._password(password, row['salt']), row['password_hash']):
            raise AccountError('Неверный никнейм или пароль.')
        return self._public(row)

    @staticmethod
    def _public(row):
        hours = row['play_seconds'] / 3600
        rank = RANKS[0]
        for item in RANKS:
            if hours >= item[0]: rank = item
        role = row['role']
        title = SPECIAL_ROLES.get(role, f'{rank[2]} {rank[1]}')
        return {'username': row['username'], 'role': role, 'play_seconds': row['play_seconds'],
                'hours': hours, 'rank': title}

    def get_user(self, username: str):
        with self._db() as db:
            row = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if not row: raise AccountError('Пользователь не найден.')
        return self._public(row)

    def add_playtime(self, username: str, seconds: int):
        if seconds <= 0: return self.get_user(username)
        with self._db() as db:
            db.execute('UPDATE users SET play_seconds=play_seconds+? WHERE username=?', (int(seconds), username))
        return self.get_user(username)

    def set_special_role(self, actor: str, target: str, role: str | None):
        if role not in (None, 'moderator'):
            raise AccountError('Назначить владельца через обычную команду нельзя.')
        with self._db() as db:
            owner = db.execute('SELECT role FROM users WHERE username=?', (actor,)).fetchone()
            if not owner or owner['role'] != 'owner': raise AccountError('Только владелец может выдавать особые ранги.')
            target_row = db.execute('SELECT role FROM users WHERE username=?', (target,)).fetchone()
            if not target_row: raise AccountError('Пользователь не найден.')
            if target_row['role'] == 'owner': raise AccountError('Роль владельца нельзя снять или изменить через управление модераторами.')
            cur = db.execute('UPDATE users SET role=? WHERE username=?', (role or 'player', target))
            if not cur.rowcount: raise AccountError('Пользователь не найден.')
        return self.get_user(target)

    def can_moderate(self, username: str) -> bool:
        with self._db() as db:
            row = db.execute('SELECT role FROM users WHERE username=?', (username,)).fetchone()
        return bool(row and row['role'] in ('moderator', 'owner'))
