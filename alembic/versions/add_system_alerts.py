"""Add system_alerts table

Revision ID: add_system_alerts
Revises: add_activity_logs
Create Date: 2026-01-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_system_alerts'
down_revision = 'add_activity_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'system_alerts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.String(500), nullable=False),
        sa.Column('affected_resource', sa.String(100), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_alerts_id'), 'system_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_system_alerts_is_resolved'), 'system_alerts', ['is_resolved'], unique=False)
    op.create_index(op.f('ix_system_alerts_created_at'), 'system_alerts', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_system_alerts_created_at'), table_name='system_alerts')
    op.drop_index(op.f('ix_system_alerts_is_resolved'), table_name='system_alerts')
    op.drop_index(op.f('ix_system_alerts_id'), table_name='system_alerts')
    op.drop_table('system_alerts')
