import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_token


def test_hash_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert len(hashed) > 20


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_decode_invalid_token():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        decode_token("not.a.valid.token")
    assert exc.value.status_code == 401
