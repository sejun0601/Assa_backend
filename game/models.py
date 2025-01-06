# game/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Problem(models.Model):
    question = models.TextField()
    answer = models.CharField(max_length=255)

    def __str__(self):
        return f"Problem {self.id}"

class Match(models.Model):
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player1_matches')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player2_matches')
    problem = models.ForeignKey(Problem, on_delete=models.SET_NULL, null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_matches')
    
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    MATCH_STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('finished', 'Finished'),   # 승자가 정해져 끝난 경우
        ('forfeited', 'Forfeited'), # 기권/강제종료 등
        ('draw', 'Draw'),           # 무승부
    ]
    status = models.CharField(max_length=10, choices=MATCH_STATUS_CHOICES, default='ongoing')

    def __str__(self):
        w = self.winner.username if self.winner else "No winner"
        return f"Match {self.id}: {self.player1.username} vs {self.player2.username} (Winner: {w}, Status: {self.status})"


class MatchQueue(models.Model):
    """
    매칭 대기열: 유저가 매칭을 누르면 이 테이블에 등록.
    두 명이 매칭되면, 양쪽 대기열을 제거하고 Match를 생성.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in queue"