"""create_notepad_model

Revision ID: c52e045b1814
Revises: 001
Create Date: 2026-09-21 01:28:51.633718

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c52e045b1814'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Some installations already have notes created outside Alembic.
    # Adopt only a compatible table; never drop existing notes or webhook.
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('notepad'):
        columns = {column['name']: column for column in inspector.get_columns('notepad')}
        expected = {'id': sa.Integer, 'title': sa.String, 'body': sa.Text, 'user_id': sa.Integer}
        compatible = all(
            name in columns
            and isinstance(columns[name]['type'], column_type)
            and not columns[name]['nullable']
            for name, column_type in expected.items()
        )
        compatible = compatible and columns['title']['type'].length == 256
        primary_key = inspector.get_pk_constraint('notepad')['constrained_columns']
        has_user_fk = any(
            fk['constrained_columns'] == ['user_id']
            and fk['referred_table'] == 'user'
            and fk['referred_columns'] == ['id']
            for fk in inspector.get_foreign_keys('notepad')
        )
        if not compatible or primary_key != ['id'] or not has_user_fk:
            raise RuntimeError(
                "Existing notepad table is incompatible with the Notepad model; "
                "review its schema before retrying the migration. No notes were modified."
            )
        return

    op.create_table(
        'notepad',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('notepad')
