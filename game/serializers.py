# game/serializers.py
from rest_framework import serializers
from .models import Problem, Match

class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['id', 'question']
        # answer는 노출하지 않음

class MatchSerializer(serializers.ModelSerializer):
    # problem 정보를 읽기 전용으로 일부만 노출
    problem = ProblemSerializer(read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'player1', 'player2', 'problem', 'winner', 'started_at', 'ended_at', 'status']
        read_only_fields = ['winner', 'started_at', 'ended_at']
