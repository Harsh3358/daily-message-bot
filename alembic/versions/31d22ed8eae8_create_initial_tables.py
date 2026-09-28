"""create_initial_tables

Revision ID: 31d22ed8eae8
Revises: 
Create Date: 2026-09-23 16:19:09.260012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '31d22ed8eae8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # 1. Create subjects table
    op.create_table(
        'subjects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('slug', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_subjects_slug', 'subjects', ['slug'])

    # 2. Create problems table
    op.create_table(
        'problems',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('subject_id', UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('reference_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('subject_id', 'scheduled_date', name='uq_subject_scheduled_date'),
    )
    op.create_index('ix_problems_subject_id', 'problems', ['subject_id'])
    op.create_index('ix_problems_scheduled_date', 'problems', ['scheduled_date'])

    # 3. Create telegram_groups table
    op.create_table(
        'telegram_groups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('subject_id', UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False, unique=True),
        sa.Column('group_title', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_telegram_groups_subject_id', 'telegram_groups', ['subject_id'])
    op.create_index('ix_telegram_groups_chat_id', 'telegram_groups', ['chat_id'])

    # 4. Create delivery_logs table
    op.create_table(
        'delivery_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('problem_id', UUID(as_uuid=True), sa.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False),
        sa.Column('telegram_group_id', UUID(as_uuid=True), sa.ForeignKey('telegram_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('delivery_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('telegram_message_id', sa.BigInteger(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_delivery_logs_problem_id', 'delivery_logs', ['problem_id'])
    op.create_index('ix_delivery_logs_telegram_group_id', 'delivery_logs', ['telegram_group_id'])
    op.create_index('ix_delivery_logs_delivery_date', 'delivery_logs', ['delivery_date'])
    op.create_index('ix_delivery_logs_status', 'delivery_logs', ['status'])

    # Partial unique index: uniqueness on problem + telegram_group + delivery_date when status is SUCCESS
    op.create_index(
        'uq_successful_problem_delivery',
        'delivery_logs',
        ['problem_id', 'telegram_group_id', 'delivery_date'],
        unique=True,
        postgresql_where=sa.text("status = 'SUCCESS'"),
    )
    # Composite lookup index for pre-flight query checks
    op.create_index(
        'ix_delivery_lookup',
        'delivery_logs',
        ['problem_id', 'telegram_group_id', 'delivery_date', 'status'],
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index('ix_delivery_lookup', table_name='delivery_logs')
    op.drop_index('uq_successful_problem_delivery', table_name='delivery_logs')
    op.drop_index('ix_delivery_logs_status', table_name='delivery_logs')
    op.drop_index('ix_delivery_logs_delivery_date', table_name='delivery_logs')
    op.drop_index('ix_delivery_logs_telegram_group_id', table_name='delivery_logs')
    op.drop_index('ix_delivery_logs_problem_id', table_name='delivery_logs')
    op.drop_table('delivery_logs')

    op.drop_index('ix_telegram_groups_chat_id', table_name='telegram_groups')
    op.drop_index('ix_telegram_groups_subject_id', table_name='telegram_groups')
    op.drop_table('telegram_groups')

    op.drop_index('ix_problems_scheduled_date', table_name='problems')
    op.drop_index('ix_problems_subject_id', table_name='problems')
    op.drop_table('problems')

    op.drop_index('ix_subjects_slug', table_name='subjects')
    op.drop_table('subjects')
