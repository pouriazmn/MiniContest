from django.utils import timezone
from rest_framework import serializers
from .models import *


class SolvingAttemptSerializer(serializers.ModelSerializer):
    team_id = serializers.IntegerField(write_only=True, required=True)
    problem_id = serializers.IntegerField(write_only=True, required=True)
    start_time = serializers.DateTimeField(read_only=True, required=False)

    class Meta:
        model = SolvingAttempt
        fields = '__all__'
        depth = 1

    def create(self, validated_data):
        sa = SolvingAttempt(team_id=validated_data['team_id'],
                            problem_id=validated_data['problem_id'],
                            start_time=timezone.now())
        sa.save()
        return sa


class ProblemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Problem
        fields = '__all__'


class TeamSerializers(serializers.ModelSerializer):
    pending_duels = serializers.IntegerField(read_only='True')

    class Meta:
        model = Team
        fields = '__all__'


class DuelSerializer(serializers.ModelSerializer):
    requested_by_id = serializers.IntegerField(write_only=True, required=True)
    to_id = serializers.IntegerField(write_only=True, required=True)
    problem_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Duel
        fields = '__all__'
        read_only_fields = ('worth', 'pending')
        depth = 1

    def create(self, validated_data):
        d = Duel(**validated_data)
        d.save()
        return d
