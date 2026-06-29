"""Add lesson_id column to attendance table

Revision ID: add_lesson_id_to_attendance
Revises: add_conv_and_participants
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "add_lesson_id_to_attendance"
down_revision: Union[str, None] = "add_conv_and_participants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add lesson_id as nullable first (no FK)
    op.add_column("attendance", sa.Column("lesson_id", sa.String(36), nullable=True))

    # Step 2: Assign existing attendance records to any valid lesson in the same course
    conn = op.get_bind()
    result = conn.execute(
        text("""
            UPDATE attendance a
            JOIN (
                SELECT l.course_id, MIN(l.id) as lesson_id
                FROM lessons l
                GROUP BY l.course_id
            ) l ON a.course_id = l.course_id
            SET a.lesson_id = l.lesson_id
            WHERE a.lesson_id IS NULL
        """)
    )

    # Step 3: Now make it NOT NULL and add FK + unique constraint
    op.alter_column("attendance", "lesson_id", existing_type=sa.String(36), nullable=False)
    op.create_foreign_key(
        "attendance_ibfk_lesson",
        "attendance", "lessons",
        ["lesson_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_attendance_course_lesson_student",
        "attendance",
        ["course_id", "lesson_id", "student_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_attendance_course_lesson_student", "attendance", type_="unique")
    op.drop_constraint("attendance_ibfk_lesson", "attendance", type_="foreignkey")
    op.drop_column("attendance", "lesson_id")
