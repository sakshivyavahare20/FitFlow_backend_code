from rest_framework import serializers
from .models import FitnessRecommendation, FitnessInput

class FitnessInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessInput
        exclude = ['created_at']

class FitnessRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessRecommendation
        fields = '__all__'
