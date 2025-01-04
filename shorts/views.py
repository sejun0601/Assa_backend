from django.http import JsonResponse
from shorts.models import Video

def trending_videos(request):
    """
    트렌드 점수 기준으로 정렬된 영상 목록을 반환
    """
    limit = request.GET.get('limit', 10)  # 쿼리 매개변수에서 'limit' 값을 가져옴 (기본값: 10)
    try:
        limit = int(limit)  # limit 값을 정수로 변환
    except ValueError:
        return JsonResponse({'error': 'Invalid limit value'}, status=400)

    # 트렌드 점수 기준 정렬 및 limit에 따른 제한
    videos = Video.objects.order_by('-trend_score')[:limit]
    data = [
        {
            'video_id': video.video_id,
            'title': video.title,
            'description': video.description,
            'trend_score': video.trend_score,
            'view_count': video.view_count,
            'like_count': video.like_count,
            'published_at': video.published_at,
        }
        for video in videos
    ]
    return JsonResponse(data, safe=False)
