from __future__ import absolute_import, unicode_literals

# Celery 앱 임포트
from .celery import app as celery_app

__all__ = ('celery_app',)
