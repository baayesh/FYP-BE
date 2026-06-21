#!/usr/bin/env python3
"""Add missing columns to courses table"""

from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Add code column
    try:
        result = conn.execute(text("SHOW COLUMNS FROM courses LIKE 'code'"))
        if result.fetchone():
            print("✓ code column already exists")
        else:
            print("Adding code column...")
            conn.execute(text("ALTER TABLE courses ADD COLUMN code VARCHAR(50) NULL"))
            conn.commit()
            print("✓ code column added")
    except Exception as e:
        print(f"code column: {e}")
    
    # Add instructor column
    try:
        result = conn.execute(text("SHOW COLUMNS FROM courses LIKE 'instructor'"))
        if result.fetchone():
            print("✓ instructor column already exists")
        else:
            print("Adding instructor column...")
            conn.execute(text("ALTER TABLE courses ADD COLUMN instructor VARCHAR(255) NULL"))
            conn.commit()
            print("✓ instructor column added")
    except Exception as e:
        print(f"instructor column: {e}")

print("\nDone!")
