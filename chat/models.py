# ============================================
# chat/models.py
# ============================================
from django.db import models
from django.contrib.auth.models import User
import json

class Conversation(models.Model):
    title = models.CharField(max_length=255, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=[('user', 'User'), ('assistant', 'Assistant')])
    content = models.TextField()
    is_image = models.BooleanField(default=False)
    model_used = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']

class Settings(models.Model):
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE)
    model = models.CharField(max_length=100, default='gpt-4')
    system_prompt = models.TextField(blank=True)
    image_model = models.CharField(max_length=100, default='flux')