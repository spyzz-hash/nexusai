import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from groq import Groq

from .models import Conversation, Message


def get_groq_client():
    return Groq(api_key=settings.GROQ_API_KEY)


SYSTEM_PROMPT = (
    "You are NexusAI, a helpful, friendly, and knowledgeable AI assistant. "
    "You provide clear, concise, and accurate responses. "
    "Use markdown formatting when it helps readability. "
    "Be conversational and engaging."
)


def index(request):
    """Main chat page - shows all conversations."""
    conversations = Conversation.objects.all()[:20]
    return render(request, 'chat/index.html', {
        'conversations': conversations,
    })


def conversation_view(request, conversation_id):
    """View a specific conversation."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = conversation.messages.all()
    conversations = Conversation.objects.all()[:20]
    return render(request, 'chat/index.html', {
        'conversations': conversations,
        'active_conversation': conversation,
        'messages': messages,
    })


@csrf_exempt
@require_POST
def new_conversation(request):
    """Create a new conversation."""
    conversation = Conversation.objects.create()
    return JsonResponse({
        'id': str(conversation.id),
        'title': conversation.title,
    })


@csrf_exempt
@require_POST
def send_message(request):
    """Send a message and get AI response via Groq."""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        # Get or create conversation
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = Conversation.objects.create()

        # Save user message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
        )

        # Build message history for Groq (OpenAI-compatible format)
        history = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        for msg in conversation.messages.all():
            history.append({'role': msg.role, 'content': msg.content})

        # Call Groq API
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=history,
            max_tokens=2048,
            temperature=0.7,
        )

        assistant_content = response.choices[0].message.content

        # Save assistant message
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=assistant_content,
        )

        # Update conversation title from first message
        if conversation.messages.count() <= 2:
            title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            conversation.title = title
            conversation.save()

        return JsonResponse({
            'conversation_id': str(conversation.id),
            'message': assistant_content,
            'title': conversation.title,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def delete_conversation(request, conversation_id):
    """Delete a conversation."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    conversation.delete()
    return JsonResponse({'status': 'deleted'})
