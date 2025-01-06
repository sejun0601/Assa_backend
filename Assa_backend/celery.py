from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django의 기본 설정 모듈 환경 변수 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Assa_backend.settings')

# Celery 애플리케이션 생성
app = Celery('Assa_backend')

# Django 설정에서 Celery 구성 읽기
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 작업 모듈 자동 검색
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
