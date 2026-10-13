import os
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
os.environ['DJANGO_SETTINGS_MODULE'] = 'mentorpulse.settings'
from django.conf import settings
settings.DATABASES['default']['NAME'] = root / '.presentation-build' / 'demo.sqlite3'
settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8123', '--noreload'])
