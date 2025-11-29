# validate_models.py
# This script validates model-to-database consistency.
# It checks:
# 1. All tables exist
# 2. All model columns exist in DB
# 3. All DB columns exist in models (optional warning)
# 4. PostGIS extensions are available

from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()

def check_postgis(connection):
    """Check that PostGIS extension works."""
    try:
        result = connection.execute(text("SELECT PostGIS_Full_Version();"))
        version = result.fetchone()[0]
        return True, version
    except Exception as e:
        return False, str(e)

def get_db_tables(inspector):
    """Return all real DB tables."""
    return inspector.get_table_names()

def get_model_tables():
    """Fetch SQLAlchemy models metadata tables."""
    return list(db.metadata.tables.keys())

def compare_tables(db_tables, model_tables):
    """Find differences between models and DB."""
    missing_in_db = [t for t in model_tables if t not in db_tables]
    extra_in_db = [t for t in db_tables if t not in model_tables and not t.startswith("spatial_") and not t.endswith("_columns")]
    return missing_in_db, extra_in_db

def compare_columns(inspector, table):
    """Compare columns of a table in models vs DB."""
    db_columns = [col["name"] for col in inspector.get_columns(table)]
    model_columns = list(db.metadata.tables[table].columns.keys())

    missing_cols = [c for c in model_columns if c not in db_columns]
    extra_cols = [c for c in db_columns if c not in model_columns]

    return missing_cols, extra_cols

with app.app_context():
    connection = db.engine.connect()
    inspector = inspect(db.engine)

    print("=== Checking PostGIS Extension ===")
    ok, info = check_postgis(connection)
    if ok:
        print(f"PostGIS OK: {info}")
    else:
        print(f"PostGIS ERROR: {info}")

    print("\n=== Checking Tables ===")
    db_tables = get_db_tables(inspector)
    model_tables = get_model_tables()

    missing_in_db, extra_in_db = compare_tables(db_tables, model_tables)

    print(f"Tables in DB: {len(db_tables)}")
    print(f"Tables in Models: {len(model_tables)}")

    if missing_in_db:
        print("\n❌ Missing tables in DB:")
        for t in missing_in_db:
            print(f"  - {t}")
    else:
        print("\n✔ All model tables exist in DB")

    if extra_in_db:
        print("\n⚠ Extra tables in DB (safe to ignore if intentional):")
        for t in extra_in_db:
            print(f"  - {t}")

    print("\n=== Checking Column Mismatches ===")
    for table in model_tables:
        if table not in db_tables:
            continue
        missing_cols, extra_cols = compare_columns(inspector, table)

        if missing_cols or extra_cols:
            print(f"\nTable: {table}")
            if missing_cols:
                print("  ❌ Missing columns in DB:")
                for c in missing_cols:
                    print(f"    - {c}")
            if extra_cols:
                print("  ⚠ Extra columns in DB:")
                for c in extra_cols:
                    print(f"    - {c}")

    print("\n=== Validation Complete ===")
