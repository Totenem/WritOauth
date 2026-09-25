import re
import secrets
from typing import Callable

# Excludes 0/O and 1/I - a teacher reads this code aloud or types it from a
# printout, and those pairs are the ones people actually mistype.
_SUFFIX_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_SUFFIX_LENGTH = 4
_MAX_ATTEMPTS = 25


def _slug(name: str) -> str:
    letters = re.sub(r"[^A-Za-z0-9]", "", name).upper()
    return letters[:6] or "COURSE"


def generate_course_code(name: str, exists: Callable[[str], bool]) -> str:
    """A short, unique, human-shareable code derived from a subject's name.

    `exists` is called with each candidate and should return True if that
    code is already taken (by any subject, not just this teacher's - codes
    are globally unique so a batch upload can't ambiguously target two
    different teachers' courses).
    """
    prefix = _slug(name)
    for _ in range(_MAX_ATTEMPTS):
        suffix = "".join(
            secrets.choice(_SUFFIX_ALPHABET) for _ in range(_SUFFIX_LENGTH)
        )
        candidate = f"{prefix}-{suffix}"
        if not exists(candidate):
            return candidate
    raise RuntimeError("Could not generate a unique course code")
