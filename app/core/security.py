from datetime import datetime, timedelta, UTC

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _parse_expires_delta(expires_in: str) -> timedelta:
    unit = expires_in[-1]
    amount = int(expires_in[:-1])
    if unit == "d":
        return timedelta(days=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    return timedelta(days=7)


def create_access_token(subject: str, expires_in: str | None = None) -> str:
    expire_delta = _parse_expires_delta(expires_in or settings.expires_in)
    expire = datetime.now(UTC) + expire_delta
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
