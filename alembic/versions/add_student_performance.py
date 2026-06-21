"""Add student performance tables

Revision ID: add_student_performance
Revises: 
Create Date: 2025-11-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_student_performance'
down_revision = None  # Update this with your latest migration revision
branch_label = None
depends_on = None


def upgrade():
    # Create performance_trends table
    op.create_table(
        'performance_trends',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('score', sa.Numeric(5, 2), nullable=False),
        sa.Column('course_id', sa.String(36), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create weekly_activities table
    op.create_table(
        'weekly_activities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('day_of_week', sa.String(10), nullable=False),
        sa.Column('hours_studied', sa.Numeric(4, 2), server_default='0.0'),
        sa.Column('assignments_completed', sa.Integer(), server_default='0'),
        sa.Column('quizzes_completed', sa.Integer(), server_default='0'),
        sa.Column('lessons_viewed', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create student_skills table
    op.create_table(
        'student_skills',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('skill_name', sa.String(100), nullable=False),
        sa.Column('skill_value', sa.Numeric(5, 2), nullable=False),
        sa.Column('last_assessed', sa.Date(), nullable=False),
        sa.Column('course_id', sa.String(36), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create student_levels table
    op.create_table(
        'student_levels',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('grade', sa.String(50), nullable=False),
        sa.Column('stream', sa.String(50)),
        sa.Column('overall_progress', sa.Numeric(5, 2), server_default='0.0'),
        sa.Column('academic_year', sa.String(20)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create subject_marks table
    op.create_table(
        'subject_marks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('subject_name', sa.String(100), nullable=False),
        sa.Column('score', sa.Numeric(5, 2), nullable=False),
        sa.Column('max_score', sa.Numeric(5, 2), server_default='100.0'),
        sa.Column('assessment_type', sa.String(50)),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('course_id', sa.String(36), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create improvement_areas table
    op.create_table(
        'improvement_areas',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('subject_name', sa.String(100), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('suggestion', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(20), server_default='medium'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('course_id', sa.String(36), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('identified_date', sa.Date(), nullable=False),
        sa.Column('resolved_date', sa.Date()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table('improvement_areas')
    op.drop_table('subject_marks')
    op.drop_table('student_levels')
    op.drop_table('student_skills')
    op.drop_table('weekly_activities')
    op.drop_table('performance_trends')
