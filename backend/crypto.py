"""Encryption for patient name and phone, and the keyed hash used to find a phone number."""
import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from .config import settings


def encrypt(text: str) -> str:
    nonce = os.urandom(12)
    sealed = AESGCM(settings.field_key).encrypt(nonce, text.encode(), None)
    return base64.b64encode(nonce + sealed).decode()


def decrypt(token: str) -> str:
    raw = base64.b64decode(token)
    return AESGCM(settings.field_key).decrypt(raw[:12], raw[12:], None).decode()


def phone_hash(phone: str) -> str:
    """The same number always gives the same hash, so a phone can be matched without decrypting."""
    # ponytail: keeps the last 10 digits, which fits Indian numbers with or without +91.
    # Store a full E.164 number instead if patients from other countries are registered.
    digits = "".join(c for c in phone if c.isdigit())[-10:]
    return hmac.new(settings.hash_key, digits.encode(), hashlib.sha256).hexdigest()


class EncryptedStr(TypeDecorator):
    """A text column stored AES-256-GCM encrypted. Code reads and writes plain text."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else encrypt(value)

    def process_result_value(self, value, dialect):
        return None if value is None else decrypt(value)
