from django.db import models

class Thread(models.Model):
    title = models.CharField(max_length=30, default='Default Title')

class Message(models.Model):
    associated_thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    message = models.TextField()
