.. image:: https://badge.fury.io/py/django-postgrespool2.svg
    :target: https://badge.fury.io/py/django-postgrespool2

Django-PostgresPool2
====================

This is a fork of original `django-postgrespool <https://github.com/kennethreitz/django-postgrespool>`_.


Installation
------------

Installing Django-PostgresPool2 is simple, with pip::

    $ pip install django-postgrespool2


Usage
-----

Using Django-PostgresPool2 is simple, just set ``django_postgrespool2`` as your connection engine:

::

    DATABASES = {
        'default': {
            'ENGINE': 'django_postgrespool2'


If you're using the `dj-database-url <https://github.com/kennethreitz/dj-database-url>`_ module:

::

    import dj_database_url

    DATABASES = {'default': dj_database_url.config(engine='django_postgrespool2')}


Everything should work as expected.

Configuration
-------------

Optionally, you can provide additional options to pass to SQLAlchemy's pool creation::

    DATABASE_POOL_ARGS = {
        'max_overflow': 10,
        'pool_size': 5,
        'recycle': 300
    }

Here's a basic explanation of two of these options:

* **pool_size** – The *minimum* number of connections to maintain in the pool.
* **max_overflow** – The maximum *overflow* size of the pool. This is not the maximum size of the pool.

The total number of "sleeping" connections the pool will allow is ``pool_size``.
The total simultaneous connections the pool will allow is ``pool_size + max_overflow``.

As an example, databases in the `Heroku Postgres <https://postgres.heroku.com>`_ starter tier have a maximum connection limit of 20. In that case your ``pool_size`` and ``max_overflow``, when combined, should not exceed 20.

Check out the official `SQLAlchemy Connection Pooling <http://docs.sqlalchemy.org/en/latest/core/pooling.html#sqlalchemy.pool.QueuePool.__init__>`_ docs to learn more about the optoins that can be defined in ``DATABASE_POOL_ARGS``.
