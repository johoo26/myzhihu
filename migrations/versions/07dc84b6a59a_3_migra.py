"""3 migra

Revision ID: 07dc84b6a59a
Revises: 
Create Date: 2017-09-18 21:40:53.414580

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07dc84b6a59a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('answers', sa.Column('likes_count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('answers', 'likes_count')
    # ### end Alembic commands ###
