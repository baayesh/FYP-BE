"""add_teacher_stats_tables

Revision ID: b7a2d3c4e5f6
Revises: ef17fdf2e3b0
Create Date: 2025-11-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7a2d3c4e5f6'
down_revision = '457857de2395'
branch_label = None
depends_on = None


def upgrade():
    op.create_table(
        'teacher_stats',
        sa.Column('id', sa.String(length=36), primary_key=True, index=True),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('snapshot_date', sa.Date(), nullable=False, index=True),

        sa.Column('total_courses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_students', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pending_grading', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('upcoming_classes', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('avg_feedback_rating', sa.Float(), nullable=False, server_default='0'),
        sa.Column('avg_grade', sa.Float(), nullable=False, server_default='0'),

        sa.Column('enrollments_today', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assignments_submitted_today', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_index('idx_teacher_stats_teacher_date', 'teacher_stats', ['teacher_id', 'snapshot_date'])

    op.create_table(
        'teacher_stat_timeseries',
        sa.Column('id', sa.String(length=36), primary_key=True, index=True),
        sa.Column('teacher_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('metric_name', sa.String(length=50), nullable=False, index=True),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
    )

    op.create_index('idx_tstats_ts_teacher_metric', 'teacher_stat_timeseries', ['teacher_id', 'metric_name', 'timestamp'])


def downgrade():
    op.drop_index('idx_tstats_ts_teacher_metric', table_name='teacher_stat_timeseries')
    op.drop_table('teacher_stat_timeseries')
    op.drop_index('idx_teacher_stats_teacher_date', table_name='teacher_stats')
    op.drop_table('teacher_stats')
