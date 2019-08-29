from django.urls import path, include
from MiniContest.contest import views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'scoreboard', views.ScoreboardView)
router.register(r'purchase-problem', views.PurchaseProblemView)

urlpatterns = router.urls
