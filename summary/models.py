from django.db import models

class Summary(models.Model):
    content = models.TextField()
    generator_uuid = models.CharField(max_length=200)
    nav_summary = models.CharField(max_length=100)
