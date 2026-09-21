"""Exercise the migration chain without loading application models or remote DBs."""

import importlib.util
import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


VERSIONS = Path(__file__).resolve().parents[4] / 'migrations' / 'versions'


def load_revision(filename):
    spec = importlib.util.spec_from_file_location('migration', VERSIONS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INITIAL = load_revision('001.py')
NOTEPAD = load_revision('c52e045b1814_create_notepad_model.py')


@pytest.fixture
def connection():
    # The optional URL must point at an empty, disposable database.
    engine = sa.create_engine(os.environ.get('MIGRATION_TEST_URL', 'sqlite:///:memory:'))
    with engine.begin() as conn:
        with Operations.context(MigrationContext.configure(conn)):
            INITIAL.upgrade()
            conn.execute(sa.text('INSERT INTO webhook (id) VALUES (42)'))
            yield conn
            if sa.inspect(conn).has_table('notepad'):
                NOTEPAD.downgrade()
            INITIAL.downgrade()
    engine.dispose()


def test_fresh_upgrade_and_downgrade_preserve_webhook(connection):
    NOTEPAD.upgrade()
    columns = {c['name'] for c in sa.inspect(connection).get_columns('notepad')}
    assert columns == {'id', 'title', 'body', 'user_id'}
    assert connection.execute(sa.text('SELECT id FROM webhook')).scalar_one() == 42
    NOTEPAD.downgrade()
    assert not sa.inspect(connection).has_table('notepad')
    assert connection.execute(sa.text('SELECT id FROM webhook')).scalar_one() == 42
    NOTEPAD.upgrade()


def test_existing_notes_are_preserved(connection):
    connection.execute(sa.text(
        'CREATE TABLE notepad (id INTEGER NOT NULL PRIMARY KEY, '
        'title VARCHAR(256) NOT NULL, body TEXT NOT NULL, user_id INTEGER NOT NULL, '
        'FOREIGN KEY (user_id) REFERENCES user(id))'
    ))
    connection.execute(sa.text(
        "INSERT INTO user (id, email, password, created_at) "
        "VALUES (1, 'migration@example.test', 'unused', '2026-01-01 00:00:00')"
    ))
    connection.execute(sa.text(
        "INSERT INTO notepad (id, title, body, user_id) VALUES (1, 'Note', 'Keep this', 1)"
    ))
    NOTEPAD.upgrade()
    assert connection.execute(sa.text('SELECT title, body, user_id FROM notepad')).one() == (
        'Note', 'Keep this', 1
    )
    assert connection.execute(sa.text('SELECT id FROM webhook')).scalar_one() == 42


def test_incompatible_existing_table_is_not_silently_accepted(connection):
    connection.execute(sa.text('CREATE TABLE notepad (id INTEGER NOT NULL PRIMARY KEY)'))
    connection.execute(sa.text('INSERT INTO notepad (id) VALUES (7)'))
    with pytest.raises(RuntimeError, match='incompatible'):
        NOTEPAD.upgrade()
    assert connection.execute(sa.text('SELECT id FROM notepad')).scalar_one() == 7
