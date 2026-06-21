"""fix_teacher_id_type

Revision ID: fix_teacher_id_type
Revises: ab1cd4348e15
Create Date: 2025-11-08 20:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_teacher_id_type'
down_revision = 'ab1cd4348e15'
branch_label = None
depends_on = None


def upgrade():
    # First, drop the foreign key constraint on course_enrollments that references courses
    op.drop_constraint('course_enrollments_ibfk_2', 'course_enrollments', type_='foreignkey')

    # Change teacher_id column type from int to varchar(36)
    op.alter_column('courses', 'teacher_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(36),
                    existing_nullable=True)

    # Change student_id in course_enrollments from int to varchar(36)
    op.alter_column('course_enrollments', 'student_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(36),
                    existing_nullable=False)

    # Add foreign key constraint for courses.teacher_id -> users.id
    op.create_foreign_key(
        'fk_courses_teacher_id',
        'courses', 'users',
        ['teacher_id'], ['id'],
        ondelete='CASCADE'
    )

    # Add foreign key constraint for course_enrollments.student_id -> users.id
    op.create_foreign_key(
        'fk_course_enrollments_student_id',
        'course_enrollments', 'users',
        ['student_id'], ['id'],
        ondelete='CASCADE'
    )

    # Re-add foreign key constraint for course_enrollments.course_id -> courses.id
    op.create_foreign_key(
        'fk_course_enrollments_course_id',
        'course_enrollments', 'courses',
        ['course_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop all the foreign key constraints
    op.drop_constraint('fk_course_enrollments_course_id', 'course_enrollments', type_='foreignkey')
    op.drop_constraint('fk_course_enrollments_student_id', 'course_enrollments', type_='foreignkey')
    op.drop_constraint('fk_courses_teacher_id', 'courses', type_='foreignkey')

    # Change student_id back to int
    op.alter_column('course_enrollments', 'student_id',
                    existing_type=sa.String(36),
                    type_=sa.Integer(),
                    existing_nullable=False)

    # Change teacher_id back to int
    op.alter_column('courses', 'teacher_id',
                    existing_type=sa.String(36),
                    type_=sa.Integer(),
                    existing_nullable=True)

    # Re-add the original foreign key constraint for course_enrollments.course_id
    op.create_foreign_key(
        'course_enrollments_ibfk_2',
        'course_enrollments', 'courses',
        ['course_id'], ['id'],
        ondelete='CASCADE'
    )
