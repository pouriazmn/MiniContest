from django.urls import path, include
from contest import views

urlpatterns = [
    path('scoreboard/', views.ScoreboardView.as_view()),
    path('duels/', views.DuelRequestView.as_view()),
    path('get-problem', views.SolveAttemptView.as_view()),
]
