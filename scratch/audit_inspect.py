import glob
import re
import os

print("=== MIGRATION TABLES ===")
for sql_file in sorted(glob.glob("supabase/migrations/*.sql")):
    print(f"\n--- {sql_file} ---")
    with open(sql_file, "r", encoding="utf-8") as f:
        content = f.read()
    tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_\.\"]+)", content, re.IGNORECASE)
    for t in tables:
        print(f"  Table: {t}")
    indexes = re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_\.\"]+)", content, re.IGNORECASE)
    for idx in indexes:
        print(f"  Index: {idx}")

print("\n=== SQLALCHEMY MODELS ===")
import sys
sys.path.insert(0, "services/api")
from src.db.models.base import Base
import src.db.models.user
import src.db.models.core
import src.db.models.extended
import src.db.models.ai

for table_name, table in Base.metadata.tables.items():
    print(f"Model Table: {table_name} ({len(table.columns)} columns)")
