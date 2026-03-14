"""
Migration: Add moderation fields to Review table
Run this script to add is_flagged, is_approved, and moderation_notes fields
"""
from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add moderation fields to reviews table"""
    with engine.connect() as conn:
        # Add is_flagged column (default False)
        try:
            conn.execute(text(
                "ALTER TABLE reviews ADD COLUMN is_flagged BOOLEAN DEFAULT FALSE"
            ))
            conn.commit()
            print("✓ Added is_flagged column")
        except Exception as e:
            print(f"is_flagged column may already exist: {e}")
        
        # Add is_approved column (default True)
        try:
            conn.execute(text(
                "ALTER TABLE reviews ADD COLUMN is_approved BOOLEAN DEFAULT TRUE"
            ))
            conn.commit()
            print("✓ Added is_approved column")
        except Exception as e:
            print(f"is_approved column may already exist: {e}")
        
        # Add moderation_notes column
        try:
            conn.execute(text(
                "ALTER TABLE reviews ADD COLUMN moderation_notes TEXT"
            ))
            conn.commit()
            print("✓ Added moderation_notes column")
        except Exception as e:
            print(f"moderation_notes column may already exist: {e}")
        
        print("\n✓ Migration completed successfully")


def downgrade():
    """Remove moderation fields from reviews table"""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE reviews DROP COLUMN IF EXISTS is_flagged"))
        conn.execute(text("ALTER TABLE reviews DROP COLUMN IF EXISTS is_approved"))
        conn.execute(text("ALTER TABLE reviews DROP COLUMN IF EXISTS moderation_notes"))
        conn.commit()
        print("✓ Rollback completed successfully")


if __name__ == "__main__":
    print("Running migration: Add review moderation fields")
    upgrade()
