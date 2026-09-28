"""Student-name normalization shared by every path that creates students.

Two students count as the same person when their first and last names match
for the same teacher, ignoring case and extra whitespace. The database
enforces the same rule with a unique index on
`(teacher_id, lower(first_name), lower(last_name))`, so names must also be
*stored* whitespace-collapsed - otherwise "John  Smith" and "John Smith"
would slip past the index as different strings.
"""

NameKey = tuple[str, str]


def normalize_name(value: str) -> str:
    """Trim and collapse internal runs of whitespace: " Mary   Ann " -> "Mary Ann"."""
    return " ".join(value.split())


def name_key(first_name: str, last_name: str) -> NameKey:
    """The identity used for duplicate detection.

    `lower()` rather than `casefold()` so it agrees with SQL `lower()` in
    the unique index - casefold maps e.g. "ß" to "ss", which the database
    would not.
    """
    return (normalize_name(first_name).lower(), normalize_name(last_name).lower())


def display_name(first_name: str, last_name: str) -> str:
    return f"{normalize_name(first_name)} {normalize_name(last_name)}".strip()
