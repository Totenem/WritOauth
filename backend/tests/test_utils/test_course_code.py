import re

import pytest

from utils.course_code import generate_course_code


def test_code_is_prefixed_from_the_subject_name() -> None:
    code = generate_course_code("English 301: Senior Seminar", lambda _: False)

    assert re.fullmatch(r"ENGLIS-[A-Z2-9]{4}", code)


def test_suffix_avoids_ambiguous_characters() -> None:
    codes = {generate_course_code("Algebra", lambda _: False) for _ in range(200)}

    suffixes = "".join(code.split("-")[1] for code in codes)
    assert not set(suffixes) & set("01IO")


def test_retries_until_the_code_is_free() -> None:
    seen: list[str] = []

    def taken(code: str) -> bool:
        seen.append(code)
        return len(seen) < 3  # first two candidates collide

    code = generate_course_code("Algebra", taken)

    assert len(seen) == 3
    assert code == seen[-1]


def test_gives_up_rather_than_looping_forever() -> None:
    with pytest.raises(RuntimeError):
        generate_course_code("Algebra", lambda _: True)


def test_name_with_no_letters_still_gets_a_prefix() -> None:
    assert generate_course_code("!!!", lambda _: False).startswith("COURSE-")
