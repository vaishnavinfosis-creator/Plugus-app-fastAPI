"""
Migration: Add password_reset_tokens table
Run this script to create the password_reset_tokens table for password reset functionality
"""
from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Create password_reset_tokens table"""
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_hash VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✓ Created password_reset_tokens table")
        except Exception as e:
            print(f"password_reset_tokens table may already exist: {e}")
        
        # Create index on user_id for faster lookups
        try:
            conn.execute(text(
                "CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id)"
            ))
            conn.commit()
            print("✓ Created index on user_id")
        except Exception as e:
            print(f"Index may already exist: {e}")
        
        # Create index on token_hash for faster lookups
        try:
            conn.execute(text(
                "CREATE INDEX idx_password_reset_tokens_token_hash ON password_reset_tokens(token_hash)"
            ))
            conn.commit()
            print("✓ Created index on token_hash")
        except Exception as e:
            print(f"Index may already exist: {e}")
        
        print("\n✓ Migration completed successfully")


def downgrade():
    """Drop password_reset_tokens table"""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS password_reset_tokens CASCADE"))
        conn.commit()
        print("✓ Rollback completed successfully")


if __name__ == "__main__":
    print("Running migration: Add password_reset_tokens table")
    upgrade()
