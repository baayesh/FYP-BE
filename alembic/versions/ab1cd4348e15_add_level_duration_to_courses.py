"""add_level_duration_to_courses

Revision ID: ab1cd4348e15
Revises: add_student_performance
Create Date: 2025-11-08 20:49:54.815518

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab1cd4348e15'
down_revision = 'add_student_performance'
branch_label = None
depends_on = None


def upgrade():
    # Add level and duration columns to courses table
    op.add_column('courses', sa.Column('level', sa.String(50), nullable=True))
    op.add_column('courses', sa.Column('duration', sa.String(50), nullable=True))


def downgrade():
    # Remove level and duration columns from courses table
    op.drop_column('courses', 'duration')
    op.drop_column('courses', 'level')
