import django

SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django_postgrespool2',
        'NAME': 'postgrespool_test',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'localhost',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.admin',
    'tests',
]

if django.VERSION[:2] < (1, 6):
    TEST_RUNNER = 'discover_runner.DiscoverRunner'

SECRET_KEY = 'local'
