from django.urls import path
from .views import FitnessRecommendationAPI

urlpatterns = [
    path('', FitnessRecommendationAPI.as_view(), name='fitness_recommendation'),
]
