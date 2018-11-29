import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

#On se connecte à la base de données. On utilise Sqlite
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

#On initialise la base de données à l'aide des commandes SQL données dans schema.sql
def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

#On ajoute la commande init-db à flask pour pouvoir initialiser la base de données
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Supprime les données existantes et créé les nouvelles tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
