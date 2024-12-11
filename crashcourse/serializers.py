from rest_framework.serializers import ModelSerializer
from .models import CrashCourse

class CrashCourseSerializer(ModelSerializer):
    class Meta:
        model = CrashCourse
        fields = ["id", "nav_summary"]