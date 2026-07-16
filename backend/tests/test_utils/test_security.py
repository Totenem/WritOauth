from utils.security import hash_password, verify_password


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
