from datetime import timedelta

import pytest

from utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_does_not_return_plaintext() -> None:
    assert hash_password("x") != "x"


def test_hash_password_is_salted() -> None:
    assert hash_password("x") != hash_password("x")


def test_verify_password_succeeds_for_correct_password() -> None:
    assert verify_password("x", hash_password("x")) is True


def test_verify_password_fails_for_incorrect_password() -> None:
    assert verify_password("y", hash_password("x")) is False


def test_hash_password_handles_empty_string() -> None:
    hashed = hash_password("")
    assert hashed != ""
    assert verify_password("", hashed) is True
    assert verify_password("not-empty", hashed) is False


def test_create_and_decode_access_token_round_trip() -> None:
    token = create_access_token({"sub": "teacher@example.com"})
    claims = decode_access_token(token)

    assert claims["sub"] == "teacher@example.com"
    assert "exp" in claims


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token(
        {"sub": "teacher@example.com"}, expires_delta=timedelta(minutes=-1)
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_decode_access_token_rejects_malformed_token() -> None:
    with pytest.raises(ValueError):
        decode_access_token("not-a-valid-token")
