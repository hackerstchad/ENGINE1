# -*- coding: utf-8 -*-
"""Module d'authentification simple par mot de passe haché."""

import hashlib
from config import DEFAULT_USERNAME, DEFAULT_PASSWORD


def _hash(value: str) -> str:
    """Hache une chaîne en SHA-256."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# Identifiants stockés sous forme hachée
_STORED_USERNAME_HASH = _hash(DEFAULT_USERNAME)
_STORED_PASSWORD_HASH = _hash(DEFAULT_PASSWORD)


def verify_credentials(username: str, password: str) -> bool:
    """Vérifie les identifiants fournis."""
    return (
        _hash(username) == _STORED_USERNAME_HASH
        and _hash(password) == _STORED_PASSWORD_HASH
    )
