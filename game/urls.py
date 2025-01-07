# game/urls.py
from django.urls import path
from .views import (
    MatchQueueView,
    MatchDetailView,
    MatchAnswerView,
    MatchForfeitView,
    MyMatchesView
)

urlpatterns = [
    # 매칭 대기열
    path('queue/', MatchQueueView.as_view(), name='match_queue'),

    # 매치 상세조회
    path('matches/<int:match_id>/', MatchDetailView.as_view(), name='match_detail'),

    # 정답 제출
    path('matches/<int:match_id>/answer/', MatchAnswerView.as_view(), name='match_answer'),

    # 새로 만든 강제 종료/포기 엔드포인트
    path('matches/<int:match_id>/forfeit/', MatchForfeitView.as_view(), name='match_forfeit'),
    
    path('my-matches/', MyMatchesView.as_view(), name='my-matches')
    
]
