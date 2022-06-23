"""Update log unique time and vehicle

Revision ID: 3161c46e9c33
Revises: 377e203c909a
Create Date: 2022-06-21 15:22:47.522739

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3161c46e9c33'
down_revision = '377e203c909a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('_start_unit_unique_constraint', 'log_file', ['start_time', 'unit_number'])


def downgrade():
    op.drop_constraint('_start_unit_unique_constraint', 'log_file', type_='unique')
