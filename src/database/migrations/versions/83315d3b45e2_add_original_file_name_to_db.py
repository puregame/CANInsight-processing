"""add original file name to db

Revision ID: 83315d3b45e2
Revises: 3161c46e9c33
Create Date: 2022-06-28 12:01:07.439477

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83315d3b45e2'
down_revision = '3161c46e9c33'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('log_file', sa.Column('original_file_name', sa.String(), nullable=True))


def downgrade():
    op.drop_column('log_file', 'original_file_name')
