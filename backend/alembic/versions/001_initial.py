"""Initial database schema creation

Revision ID: 001_initial
Revises: 
Create Date: 2026-04-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create ENUM types with IF NOT EXISTS
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM ('Admin_IT', 'Pengawas_K3', 'Manager_HR');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'camera_status') THEN
                CREATE TYPE camera_status AS ENUM ('Active', 'Inactive', 'Maintenance');
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'violation_status') THEN
                CREATE TYPE violation_status AS ENUM ('Unverified', 'Verified', 'False_Positive');
            END IF;
        END $$;
    """)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('telegram_id', sa.String(50), nullable=True),
        sa.Column('role', postgresql.ENUM('Admin_IT', 'Pengawas_K3', 'Manager_HR', name='user_role', create_type=False), nullable=False, server_default='Pengawas_K3'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create camera table
    op.create_table(
        'camera',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rtsp_url', sa.String(255), nullable=False),
        sa.Column('status', postgresql.ENUM('Active', 'Inactive', 'Maintenance', name='camera_status', create_type=False), nullable=False, server_default='Active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create violations table
    op.create_table(
        'violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('camera_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('missing_apd', sa.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('snapshot_path', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', postgresql.ENUM('Unverified', 'Verified', 'False_Positive', name='violation_status', create_type=False), nullable=False, server_default='Unverified'),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['camera_id'], ['camera.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_violations_timestamp', 'violations', ['timestamp'])
    
    # Create detection_stats table
    op.create_table(
        'detection_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('camera_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('total_workers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('compliant_workers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('violating_workers', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['camera_id'], ['camera.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_detection_stats_timestamp', 'detection_stats', ['timestamp'])
    
    # Create notification table
    op.create_table(
        'notification',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('violation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['violation_id'], ['violations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notification_user_id', 'notification', ['user_id'])


def downgrade() -> None:
    # Drop indices
    op.drop_index('idx_notification_user_id', table_name='notification')
    op.drop_index('idx_detection_stats_timestamp', table_name='detection_stats')
    op.drop_index('idx_violations_timestamp', table_name='violations')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    
    # Drop tables
    op.drop_table('notification')
    op.drop_table('detection_stats')
    op.drop_table('violations')
    op.drop_table('camera')
    op.drop_table('users')
    
    # Drop ENUM types with IF EXISTS
    op.execute("DROP TYPE IF EXISTS violation_status CASCADE")
    op.execute("DROP TYPE IF EXISTS camera_status CASCADE")
    op.execute("DROP TYPE IF EXISTS user_role CASCADE")
    
    # Drop UUID extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
