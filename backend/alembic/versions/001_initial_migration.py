"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

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
    # Create enums
    booking_status_enum = postgresql.ENUM('pending', 'confirmed', 'cancelled', 'completed', name='booking_status', create_type=True)
    booking_status_enum.create(op.get_bind(), checkfirst=True)
    
    payment_method_enum = postgresql.ENUM('stripe', 'solana', 'bitcoin', 'ethereum', name='payment_method', create_type=True)
    payment_method_enum.create(op.get_bind(), checkfirst=True)
    
    payment_status_enum = postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'refunded', 'cancelled', name='payment_status', create_type=True)
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create tours table
    op.create_table(
        'tours',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('price_sol', sa.Float(), nullable=False),
        sa.Column('duration', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('price >= 0', name='check_price_positive'),
        sa.CheckConstraint('price_sol >= 0', name='check_price_sol_positive'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tours_location', 'tours', ['location'])
    op.create_index('idx_tours_created_at', 'tours', ['created_at'])
    op.create_index(op.f('ix_tours_id'), 'tours', ['id'], unique=False)
    op.create_index(op.f('ix_tours_name'), 'tours', ['name'], unique=False)
    
    # Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tour_id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('booking_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', booking_status_enum, nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bookings_user_email', 'bookings', ['user_email'])
    op.create_index('idx_bookings_status', 'bookings', ['status'])
    op.create_index('idx_bookings_booking_date', 'bookings', ['booking_date'])
    op.create_index('idx_bookings_tour_status', 'bookings', ['tour_id', 'status'])
    op.create_index(op.f('ix_bookings_id'), 'bookings', ['id'], unique=False)
    op.create_index(op.f('ix_bookings_tour_id'), 'bookings', ['tour_id'], unique=False)
    
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_method', payment_method_enum, nullable=False),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('status', payment_status_enum, nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount >= 0', name='check_payment_amount_positive'),
        sa.UniqueConstraint('transaction_id')
    )
    op.create_index('idx_payments_transaction_id', 'payments', ['transaction_id'])
    op.create_index('idx_payments_status', 'payments', ['status'])
    op.create_index('idx_payments_method_status', 'payments', ['payment_method', 'status'])
    op.create_index('idx_payments_created_at', 'payments', ['created_at'])
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_booking_id'), 'payments', ['booking_id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_table('payments')
    op.drop_table('bookings')
    op.drop_table('tours')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS payment_status')
    op.execute('DROP TYPE IF EXISTS payment_method')
    op.execute('DROP TYPE IF EXISTS booking_status')

