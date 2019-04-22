import unittest
try:
    from unittest import mock
except ImportError:
    import mock
import warnings

from django.db import DatabaseError, connection
from django.test import TestCase
from django import VERSION as dj_version

if (1, 8) <= dj_version < (1, 9):
    import copy
    from django.conf import settings
    from django.db import DEFAULT_DB_ALIAS
    from django.db.utils import ConnectionHandler

    def clone_connection():
        databases = copy.deepcopy(settings.DATABASES)
        new_connections = ConnectionHandler(databases)
        new_connection = new_connections[DEFAULT_DB_ALIAS]
        return new_connection

    connection.copy = clone_connection


@unittest.skipUnless(connection.vendor == 'postgresql', 'PostgreSQL tests')
class Tests(TestCase):

    def test_nodb_connection(self):
        """
        Test that the _nodb_connection property fallbacks to the default connection
        database when access to the 'postgres' database is not granted.
        """
        def mocked_connect(self):
            if self.settings_dict['NAME'] is None:
                raise DatabaseError()
            return ''

        nodb_conn = connection._nodb_connection
        self.assertIsNone(nodb_conn.settings_dict['NAME'])

        # Now assume the 'postgres' db isn't available
        if (1, 8) <= dj_version < (1, 9):
            del connection._nodb_connection
        with warnings.catch_warnings(record=True) as w:
            with mock.patch('django.db.backends.base.base.BaseDatabaseWrapper.connect',
                            side_effect=mocked_connect, autospec=True):
                warnings.simplefilter('always', RuntimeWarning)
                nodb_conn = connection._nodb_connection
        if (1, 8) <= dj_version < (1, 9):
            del connection._nodb_connection
        self.assertIsNotNone(nodb_conn.settings_dict['NAME'])
        self.assertEqual(nodb_conn.settings_dict['NAME'], connection.settings_dict['NAME'])
        # Check a RuntimeWarning nas been emitted
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0].message.__class__, RuntimeWarning)

    def test_connect_and_rollback(self):
        """
        PostgreSQL shouldn't roll back SET TIME ZONE, even if the first
        transaction is rolled back (#17062).
        """
        new_connection = connection.copy()
        try:
            # Ensure the database default time zone is different than
            # the time zone in new_connection.settings_dict. We can
            # get the default time zone by reset & show.
            with new_connection.cursor() as cursor:
                cursor.execute("RESET TIMEZONE")
                cursor.execute("SHOW TIMEZONE")
                db_default_tz = cursor.fetchone()[0]
            new_tz = 'Europe/Paris' if db_default_tz == 'UTC' else 'UTC'
            new_connection.close()

            if hasattr(new_connection, 'timezone_name'):  # django 1.8
                # Invalidate timezone name cache, because the setting_changed
                # handler cannot know about new_connection.
                del new_connection.timezone_name

            # Fetch a new connection with the new_tz as default
            # time zone, run a query and rollback.
            with self.settings(TIME_ZONE=new_tz):
                if (1, 8) <= dj_version < (1, 9):
                    new_connection.settings_dict['TIME_ZONE'] = new_tz
                new_connection.set_autocommit(False)
                new_connection.rollback()

                # Now let's see if the rollback rolled back the SET TIME ZONE.
                with new_connection.cursor() as cursor:
                    cursor.execute("SHOW TIMEZONE")
                    tz = cursor.fetchone()[0]
                self.assertEqual(new_tz, tz)

        finally:
            new_connection.dispose()

    def test_connect_non_autocommit(self):
        """
        The connection wrapper shouldn't believe that autocommit is enabled
        after setting the time zone when AUTOCOMMIT is False (#21452).
        """
        new_connection = connection.copy()
        new_connection.settings_dict['AUTOCOMMIT'] = False

        try:
            # Open a database connection.
            new_connection.cursor()
            self.assertFalse(new_connection.get_autocommit())
        finally:
            new_connection.dispose()

    def test_connect_isolation_level(self):
        """
        The transaction level can be configured with
        DATABASES ['OPTIONS']['isolation_level'].
        """
        import psycopg2
        from psycopg2.extensions import (
            ISOLATION_LEVEL_READ_COMMITTED as read_committed,
            ISOLATION_LEVEL_SERIALIZABLE as serializable,
        )
        # Since this is a django.test.TestCase, a transaction is in progress
        # and the isolation level isn't reported as 0. This test assumes that
        # PostgreSQL is configured with the default isolation level.

        # Check the level on the psycopg2 connection, not the Django wrapper.
        default_level = read_committed if psycopg2.__version__ < '2.7' else None
        self.assertEqual(connection.connection.isolation_level, default_level)

        new_connection = connection.copy()
        new_connection.settings_dict['OPTIONS']['isolation_level'] = serializable
        try:
            # Start a transaction so the isolation level isn't reported as 0.
            new_connection.set_autocommit(False)
            # Check the level on the psycopg2 connection, not the Django wrapper.
            self.assertEqual(new_connection.connection.isolation_level, serializable)
        finally:
            new_connection.dispose()

    def test_connect_no_is_usable_checks(self):
        new_connection = connection.copy()
        with mock.patch.object(new_connection, 'is_usable') as is_usable:
            new_connection.connect()
        is_usable.assert_not_called()
        new_connection.dispose()
