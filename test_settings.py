import logging


logging.disable(logging.CRITICAL)

INSTALLED_APPS = ('jsonview',)

SECRET_KEY = 'foo'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    },
}
