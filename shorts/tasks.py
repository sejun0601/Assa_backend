import logging
import math
from datetime import datetime
from django.utils.timezone import now
from celery import shared_task
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from shorts.models import Video, VideoStatsHistory
from django.conf import settings

logger = logging.getLogger(__name__)


def calculate_trend_score(view_diff, like_diff, age_in_hours, w_v=1.0, w_l=2.0):
    if age_in_hours <= 0:
        age_in_hours = 1  # 0으로 나누는 문제 방지

    return (view_diff * w_v + like_diff * w_l) / math.sqrt(age_in_hours)


@shared_task
def fetch_youtube_data():
    # 유튜브 API 클라이언트 초기화
    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_DATA_API_KEY)
    updated_videos = []

    # 기존 Video 업데이트
    existing_videos = Video.objects.all()
    for video in existing_videos:
        try:
            response = youtube.videos().list(
                part="statistics,snippet", id=video.video_id
            ).execute()
        except HttpError as e:
            logger.error(f"유튜브 API 호출 에러 (video_id: {video.video_id}): {e}")
            continue

        items = response.get('items', [])
        if not items:
            logger.warning(f"해당 video_id {video.video_id}로 정보를 찾을 수 없습니다.")
            continue

        item = items[0]
        stats = item['statistics']

        # DB 최신 영상 정보 업데이트
        old_view_count = video.view_count
        old_like_count = video.like_count

        new_view_count = int(stats.get('viewCount', 0))
        new_like_count = int(stats.get('likeCount', 0))

        video.view_count = new_view_count
        video.like_count = new_like_count
        video.title = item['snippet']['title']
        video.description = item['snippet']['description']

        video.save()

        # 이력 테이블에 저장
        VideoStatsHistory.objects.create(
            video=video, view_count=new_view_count, like_count=new_like_count
        )

        # 증가량 계산
        view_diff = new_view_count - old_view_count
        like_diff = new_like_count - old_like_count

        # 트렌드 점수 계산
        age_in_hours = (now() - video.published_at).total_seconds() / 3600
        trend_score = calculate_trend_score(view_diff, like_diff, age_in_hours)

        video.view_diff = view_diff
        video.like_diff = like_diff
        video.trend_score = trend_score
        video.save()

        updated_videos.append({"video": video, "trend_score": trend_score})

    logger.info("유튜브 데이터 업데이트 완료")

    # 새로운 영상 검색 및 추가
    try:
        search_response = youtube.search().list(
            part="snippet",
            maxResults=50,
            order="date",
            regionCode="KR",
            type="video",
            videoDuration="short",
            relevanceLanguage="ko",
        ).execute()

        for item in search_response.get('items', []):
            video_id = item['id'].get('videoId')
            if not video_id or Video.objects.filter(video_id=video_id).exists():
                continue

            snippet = item['snippet']
            new_video = Video.objects.create(
                video_id=video_id,
                title=snippet.get('title'),
                description=snippet.get('description'),
                published_at=snippet.get('publishedAt'),
            )

            # 초기 통계 정보 가져오기
            try:
                stats_response = youtube.videos().list(
                    part="statistics", id=video_id
                ).execute()

                stats = stats_response['items'][0]['statistics']
                new_video.view_count = int(stats.get('viewCount', 0))
                new_video.like_count = int(stats.get('likeCount', 0))

                age_in_hours = (
                    now() - datetime.fromisoformat(new_video.published_at.replace('Z', '+00:00'))
                ).total_seconds() / 3600
                trend_score = calculate_trend_score(new_video.view_count, new_video.like_count, age_in_hours)

                new_video.trend_score = trend_score
                new_video.save()

                # 이력 테이블에 초기 값 저장
                VideoStatsHistory.objects.create(
                    video=new_video,
                    view_count=new_video.view_count,
                    like_count=new_video.like_count,
                )
            except HttpError as e:
                logger.error(f"유튜브 API 호출 에러 (video_id: {video_id}): {e}")
                continue

    except HttpError as e:
        logger.error(f"유튜브 API 검색 호출 에러: {e}")

    logger.info("새로운 유튜브 영상 추가 완료")
