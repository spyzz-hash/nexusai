from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('conversation/<uuid:conversation_id>/', views.conversation_view, name='conversation'),
    path('api/new/', views.new_conversation, name='new_conversation'),
    path('api/send/', views.send_message, name='send_message'),
    path('api/delete/<uuid:conversation_id>/', views.delete_conversation, name='delete_conversation'),
]
