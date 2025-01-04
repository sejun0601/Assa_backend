# app_name/models.py
from django.db import models

class Video(models.Model):
    """
    유튜브 영상 기본 정보 저장
    """
    video_id = models.CharField(max_length=50, unique=True)  # 유튜브 영상 ID
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    published_at = models.DateTimeField()  # 영상이 최초로 게시된 시간

    # 최신 통계 정보 (가장 최근 수집)
    view_count = models.BigIntegerField(default=0)
    like_count = models.BigIntegerField(default=0)
    view_diff = models.BigIntegerField(default=0)  # 조회수 증가량
    like_diff = models.BigIntegerField(default=0)  # 좋아요 증가량
    trend_score = models.BigIntegerField(default=0)

    def __str__(self):
        return self.title


class VideoStatsHistory(models.Model):
    """
    영상의 통계 정보 이력 저장 테이블
    주기적으로 수집할 때마다 저장
    """
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='stats_history')
    collected_at = models.DateTimeField(auto_now_add=True)  # 통계를 수집한 시각
    view_count = models.BigIntegerField(default=0)
    like_count = models.BigIntegerField(default=0)
    trend_score = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.video.title} / {self.collected_at}"
