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
        existing_videos = Video.objects.only('video_id', 'view_count', 'like_count', 'published_at')

        # 구글 API 클라이언트 초기화
        youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_DATA_API_KEY)

        # 기존 영상 업데이트
        video_ids = [video.video_id for video in existing_videos]
        batch_size = 50

        for i in range(0, len(video_ids), batch_size):
            batch_ids = video_ids[i:i + batch_size]
            try:
                response = youtube.videos().list(
                    part="statistics,snippet",
                    id=",".join(batch_ids)
                ).execute()
            except HttpError as e:
                logger.error(f"유튜브 API 호출 에러 (batch_ids: {batch_ids}): {e}")
                continue

            for item in response.get('items', []):
                video_id = item['id']
                video = Video.objects.get(video_id=video_id)

                stats = item['statistics']
                snippet = item['snippet']

                old_view_count = video.view_count
                old_like_count = video.like_count

                new_view_count = int(stats.get('viewCount', 0))
                new_like_count = int(stats.get('likeCount', 0))

                video.view_count = new_view_count
                video.like_count = new_like_count
                video.title = snippet['title']
                video.description = snippet['description']
                video.save()

                VideoStatsHistory.objects.create(
                    video=video,
                    view_count=new_view_count,
                    like_count=new_like_count
                )

                view_diff = new_view_count - old_view_count
                like_diff = new_like_count - old_like_count

                age_in_hours = (now() - video.published_at).total_seconds() / 3600
                trend_score = calculate_trend_score(view_diff, like_diff, age_in_hours)

                video.trend_score = trend_score
                video.save()

        # 새로운 영상 50개 추가
        try:
            search_response = youtube.search().list(
                part="snippet",
                maxResults=50,
                order="date",
                regionCode="KR",
                type="video",
                videoDuration="short",
                relevanceLanguage="ko"
            ).execute()

            new_video_ids = [
                item['id']['videoId']
                for item in search_response.get('items', [])
                if not Video.objects.filter(video_id=item['id']['videoId']).exists()
            ]

            for i in range(0, len(new_video_ids), batch_size):
                batch_ids = new_video_ids[i:i + batch_size]

                try:
                    stats_response = youtube.videos().list(
                        part="statistics,snippet",
                        id=",".join(batch_ids)
                    ).execute()

                    for item in stats_response.get('items', []):
                        video_id = item['id']
                        snippet = item['snippet']
                        stats = item['statistics']

                        new_video = Video.objects.create(
                            video_id=video_id,
                            title=snippet.get('title'),
                            description=snippet.get('description'),
                            published_at=snippet.get('publishedAt'),
                            view_count=int(stats.get('viewCount', 0)),
                            like_count=int(stats.get('likeCount', 0)),
                            trend_score=calculate_trend_score(
                                int(stats.get('viewCount', 0)),
                                int(stats.get('likeCount', 0)),
                                (now() - datetime.fromisoformat(snippet.get('publishedAt').replace('Z', '+00:00'))).total_seconds() / 3600
                            )
                        )
                        new_video.save()

                        VideoStatsHistory.objects.create(
                            video=new_video,
                            view_count=new_video.view_count,
                            like_count=new_video.like_count
                        )

                except HttpError as e:
                    logger.error(f"유튜브 API 호출 에러 (batch_ids: {batch_ids}): {e}")
                    continue

        except HttpError as e:
            logger.error(f"유튜브 API 검색 호출 에러: {e}")

        self.stdout.write(self.style.SUCCESS('유튜브 데이터 수집 및 업데이트 작업을 완료했습니다.'))
