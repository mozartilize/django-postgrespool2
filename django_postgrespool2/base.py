# -*- coding: utf-8 -*-
from importlib import import_module
import logging
from functools import partial

from sqlalchemy import event
from sqlalchemy.pool import manage
from sqlalchemy.dialects import postgresql
from django.dispatch import Signal
from django.conf import settings

if 'Psycopg2DatabaseWrapper' not in globals():
    try:
        # Django >= 1.9
        from django.db.backends.postgresql.base import (
            psycopg2,
            Database,
            DatabaseWrapper as Psycopg2DatabaseWrapper,
        )
        from django.db.backends.postgresql.creation import (
            DatabaseCreation as Psycopg2DatabaseCreation,
        )
        from django.db.backends.postgresql.utils import utc_tzinfo_factory
    except ImportError:
        from django.db.backends.postgresql_psycopg2.base import (
            psycopg2,
            Database,
            DatabaseWrapper as Psycopg2DatabaseWrapper,
        )
        from django.db.backends.postgresql_psycopg2.creation import (
            DatabaseCreation as Psycopg2DatabaseCreation,
        )
        from django.db.backends.postgresql_psycopg2.utils import utc_tzinfo_factory


# DATABASE_POOL_ARGS should be something like:
# {'max_overflow':10, 'pool_size':5, 'recycle':300}
pool_args = {'max_overflow': 10, 'pool_size': 5, 'recycle': 300}
pool_args.update(getattr(settings, 'DATABASE_POOL_ARGS', {}))
dialect = postgresql.dialect(dbapi=psycopg2)
pool_args['dialect'] = dialect

POOL_CLS = getattr(settings, 'DATABASE_POOL_CLASS', 'sqlalchemy.pool.QueuePool')
pool_module_name, pool_cls_name = POOL_CLS.rsplit('.', 1)
pool_cls = getattr(import_module(pool_module_name), pool_cls_name)
pool_args['poolclass'] = pool_cls

db_pool = manage(Database, **pool_args)
pool_disposed = Signal(providing_args=["connection"])

log = logging.getLogger('z.pool')


def _log(message, *args):
    log.debug(message)


# Only hook up the listeners if we are in debug mode.
if settings.DEBUG:
    event.listen(pool_cls, 'checkout', partial(_log, 'retrieved from pool'))
    event.listen(pool_cls, 'checkin', partial(_log, 'returned to pool'))
    event.listen(pool_cls, 'connect', partial(_log, 'new connection'))


class DatabaseCreation(Psycopg2DatabaseCreation):
    def _clone_test_db(self, *args, **kw):
        self.connection.dispose()
        super(DatabaseCreation, self)._clone_test_db(*args, **kw)

    def create_test_db(self, *args, **kw):
        self.connection.dispose()
        super(DatabaseCreation, self).create_test_db(*args, **kw)

    def destroy_test_db(self, *args, **kw):
        """Ensure connection pool is disposed before trying to drop database.
        """
        self.connection.dispose()
        super(DatabaseCreation, self).destroy_test_db(*args, **kw)


class DatabaseWrapper(Psycopg2DatabaseWrapper):
    """SQLAlchemy FTW."""

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self._pool = None
        self._pool_connection = None
        self.creation = DatabaseCreation(self)

    @property
    def pool(self):
        return self._pool

    def _close(self):
        if self._pool_connection is not None:
            with self.wrap_database_errors:
                return self._pool_connection.close()

    def create_cursor(self, name=None):
        if name:
            # In autocommit mode, the cursor will be used outside of a
            # transaction, hence use a holdable cursor.
            cursor = self._pool_connection.cursor(
                name, scrollable=False, withhold=self.connection.autocommit)
        else:
            cursor = self._pool_connection.cursor()
        cursor.tzinfo_factory = utc_tzinfo_factory if settings.USE_TZ else None
        return cursor

    def dispose(self):
        """Dispose of the pool for this instance, closing all connections.
        """
        self.close()
        self._pool_connection = None
        # _DBProxy.dispose doesn't actually call dispose on the pool
        if self.pool:
            self.pool.dispose()
            self._pool = None
        conn_params = self.get_connection_params()
        db_pool.dispose(**conn_params)
        pool_disposed.send(sender=self.__class__, connection=self)

    def get_new_connection(self, conn_params):
        if not self._pool:
            self._pool = db_pool.get_pool(**conn_params)
        # get new connection through pool, not creating a new one outside.
        self._pool_connection = self.pool.connect()
        c = self._pool_connection.connection  # dbapi connection

        options = self.settings_dict['OPTIONS']
        try:
            self.isolation_level = options['isolation_level']
        except KeyError:
            self.isolation_level = c.isolation_level
        else:
            # Set the isolation level to the value from OPTIONS.
            if self.isolation_level != c.isolation_level:
                c.set_session(isolation_level=self.isolation_level)

        return c

    def is_usable(self):
        # https://github.com/kennethreitz/django-postgrespool/issues/24
        if self._pool_connection is None:
            return False
        return self._pool_connection.is_valid
