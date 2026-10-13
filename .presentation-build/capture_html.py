import os, sys, urllib.request, re
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
os.environ['DJANGO_SETTINGS_MODULE'] = 'mentorpulse.settings'
import django
from django.conf import settings
settings.DATABASES['default']['NAME'] = root / '.presentation-build' / 'demo.sqlite3'
settings.ALLOWED_HOSTS = ['testserver']
django.setup()
from django.test import Client
from django.contrib.auth.models import User
client = Client()
client.force_login(User.objects.get(username='alex_learner'))
for name, route in [('dashboard','/'),('directory','/mentors/'),('workspace','/mentorships/1/'),('wallet','/wallet/'),('notifications','/notifications/'),('certificate','/mentorships/2/certificate/')]:
    if name == 'certificate': client.force_login(User.objects.get(username='priya_learner'))
    response = client.get(route)
    assert response.status_code == 200, (name,response.status_code)
    html = response.content.decode().replace('/static/css/main.css',(root/'static/css/main.css').as_uri())
    for url, filename in [('https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css','bootstrap.css'),('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css','icons.css')]:
        dest=root/'.presentation-build'/filename
        if not dest.exists():
            try: urllib.request.urlretrieve(url,dest)
            except Exception as e: print(str(e))
        if dest.exists(): html=html.replace(url,dest.as_uri())
    html=re.sub(r'\s+(?:integrity|crossorigin)="[^"]*"','',html)
    (root/'.presentation-build'/f'{name}.html').write_text(html,encoding='utf-8')
    print(name, 'saved')
