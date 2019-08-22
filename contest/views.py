from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView

from .serializers import *
from .models import *

class ScoreboardView(generics.ListAPIView):
    serializer_class = TeamSerializers
    queryset = Team.objects.all()


class DuelRequestView(generics.ListCreateAPIView):
    serializer_class = DuelSerializer
    queryset = Duel.objects.all()


class SolveAttemptView(generics.ListCreateAPIView):
    serializer_class = SolvingAttemptSerializer
    queryset = SolvingAttempt.objects.all()


class SetProblemTime(APIView):
    def put(self, request, *args, **kwargs):
        id = request.data.get('id')
        sa = SolvingAttemptSerializer.get(id=id)
        sa.end_time = timezone.now()
        sa.save()
