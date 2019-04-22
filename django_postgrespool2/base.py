# -*- coding: utf-8 -*-
from importlib import import_module
import logging
from functools import partial

from sqlalchemy import event
from sqlalchemy.dialects import postgresql

from django.conf import settings

if 'Psycopg2DatabaseWrapper' not in globals():
    try:
        # Django >= 1.9
        from django.db.backends.postgresql.base import (
            psycopg2,
            PSYCOPG2_VERSION,
            Database,
            DatabaseWrapper as Psycopg2DatabaseWrapper,
        )
        from django.db.backends.postgresql.creation import (
            DatabaseCreation as Psycopg2DatabaseCreation,
        )
    except ImportError:
        from django.db.backends.postgresql_psycopg2.base import (
            psycopg2,
            Database,
            PSYCOPG2_VERSION,
            DatabaseWrapper as Psycopg2DatabaseWrapper,
        )
        from django.db.backends.postgresql_psycopg2.creation import (
            DatabaseCreation as Psycopg2DatabaseCreation,
        )


# DATABASE_POOL_ARGS should be something like:
# {'max_overflow':10, 'pool_size':5, 'recycle':300}
pool_args = {'max_overflow': 10, 'pool_size': 5, 'recycle': 300}
pool_args.update(getattr(settings, 'DATABASE_POOL_ARGS', {}))
dialect = postgresql.dialect(dbapi=psycopg2)
pool_args['dialect'] = dialect

POOL_CLS = getattr(settings, 'DATABASE_POOL_CLASS', 'sqlalchemy.pool.QueuePool')
pool_module_name, pool_cls_name = POOL_CLS.rsplit('.', 1)
pool_cls = getattr(import_module(pool_module_name), pool_cls_name)


log = logging.getLogger('z.pool')


def _log(message, *args):
    log.debug(message)


@event.listens_for(pool_cls, 'connect')
def receive_connect(dbapi_conn, conn_record):
    # psycopg 2.8 add connection info thus assign connection record info to it
    if PSYCOPG2_VERSION >= (2, 8, 0):
        conn_record.info = dbapi_conn.info


# Only hook up the listeners if we are in debug mode.
if settings.DEBUG:
    event.listen(pool_cls, 'checkout', partial(_log, 'retrieved from pool'))
    event.listen(pool_cls, 'checkin', partial(_log, 'returned to pool'))
    event.listen(pool_cls, 'connect', partial(_log, 'new connection'))


def get_conn(**kw):
    c = Database.connect(**kw)
    return c


class DatabaseCreation(Psycopg2DatabaseCreation):
    def destroy_test_db(self, *args, **kw):
        """Ensure connection pool is disposed before trying to drop database.
        """
        self.connection.dispose()
        super(DatabaseCreation, self).destroy_test_db(*args, **kw)


class DatabaseWrapper(Psycopg2DatabaseWrapper):
    """SQLAlchemy FTW."""

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self._pool = pool_cls(
            lambda: get_conn(**self.get_connection_params()), **pool_args)
        self.creation = DatabaseCreation(self)

    @property
    def pool(self):
        return self._pool

    def _commit(self):
        if self.connection is not None and self.is_usable():
            with self.wrap_database_errors:
                return self.connection.commit()

    def _rollback(self):
        if self.connection is not None and self.is_usable():
            with self.wrap_database_errors:
                return self.connection.rollback()

    def dispose(self):
        """Dispose of the pool for this instance, closing all connections."""
        self.close()
        self.pool.dispose()

    def get_new_connection(self, conn_params):
        # get new connection through pool, not creating a new one outside.
        c = self.pool.connect()

        options = self.settings_dict['OPTIONS']
        try:
            self.isolation_level = options['isolation_level']
        except KeyError:
            self.isolation_level = c.connection.isolation_level
        else:
            # Set the isolation level to the value from OPTIONS.
            if self.isolation_level != c.connection.isolation_level:
                c.connection.set_session(isolation_level=self.isolation_level)

        return c

    def _set_autocommit(self, autocommit):
        with self.wrap_database_errors:
            self.connection.connection.autocommit = autocommit

    def is_usable(self):
        # https://github.com/kennethreitz/django-postgrespool/issues/24
        return self.connection.is_valid
