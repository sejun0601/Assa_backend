# game/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Problem, Match

User = get_user_model()

class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['id', 'question', 'answer']
        # answer는 노출하지 않음
        
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']  # Include any other fields you need
        
class MatchSerializer(serializers.ModelSerializer):
    # problem 정보를 읽기 전용으로 일부만 노출
    problem = ProblemSerializer(read_only=True)
    player1 = UserDetailSerializer(read_only=True)
    player2 = UserDetailSerializer(read_only=True)
    winner = UserDetailSerializer(read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'player1', 'player2', 'problem', 'winner', 'started_at', 'ended_at', 'status']
        read_only_fields = ['winner', 'started_at', 'ended_at']
