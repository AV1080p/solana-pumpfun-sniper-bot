"""Add user model

Revision ID: 002_add_user
Revises: 001_initial
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_user'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums for user
    auth_provider_enum = postgresql.ENUM('email', 'google', 'github', 'facebook', 'apple', name='auth_provider', create_type=True)
    auth_provider_enum.create(op.get_bind(), checkfirst=True)
    
    user_role_enum = postgresql.ENUM('user', 'admin', 'moderator', name='user_role', create_type=True)
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('auth_provider', auth_provider_enum, nullable=False, server_default='email'),
        sa.Column('provider_id', sa.String(length=255), nullable=True),
        sa.Column('role', user_role_enum, nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_provider', 'users', ['auth_provider', 'provider_id'])
    op.create_index('idx_users_uuid', 'users', ['uuid'])
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_auth_provider'), 'users', ['auth_provider'], unique=False)
    op.create_index(op.f('ix_users_provider_id'), 'users', ['provider_id'], unique=False)
    
    # Add user_id column to bookings table
    op.add_column('bookings', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_bookings_user_id', 'bookings', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_bookings_user_id'), 'bookings', ['user_id'], unique=False)


def downgrade() -> None:
    # Remove user_id from bookings
    op.drop_constraint('fk_bookings_user_id', 'bookings', type_='foreignkey')
    op.drop_index(op.f('ix_bookings_user_id'), table_name='bookings')
    op.drop_column('bookings', 'user_id')
    
    # Drop users table
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS user_role')
    op.execute('DROP TYPE IF EXISTS auth_provider')

