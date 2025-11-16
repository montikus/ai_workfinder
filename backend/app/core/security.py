from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import ustawienia

# Вместо bcrypt/bcrypt_sha256 используем pbkdf2_sha256
# У него нет ограничения 72 байта, проблем с длиной пароля не будет.
kontekst_hasla = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def haszuj_haslo(haslo: str) -> str:
    """Zwraca zahaszowane hasło."""
    return kontekst_hasla.hash(haslo)


def sprawdz_haslo(haslo: str, haslo_zahaszowane: str) -> bool:
    """Sprawdza, czy podane hasło pasuje do zahaszowanego."""
    return kontekst_hasla.verify(haslo, haslo_zahaszowane)


def utworz_token_dostepu(dane: dict, expires_delta: timedelta | None = None) -> str:
    """Tworzy JWT na podstawie danych użytkownika."""
    to_encode = dane.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=ustawienia.jwt_expire_minutes)
    wygasa = datetime.utcnow() + expires_delta
    to_encode.update({"exp": wygasa})
    token = jwt.encode(
        to_encode,
        ustawienia.jwt_secret_key,
        algorithm=ustawienia.jwt_algorithm,
    )
    return token


def zweryfikuj_token(token: str) -> dict | None:
    """Zwraca payload JWT lub None, jeśli token jest nieprawidłowy / wygasł."""
    try:
        payload = jwt.decode(
            token,
            ustawienia.jwt_secret_key,
            algorithms=[ustawienia.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None
