# app_name/urls.py
from django.urls import path
from .views import trending_videos
from . import views  # 현재 앱의 views.py에서 함수를 가져옵니다.

urlpatterns = [
    path('trending-videos/', trending_videos, name='trending_videos'), # URL과 View 연결
]
