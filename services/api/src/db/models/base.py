"""
MSGI One — Common Declarative Base Model
Principle: Martin Fowler (Layer Supertype) & Silberschatz (Relational Schema Metadata).
Includes SQLite compatibility compilation rules for PostgreSQL-specific types (ARRAY, JSONB).
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


class Base(DeclarativeBase):
    pass


# SQLite fallback compilation rules for PostgreSQL dialects
@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"
