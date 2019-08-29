from django.http import HttpResponseRedirect
from django.shortcuts import render
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import RequestProblemForm
from .models import *
from .serializers import *


class ScoreboardView(viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = TeamSerializers
    queryset = Team.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = self.get_serializer(queryset, many=True).data
        for ind, each in enumerate(data):
            each['rank'] = ind+1
        return Response(data)


class PurchaseProblemView(viewsets.ViewSetMixin, generics.CreateAPIView):
    serializer_class = ProblemSerializer
    queryset = Problem.objects.all()
