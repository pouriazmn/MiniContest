from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView
from django.http import HttpResponseRedirect
from .serializers import *
from .models import *
from .forms import RequestProblemForm


class ScoreboardView(generics.ListAPIView):
    serializer_class = TeamSerializers
    queryset = Team.objects.all()
