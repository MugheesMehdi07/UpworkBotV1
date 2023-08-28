"""empty message

Revision ID: 458c50f22ae4
Revises: aed6af71c314
Create Date: 2023-08-28 16:36:08.915824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '458c50f22ae4'
down_revision = 'aed6af71c314'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('proposals')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('proposals',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('proposal', sa.VARCHAR(), nullable=True),
    sa.Column('job_id', sa.INTEGER(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
