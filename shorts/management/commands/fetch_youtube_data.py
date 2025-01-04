import logging
import math
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.utils.timezone import now
from shorts.models import Video, VideoStatsHistory

logger = logging.getLogger(__name__)

def calculate_trend_score(view_diff, like_diff, age_in_hours, w_v=1.0, w_l=2.0):
    """
    트렌드 점수를 계산하는 함수
    :param view_diff: 조회수 증가량
    :param like_diff: 좋아요 증가량
    :param age_in_hours: 영상이 게시된 후 경과 시간 (단위: 시간)
    :param w_v: 조회수 가중치
    :param w_l: 좋아요 가중치
    :return: 트렌드 점수
    """
    if age_in_hours <= 0:
        age_in_hours = 1  # 0으로 나누는 문제 방지

    return (view_diff * w_v + like_diff * w_l) / math.sqrt(age_in_hours)

class Command(BaseCommand):
    help = '유튜브 영상 정보를 주기적으로 수집하여 DB에 저장합니다.'

    def handle(self, *args, **options):
        """
        1. 저장해둔 Video 리스트를 불러옴
        2. 유튜브 API를 통해 각 영상의 통계 정보 조회
        3. 통계 정보를 업데이트하고 VideoStatsHistory에 기록
        4. 추가로 새로운 영상 50개를 불러와 저장
        5. 증가율 계산 및 트렌드 점수 정렬 후 저장
        """
        # 이미 저장된 Video 리스트를 불러오기
        existing_videos = Video.objects.all()

        # 구글 API 클라이언트 초기화
        youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_DATA_API_KEY)

        # 영상 정보를 담을 임시 리스트
        updated_videos = []

        # 기존 영상 업데이트
        for video in existing_videos:
            try:
                response = youtube.videos().list(
                    part="statistics,snippet",
                    id=video.video_id
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
                video=video,
                view_count=new_view_count,
                like_count=new_like_count
            )

            # 증가량 계산
            view_diff = new_view_count - old_view_count
            like_diff = new_like_count - old_like_count

            # 트렌드 점수 계산
            age_in_hours = (now() - video.published_at).total_seconds() / 3600
            trend_score = calculate_trend_score(view_diff, like_diff, age_in_hours)

            video.view_diff = view_diff
            video.like_diff = like_diff
            video.trend_score = trend_score  # 모델에 trend_score 필드 추가 필요
            video.save()

            updated_videos.append({
                'video': video,
                'trend_score': trend_score
            })

        # 새로운 영상 50개 추가 (예: 특정 채널 ID를 기준으로 검색)
        try:
            search_response = youtube.search().list(
                part="snippet",
                maxResults=50,
                order="date",
                regionCode="KR",
                type="video",
                videoDuration = "short",
                relevanceLanguage = "ko"
            ).execute()

            for item in search_response.get('items', []):
                video_id = item['id'].get('videoId')
                if not video_id:
                    continue

                # 중복 방지: 이미 DB에 있는 video_id는 제외
                if Video.objects.filter(video_id=video_id).exists():
                    continue

                snippet = item['snippet']

                # 새로운 영상 저장
                new_video = Video.objects.create(
                    video_id=video_id,
                    title=snippet.get('title'),
                    description=snippet.get('description'),
                    published_at=snippet.get('publishedAt'),
                )

                # 초기 통계 정보 가져오기
                try:
                    stats_response = youtube.videos().list(
                        part="statistics",
                        id=video_id
                    ).execute()

                    stats = stats_response['items'][0]['statistics']
                    new_video.view_count = int(stats.get('viewCount', 0))
                    new_video.like_count = int(stats.get('likeCount', 0))

                    # 트렌드 점수 계산
                    published_at = new_video.published_at
                    if isinstance(published_at, str):
                        published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))

                    age_in_hours = (now() - published_at).total_seconds() / 3600
                    trend_score = calculate_trend_score(new_video.view_count, new_video.like_count, age_in_hours)

                    new_video.trend_score = trend_score
                    new_video.save()

                    # 이력 테이블에 초기 값 저장
                    VideoStatsHistory.objects.create(
                        video=new_video,
                        view_count=new_video.view_count,
                        like_count=new_video.like_count
                    )
                except HttpError as e:
                    logger.error(f"유튜브 API 호출 에러 (video_id: {video_id}): {e}")
                    continue

        except HttpError as e:
            logger.error(f"유튜브 API 검색 호출 에러: {e}")

        # 트렌드 점수 기준으로 정렬
        sorted_by_trend = sorted(updated_videos, key=lambda x: x['trend_score'], reverse=True)

        # 예시: 로그로 확인
        logger.info("트렌드 점수 순 정렬 (내림차순):")
        for idx, info in enumerate(sorted_by_trend, start=1):
            logger.info(f"{idx}. {info['video'].title} / trend_score={info['trend_score']}")

        self.stdout.write(self.style.SUCCESS('유튜브 데이터 수집, 트렌드 점수 계산 및 정렬 작업을 완료했습니다.'))
