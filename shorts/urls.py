# app_name/urls.py
from django.urls import path
from . import views  # 현재 앱의 views.py에서 함수를 가져옵니다.

urlpatterns = [
    path('video-growth/', views.video_growth_view, name='video_growth'),  # URL과 View 연결
]
