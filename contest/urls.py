from django.urls import path, include
from contest import views

urlpatterns = [
    path('scoreboard/', views.ScoreboardView.as_view()),
]
