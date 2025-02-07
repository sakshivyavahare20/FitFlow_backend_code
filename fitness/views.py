from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FitnessInput, FitnessRecommendation
import google.generativeai as genai
import os
from .serializers import FitnessInputSerializer, FitnessRecommendationSerializer
from dotenv import load_dotenv

load_dotenv()

def calculate_bmi(weight, height):
    height_m = height / 100.0
    bmi = weight / (height_m ** 2)
    
    if bmi < 18.5:
        category = 'Underweight'
    elif 18.5 <= bmi < 24.9:
        category = 'Normal weight'
    elif 25 <= bmi < 29.9:
        category = 'Overweight'
    else:
        category = 'Obesity'
    
    return bmi, category

class FitnessRecommendationAPI(APIView):
    def post(self, request):
        serializer = FitnessInputSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            bmi, bmi_category = calculate_bmi(profile.weight, profile.height)
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-pro")

            prompt = f"""
            As an expert fitness trainer, create a personalized fitness plan for:

            Age: {profile.age}
            Gender: {profile.gender}
            Weight: {profile.weight} kg
            Height: {profile.height} cm
            Goal: {profile.goal}
            Fitness Level: {profile.fitness_level}
            Activity Level: {profile.activity_level}
            Exercise Setting: {profile.exercise_setting}
            Sleep Pattern: {profile.sleep_pattern}
            Focus Areas: {profile.specific_area}
            Target Timeline: {profile.target_timeline}
            Medical Conditions: {profile.medical_conditions}
            Injuries: {profile.injuries_or_physical_limitation}

            Ensure the plan includes:
            - Detailed exercise descriptions
            - Proper warm-up and cool-down routines
            - Safety precautions
            - Modifications for different fitness levels
            - Recovery protocols
            - Progress tracking

            Please format the response in a clean, easy-to-read format.
            """

            response = model.generate_content(prompt)
            recommendation_text = response.text.replace('*', '').replace('#', '').replace('', '')

            fitness_recommendation = FitnessRecommendation.objects.create(
                profile=profile,
                recommendation_text=recommendation_text,
                bmi=bmi,
                bmi_category=bmi_category
            )

            recommendation_serializer = FitnessRecommendationSerializer(fitness_recommendation)
            return Response(recommendation_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
