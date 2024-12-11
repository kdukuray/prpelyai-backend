from rest_framework.serializers import ModelSerializer
from .models import PracticeTest

class PracticeTestSerializer(ModelSerializer):
    class Meta:
        model = PracticeTest
        fields = ["id", "nav_summary"]