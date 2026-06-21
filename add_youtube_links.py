import asyncio
import json
from sqlalchemy import text
from app.core.database import SessionLocal

async def add_youtube_links():
    """Add YouTube video links to existing lessons"""
    db = SessionLocal()

    try:
        # Get all lessons
        result = db.execute(text("SELECT id, title FROM lessons"))
        lessons = result.fetchall()

        if not lessons:
            print("❌ No lessons found!")
            return

        print(f"📚 Found {len(lessons)} lessons to update with YouTube links\n")

        # YouTube video links for different lesson types
        youtube_links = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Introduction
            "https://www.youtube.com/watch?v=oHg5SJYRHA0",  # Fundamentals
            "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Applications
            "https://www.youtube.com/watch?v=J---aiyznGQ",  # Advanced Topics
            "https://www.youtube.com/watch?v=ZZ5LpwO-An4",  # Case Studies
            "https://www.youtube.com/watch?v=hTWKbfoikeg",  # Practice Problems
            "https://www.youtube.com/watch?v=60ItHLz5WEA",  # Review
            "https://www.youtube.com/watch?v=JGwWNGJdvx8",  # Final Assessment
        ]

        # Update each lesson with a YouTube link
        for i, lesson in enumerate(lessons):
            lesson_id = lesson[0]
            lesson_title = lesson[1]

            # Cycle through YouTube links
            video_link = youtube_links[i % len(youtube_links)]

            # Update the lesson
            db.execute(text("""
                UPDATE lessons
                SET video_link = :video_link, updated_at = NOW()
                WHERE id = :lesson_id
            """), {"video_link": video_link, "lesson_id": lesson_id})

            print(f"✅ Updated '{lesson_title}' with YouTube link: {video_link}")

        db.commit()
        print(f"\n🎉 Successfully added YouTube links to {len(lessons)} lessons!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error updating lessons: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🎬 Adding YouTube video links to lessons...\n")
    asyncio.run(add_youtube_links())
    print("\n✨ Update complete!")