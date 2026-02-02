# ============================================
# chat/urls.py
# ============================================
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/conversations/create/', views.create_conversation, name='create_conversation'),
    path('api/conversations/<int:conv_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('api/conversations/<int:conv_id>/title/', views.update_conversation_title, name='update_conversation_title'),
    path('api/conversations/<int:conv_id>/messages/', views.get_messages, name='get_messages'),
    path('api/messages/send/', views.send_message, name='send_message'),
    path('api/conversations/<int:conv_id>/settings/', views.update_settings, name='update_settings'),
    path('api/conversations/<int:conv_id>/settings/get/', views.get_settings, name='get_settings'),
]