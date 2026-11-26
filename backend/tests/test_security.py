"""Authentication primitives: hashing and token issue must behave as documented."""

import jwt

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password


def test_a_password_is_never_stored_in_clear():
    stored = hash_password("CorrectHorse9")
    assert stored != "CorrectHorse9"
    assert stored.startswith("$2")


def test_the_right_password_verifies_and_the_wrong_one_does_not():
    stored = hash_password("CorrectHorse9")
    assert verify_password("CorrectHorse9", stored) is True
    assert verify_password("correcthorse9", stored) is False
    assert verify_password("", stored) is False


def test_the_same_password_hashes_differently_each_time():
    first = hash_password("CorrectHorse9")
    second = hash_password("CorrectHorse9")
    assert first != second


def test_a_token_carries_the_user_id_and_expires():
    token, expires_in = create_access_token("user-123")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "user-123"
    assert "exp" in payload
    assert expires_in == settings.jwt_expire_minutes * 60


def test_a_token_signed_with_another_secret_is_rejected():
    forged = jwt.encode({"sub": "someone-else"}, "not-the-app-secret", algorithm="HS256")
    try:
        jwt.decode(forged, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidSignatureError:
        return
    raise AssertionError("a token signed with the wrong secret was accepted")