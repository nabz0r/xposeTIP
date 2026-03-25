"""One-time sync: copy primary_avatar from profile_data to targets.avatar_url.

Usage:
    docker compose exec api python scripts/sync_avatars.py
"""
from sqlalchemy import text
from api.database import SessionLocal


def main():
    db = SessionLocal()
    try:
        result = db.execute(text("""
            UPDATE targets
            SET avatar_url = profile_data->>'primary_avatar'
            WHERE profile_data->>'primary_avatar' IS NOT NULL
              AND (avatar_url IS NULL
                   OR avatar_url != profile_data->>'primary_avatar')
        """))
        db.commit()
        print(f"Synced {result.rowcount} target avatar(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
