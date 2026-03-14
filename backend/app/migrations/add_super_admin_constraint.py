"""
Migration: Add Super Admin Uniqueness Constraint
Ensures only one active Super Admin can exist in the system
"""
from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """
    Add a partial unique index to enforce only one active Super Admin
    This allows the constraint to be enforced at the database level
    """
    with engine.connect() as conn:
        # Create a partial unique index on role where role = 'SUPER_ADMIN' and is_active = true
        # This ensures only one active Super Admin can exist
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_super_admin 
            ON users (role) 
            WHERE role = 'SUPER_ADMIN' AND is_active = true;
        """))
        conn.commit()
        print("✓ Added Super Admin uniqueness constraint")


def downgrade():
    """
    Remove the Super Admin uniqueness constraint
    """
    with engine.connect() as conn:
        conn.execute(text("""
            DROP INDEX IF EXISTS idx_unique_active_super_admin;
        """))
        conn.commit()
        print("✓ Removed Super Admin uniqueness constraint")


if __name__ == "__main__":
    print("Running Super Admin uniqueness constraint migration...")
    upgrade()
    print("Migration complete!")
