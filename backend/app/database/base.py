from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def pg_enum(enum_cls):
    """Enum column type that stores the enum *value* rather than the member name.

    This matches the lowercase PostgreSQL enum types created by Alembic
    (e.g. ``other`` instead of ``OTHER``).
    """
    return SAEnum(enum_cls, values_callable=lambda cls: [member.value for member in cls])
