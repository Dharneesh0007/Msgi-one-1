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


# PostgreSQL bind casting rule for 36-character UUID strings
from sqlalchemy.dialects.postgresql.base import PGCompiler

orig_render_bind_cast = PGCompiler.render_bind_cast


def custom_render_bind_cast(self, type_, dbapi_type, sqltext):
    if getattr(type_, "length", None) == 36:
        return f"{sqltext}::UUID"
    return orig_render_bind_cast(self, type_, dbapi_type, sqltext)


PGCompiler.render_bind_cast = custom_render_bind_cast

