"""add_video_link_to_lessons

Revision ID: 31748d11b4d1
Revises: ef17fdf2e3b0
Create Date: 2025-11-24 12:16:55.214399

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31748d11b4d1'
down_revision = 'ef17fdf2e3b0'
branch_labels = None
depends_on = None


def upgrade():
    # Add video_link column to lessons table
    op.add_column('lessons', sa.Column('video_link', sa.String(500), nullable=True))


def downgrade():
    # Remove video_link column from lessons table
    op.drop_column('lessons', 'video_link')
