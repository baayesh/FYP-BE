"""Add link column to calendar_events table

Revision ID: add_calendar_event_link_column
Revises: add_course_code_instructor
Create Date: 2026-06-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_calendar_event_link_column'
down_revision = 'add_course_code_instructor'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('calendar_events', sa.Column('link', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('calendar_events', 'link')
