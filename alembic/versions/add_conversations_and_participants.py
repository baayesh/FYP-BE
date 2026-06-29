"""Add conversations and conversation_participants tables

Revision ID: add_conversations_and_participants
Revises: add_forum_threads_likes_tags
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_conv_and_participants"
down_revision: Union[str, None] = "add_forum_threads_likes_tags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("type", sa.Enum("direct", "group", name="conversationtype"), nullable=False, server_default="direct"),
        sa.Column("context_type", sa.String(50), nullable=True),
        sa.Column("context_id", sa.String(36), nullable=True),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("last_preview", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_id"), "conversations", ["id"])

    op.create_table(
        "conversation_participants",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("conversation_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("last_read_at", sa.DateTime(), nullable=True),
        sa.Column("is_muted", sa.Boolean(), nullable=True, server_default=sa.text("0")),
        sa.Column("joined_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("left_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "user_id", name="uq_conversation_participant"),
    )
    op.create_index(op.f("ix_conversation_participants_id"), "conversation_participants", ["id"])


def downgrade() -> None:
    op.drop_table("conversation_participants")
    op.drop_table("conversations")
