"""
Quick database initialization script
Untuk testing dan development purposes
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import DATABASE_URL

def check_database():
    """Check if database is accessible and has tables"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            print("\n" + "="*60)
            print("DATABASE STATUS")
            print("="*60)
            print(f"✓ Database connected: {DATABASE_URL}")
            print(f"\nTables found: {len(tables)}")
            if tables:
                for table in sorted(tables):
                    print(f"  - {table}")
            else:
                print("  (No tables found - run migrations)")
            print("="*60 + "\n")
            
            return len(tables) > 0
    except Exception as e:
        print(f"\n✗ Database connection failed: {e}\n")
        return False

def reset_database():
    """Reset database (drop all tables and restart)"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Drop all tables
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
            print("\n✓ Database reset successfully\n")
    except Exception as e:
        print(f"\n✗ Error resetting database: {e}\n")
        raise

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    else:
        check_database()
