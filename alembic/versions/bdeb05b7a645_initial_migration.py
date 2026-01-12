"""initial migration

Revision ID: bdeb05b7a645
Revises: 
Create Date: 2026-01-12 10:18:42.905350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdeb05b7a645'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_departments_id', 'departments', ['id'])
    op.create_index('ix_departments_name', 'departments', ['name'])

    op.create_table('employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('salary', sa.Float(), nullable=True),
        sa.Column('dept_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['dept_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_employees_id', 'employees', ['id'])
    op.create_index('ix_employees_email', 'employees', ['email'])

    op.create_table('attendance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emp_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['emp_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attendance_id', 'attendance', ['id'])

    op.create_table('leaves',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emp_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('approve', sa.Boolean(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['emp_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_leaves_id', 'leaves', ['id'])

    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('receiver_id', sa.Integer(), nullable=True),
        sa.Column('message', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['receiver_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_id', 'messages', ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_messages_id', table_name='messages')
    op.drop_table('messages')
    op.drop_index('ix_leaves_id', table_name='leaves')
    op.drop_table('leaves')
    op.drop_index('ix_attendance_id', table_name='attendance')
    op.drop_table('attendance')
    op.drop_index('ix_employees_email', table_name='employees')
    op.drop_index('ix_employees_id', table_name='employees')
    op.drop_table('employees')
    op.drop_index('ix_departments_name', table_name='departments')
    op.drop_index('ix_departments_id', table_name='departments')
    op.drop_table('departments')
