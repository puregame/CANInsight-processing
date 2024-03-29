"""initial version

Revision ID: b229a053386d
Revises: 
Create Date: 2022-01-05 15:54:27.162464

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b229a053386d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('vehicle',
    sa.Column('unit_number', sa.String(), nullable=False),
    sa.Column('serial_number', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('unit_number')
    )
    op.create_table('log_file',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('upload_time', sa.DateTime(), nullable=True),
    sa.Column('unit_number', sa.String(), nullable=False),
    sa.Column('length', sa.Float(), nullable=True),
    sa.Column('samples', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['unit_number'], ['vehicle.unit_number'], name='vehicle_id_log_fkey', onupdate='CASCADE', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('log_file')
    op.drop_table('vehicle')
    # ### end Alembic commands ###
