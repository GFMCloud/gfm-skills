"""Checks the provider's HMAC-SHA256 signature over the raw body."""
import hashlib
import hmac
import os


def secret():
    value = os.environ.get("PAYHOOK_SECRET")
    if not value:
        raise RuntimeError("PAYHOOK_SECRET is not set")
    return value.encode()


def sign(body, key=None):
    return hmac.new(key or secret(), body, hashlib.sha256).hexdigest()


def valid(body, signature):
    return hmac.compare_digest(sign(body), signature or "")
