"""mig

Revision ID: 782fe137a73b
Revises: 07dc84b6a59a
Create Date: 2017-09-20 22:35:32.249063

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '782fe137a73b'
down_revision = '07dc84b6a59a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('answers', sa.Column('body_html', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('answers', 'body_html')
    # ### end Alembic commands ###
