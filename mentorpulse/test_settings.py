from .settings import *

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
# Keep test uploads separate from user resources.
MEDIA_ROOT = BASE_DIR / '.test-media'
