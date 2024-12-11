from django.db import models

class CrashCourse(models.Model):
    content = models.TextField()
    resources = models.TextField()
    generator_uuid = models.CharField(max_length=200)
    nav_summary = models.CharField(max_length=100, default='new crashcourse')
