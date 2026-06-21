"""Add system_health table

Revision ID: add_system_health
Revises: b7a2d3c4e5f6
Create Date: 2026-01-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_system_health'
down_revision = 'b7a2d3c4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'system_health',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('api_uptime', sa.Float(), nullable=True),
        sa.Column('response_time', sa.Integer(), nullable=True),
        sa.Column('error_rate', sa.Float(), nullable=True),
        sa.Column('database_status', sa.String(50), nullable=True),
        sa.Column('active_connections', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_health_id'), 'system_health', ['id'], unique=False)
    op.create_index(op.f('ix_system_health_timestamp'), 'system_health', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_system_health_timestamp'), table_name='system_health')
    op.drop_index(op.f('ix_system_health_id'), table_name='system_health')
    op.drop_table('system_health')
