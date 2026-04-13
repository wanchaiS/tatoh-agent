import sys
import asyncio
from alembic.config import Config
from alembic import command
from sqlalchemy import text

# Import the pre-configured async engine from your architecture
from db.database import engine

async def setup_schema():
    """Ensure the target schema exists before Alembic tries to use it."""
    print("Verifying database schemas...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS tatoh"))
    print("Schema 'tatoh' is ready.")
    await engine.dispose()

def run_migrations():
    """Programmatically run 'alembic upgrade head'."""
    print("Running Alembic migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Database migrations complete!")

def check_status():
    """Check current database revision."""
    print("Checking database migration status...")
    alembic_cfg = Config("alembic.ini")
    # Show current version against the DB
    print("\n--- Current Database Revision ---")
    command.current(alembic_cfg, verbose=True)
    # Show latest available head version
    print("\n--- Latest Available (Head) Revision ---")
    command.heads(alembic_cfg, verbose=True)

def migrate():
    """Run full migration sequence."""
    asyncio.run(setup_schema())
    run_migrations()

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.db_manager [migrate|status]")
        sys.exit(1)
    
    cmd = sys.argv[1].strip().lower()
    
    if cmd == "migrate":
        migrate()
    elif cmd == "status":
        check_status()
    else:
        print(f"Unknown command: {cmd}")
        print("Available commands: migrate, status")
        sys.exit(1)

if __name__ == "__main__":
    main()
