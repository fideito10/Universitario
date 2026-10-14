"""Hash de claves con la stdlib (scrypt). Formato: scrypt$N$r$p$salt_b64$hash_b64"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os

_PREFIX = "scrypt$"
_N, _R, _P = 2 ** 14, 8, 1
_DKLEN = 32
_MAXMEM = 64 * 1024 * 1024


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def is_hash(value) -> bool:
    return isinstance(value, str) and value.startswith(_PREFIX) and value.count("$") == 5


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(str(password).encode("utf-8"), salt=salt, n=_N, r=_R, p=_P,
                        dklen=_DKLEN, maxmem=_MAXMEM)
    return f"{_PREFIX}{_N}${_R}${_P}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    """True si `password` corresponde al hash `stored`. Nunca lanza."""
    try:
        _, n, r, p, salt_b64, hash_b64 = str(stored).split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.scrypt(str(password).encode("utf-8"), salt=salt, n=int(n), r=int(r),
                            p=int(p), dklen=len(expected), maxmem=_MAXMEM)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def equals_plain(a: str, b: str) -> bool:
    """Comparacion en tiempo constante de dos claves en texto."""
    return hmac.compare_digest(str(a).encode("utf-8"), str(b).encode("utf-8"))
