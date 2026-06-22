"""Add likes and tags columns to forum_threads

Revision ID: add_forum_threads_likes_tags
Revises: add_calendar_event_link_column
Create Date: 2026-06-21 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_forum_threads_likes_tags"
down_revision: Union[str, None] = "add_calendar_event_link_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("forum_threads", sa.Column("likes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("forum_threads", sa.Column("tags", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("forum_threads", "tags")
    op.drop_column("forum_threads", "likes")
