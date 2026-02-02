# ============================================
# chat/views.py
# ============================================
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
from g4f.client import Client
from g4f.cookies import set_cookies_dir
from .models import Conversation, Message, Settings

# Setup cookies directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIES_DIR = os.path.join(BASE_DIR, 'har_and_cookies')

# Create cookies directory if it doesn't exist
if not os.path.exists(COOKIES_DIR):
    os.makedirs(COOKIES_DIR)
    # Create a README file
    with open(os.path.join(COOKIES_DIR, 'README.txt'), 'w') as f:
        f.write('Place your .har and .json cookie files here for providers that require authentication.\n')
        f.write('This directory is optional - most providers work without cookies.\n')

# Set the cookies directory for g4f
try:
    set_cookies_dir(COOKIES_DIR)
except:
    pass  # Ignore if setting cookies dir fails

def index(request):
    conversations = Conversation.objects.all().order_by('-updated_at')
    conversations_data = [{
        'id': conv.id,
        'title': conv.title,
        'created_at': conv.created_at.isoformat()
    } for conv in conversations]
    
    import json
    return render(request, 'chat/index.html', {
        'conversations': json.dumps(conversations_data)
    })

@csrf_exempt
@require_http_methods(["POST"])
def create_conversation(request):
    conv = Conversation.objects.create(title='New Chat')
    Settings.objects.create(conversation=conv)
    return JsonResponse({
        'id': conv.id,
        'title': conv.title,
        'created_at': conv.created_at.isoformat()
    })

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_conversation(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id)
    conv.delete()
    return JsonResponse({'success': True})

@csrf_exempt
@require_http_methods(["POST"])
def update_conversation_title(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id)
    data = json.loads(request.body)
    conv.title = data.get('title', conv.title)
    conv.save()
    return JsonResponse({'success': True, 'title': conv.title})

@require_http_methods(["GET"])
def get_messages(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id)
    messages = conv.messages.all()
    return JsonResponse({
        'messages': [{
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'is_image': msg.is_image,
            'model_used': msg.model_used,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]
    })

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    data = json.loads(request.body)
    conv_id = data.get('conversation_id')
    user_message = data.get('message')
    response_type = data.get('response_type', 'text')
    
    conv = get_object_or_404(Conversation, id=conv_id)
    settings = Settings.objects.get_or_create(conversation=conv)[0]
    
    # Save user message
    Message.objects.create(
        conversation=conv,
        role='user',
        content=user_message
    )
    
    # Generate AI response
    client = Client()
    
    try:
        if response_type == 'image':
            try:
                response = client.images.generate(
                    model=settings.image_model,
                    prompt=user_message,
                    response_format="url"
                )
                ai_response = response.data[0].url
                is_image = True
            except Exception as img_error:
                # If image generation fails, return error message
                raise Exception(f"Image generation failed: {str(img_error)}")
        else:
            # Get conversation history (excluding the message we just added)
            history = conv.messages.filter(is_image=False).order_by('created_at')
            history_count = history.count()
            
            messages = []
            
            # Add system prompt if exists
            if settings.system_prompt:
                messages.append({"role": "system", "content": settings.system_prompt})
            
            # Add conversation history (all messages except the last one we just added)
            if history_count > 1:
                for msg in list(history)[:history_count-1]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add the current user message
            messages.append({"role": "user", "content": user_message})
            
            try:
                response = client.chat.completions.create(
                    model=settings.model,
                    messages=messages,
                    web_search=False
                )
                ai_response = response.choices[0].message.content
                is_image = False
            except Exception as chat_error:
                # If chat fails, try a simpler approach
                raise Exception(f"Chat generation failed: {str(chat_error)}")
        
        # Save AI response
        ai_msg = Message.objects.create(
            conversation=conv,
            role='assistant',
            content=ai_response,
            is_image=is_image,
            model_used=settings.image_model if is_image else settings.model
        )
        
        # Update conversation title if it's the first message
        if conv.messages.count() == 2:
            conv.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            conv.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': ai_msg.id,
                'role': 'assistant',
                'content': ai_response,
                'is_image': is_image,
                'model_used': ai_msg.model_used,
                'created_at': ai_msg.created_at.isoformat()
            },
            'conversation_title': conv.title
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_settings(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id)
    settings = Settings.objects.get_or_create(conversation=conv)[0]
    
    data = json.loads(request.body)
    settings.model = data.get('model', settings.model)
    settings.system_prompt = data.get('system_prompt', settings.system_prompt)
    settings.image_model = data.get('image_model', settings.image_model)
    settings.save()
    
    return JsonResponse({'success': True})

@require_http_methods(["GET"])
def get_settings(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id)
    settings = Settings.objects.get_or_create(conversation=conv)[0]
    
    return JsonResponse({
        'model': settings.model,
        'system_prompt': settings.system_prompt,
        'image_model': settings.image_model
    })