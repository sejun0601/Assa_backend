# app_name/views.py
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from shorts.models import Video, VideoStatsHistory

def video_growth_view(request):
    """
    어제 대비 오늘 증가율이 큰 순서로 비디오 리스트를 보여주는 예시
    """
    now = timezone.now()
    yesterday = now - timedelta(days=1)

    # 어제와 오늘 사이에 수집된 이력
    # (실제 운영 시에는 정확히 '어제'에 수집된 자료를 가져오는 방식으로 수정 필요)
    today_stats = VideoStatsHistory.objects.filter(collected_at__date=now.date())
    yesterday_stats = VideoStatsHistory.objects.filter(collected_at__date=yesterday.date())

    # 각 비디오별로 어제, 오늘 데이터 매핑
    growth_data = []
    for video in Video.objects.all():
        today_stat = today_stats.filter(video=video).order_by('-collected_at').first()
        yesterday_stat = yesterday_stats.filter(video=video).order_by('-collected_at').first()

        if today_stat and yesterday_stat:
            view_diff = today_stat.view_count - yesterday_stat.view_count
            like_diff = today_stat.like_count - yesterday_stat.like_count
            growth_data.append({
                'video': video,
                'view_diff': view_diff,
                'like_diff': like_diff,
            })

    # 조회수 증가량 기준으로 내림차순 정렬
    growth_data.sort(key=lambda x: x['view_diff'], reverse=True)

    context = {
        'growth_data': growth_data,
    }
    return render(request, '../templates/video_growth_list.html', context)
