import time

# game/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q


from django.contrib.auth import get_user_model
User = get_user_model()

from .models import MatchQueue, Match, Problem
from .serializers import MatchSerializer
from accounts.models import Profile  # Profile 모델 임포트

# -----------------------------
#  A. 매칭 대기열 처리 (MatchQueue)
# -----------------------------
class MatchQueueView(APIView):
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "로그인 필요" , "matched": False}, status=status.HTTP_401_UNAUTHORIZED)

        # 1) 이미 진행 중인 매치가 있는지 확인
        ongoing_match = Match.objects.filter(
            Q(player1=user) | Q(player2=user),
            status='ongoing'
        ).first()
        if ongoing_match:
            return Response({
                    "detail": "매칭 완료",
                    "matched": True,
                    "match": MatchSerializer(ongoing_match).data
                }, status=status.HTTP_201_CREATED)

        # 2) 이미 대기열에 있는지 확인
        existing_queue = MatchQueue.objects.filter(user=user).first()
        if existing_queue:
            if existing_queue.match:  # 매칭이 이미 연결되어 있는 상태(매치가 존재)라면
                return Response({
                    "detail": "매칭이 이미 완료되었거나 연결되었습니다.",
                    "matched": True,
                    "match": MatchSerializer(existing_queue.match).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "이미 대기 중입니다.", "matched": False}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # 3) 다른 유저가 대기 중인지 확인
            waiting = MatchQueue.objects.exclude(user=user).order_by('created_at').first()
            if waiting:
                # 매칭 생성
                problem = Problem.objects.order_by('?').first()
                match = Match.objects.create(
                    player1=waiting.user,
                    player2=user,
                    problem=problem,
                    status='ongoing'  # 매치 시작 시 상태를 ongoing으로 설정
                )

                # 대기열에서 제거
                MatchQueue.objects.filter(user=waiting.user).delete()
                MatchQueue.objects.filter(user=user).delete()

                return Response({
                    "detail": "매칭 완료",
                    "matched": True,
                    "match": MatchSerializer(match).data
                }, status=status.HTTP_201_CREATED)
            else:
                # 4) 대기열에 추가하고 매칭을 기다림
                MatchQueue.objects.create(user=user)
                return Response({"detail": "대기열에 등록되었습니다.", "matched": False}, status=status.HTTP_200_OK)

# -----------------------------
#  B. 매치 상세 & 정답 제출
# -----------------------------
class MatchDetailView(APIView):
    """
    GET /api/game/matches/<match_id>/
      -> 매치 상세 정보 조회
    """
    def get(self, request, match_id):
        match = get_object_or_404(Match, id=match_id)
        serializer = MatchSerializer(match)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MatchAnswerView(APIView):
    """
    POST /api/game/matches/<match_id>/answer/
      body: { "answer": "사용자 제출 정답" }

    - winner가 이미 정해졌다면 -> "이미 끝났다" 메시지
    - 아직이라면 정답 검증 -> 맞으면 winner 설정
    """
    def post(self, request, match_id):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "로그인 필요"}, status=status.HTTP_200_OK)

        match = get_object_or_404(Match, id=match_id)

        if match.winner:
            return Response({
                "detail": "이미 승자가 결정되었습니다.",
                "winner": match.winner.username
            }, status=status.HTTP_200_OK)

        # 매치 플레이어인지 확인
        if user not in [match.player1, match.player2]:
            return Response({"detail": "해당 매치에 속한 유저가 아닙니다."},
                            status=status.HTTP_200_OK)

        answer = request.data.get("answer")
        if not answer:
            return Response({"detail": "answer 필드가 필요합니다."},
                            status=status.HTTP_200_OK)

        correct_answer = match.problem.answer if match.problem else None
        if correct_answer and (str(answer).strip().lower() == str(correct_answer).strip().lower()):
            # 정답 -> 승자 설정
            match.winner = user
            match.ended_at = timezone.now()
            match.status = 'finished'
            match.save()

            try:
                winner_profile = Profile.objects.get(user=user)  # 현재 정답 맞힌 유저의 프로필
                winner_profile.rank_score += 20
                winner_profile.win_count += 1
                winner_profile.save()
            except Profile.DoesNotExist:
                return Response({"detail": "승자의 프로필이 존재하지 않습니다."}, status=status.HTTP_200_OK)

            # 패배자의 프로필 업데이트
            loser = match.player1 if user == match.player2 else match.player2  # 상대방 유저
            try:
                loser_profile = Profile.objects.get(user=loser)  # 패배자의 프로필
                loser_profile.rank_score -= 20
                if loser_profile.rank_score < 0:
                    loser_profile.rank_score = 0
                loser_profile.lose_count += 1
                loser_profile.save()
            except Profile.DoesNotExist:
                return Response({"detail": "패배자의 프로필이 존재하지 않습니다."}, status=status.HTTP_200_OK)


            return Response({
                "detail": "정답! 승리했습니다.",
                "winner": user.username
            }, status=status.HTTP_200_OK)
        else:
            # 오답
            return Response({"detail": "틀렸습니다."}, status=status.HTTP_200_OK)


# game/views.py

class MatchForfeitView(APIView):
    """
    POST /api/game/matches/<match_id>/forfeit/
      - 승자가 안 나왔어도, 이 매치를 강제 종료하고 싶을 때
      - (혹은 본인이 포기하는 로직이라면 권한 체크 추가)
    """
    def post(self, request, match_id):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "로그인 필요"}, status=status.HTTP_401_UNAUTHORIZED)

        match = get_object_or_404(Match, id=match_id)

        # (선택) 본인이 player1 또는 player2인지 확인
        # if user not in [match.player1, match.player2]:
        #     return Response({"detail": "이 매치에 속한 유저가 아닙니다."}, status=403)

        # 이미 끝난 매치라면 종료
        if match.status != 'ongoing':
            return Response({"detail": f"이미 종료된 매치입니다. (status: {match.status})"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # 여기서 승자는 null(없음)으로 두고, status='forfeited'
        match.status = 'forfeited'
        match.ended_at = timezone.now()
        match.save()

        return Response({
            "detail": "매치가 강제 종료(포기)되었습니다.",
            "match_id": match.id,
            "status": match.status
        }, status=status.HTTP_200_OK)


class MyMatchesView(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "로그인 필요"}, status=status.HTTP_401_UNAUTHORIZED)

        # 현재 유저가 player1 또는 player2로 참가한 모든 매치를 가져옴
        my_matches = Match.objects.filter(Q(player1=user) | Q(player2=user)).order_by('-started_at')
        serializer = MatchSerializer(my_matches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)