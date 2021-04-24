import click
import logging

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as _Session

from . import db, scenarios, secrets
import flask_login
import random

login_manager = flask_login.LoginManager()


logger = logging.getLogger(__name__)

from sqlalchemy import create_engine

engine = create_engine(secrets.db_url)
db.Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
import os
from contextlib import contextmanager

@contextmanager
def session_scope() -> _Session:
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

@click.group()
def cli():
    pass

@cli.command()
def show_users():
    print("Known users:")
    with session_scope() as s:
        for u in s.query(db.User):
            assert isinstance(u, db.User)
            print(f"User {u.id}, name: {u.name}, codename: {u.codename} login link: {secrets.base_url}login/{u.login_link}")


@cli.command()
@click.option('--name')
def add_user(name: str):
    with session_scope() as s:
        u = db.User()
        u.name = name
        u.codename = name.replace(' ', '_').lower()
        u.login_link = ''.join(['%x' % random.randrange(256) for i in range(16)])
        s.add(u)


if __name__ == '__main__':
    cli()