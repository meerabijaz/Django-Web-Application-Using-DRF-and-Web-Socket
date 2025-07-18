from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Room, Message
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@login_required(login_url='/accounts/login/')
def dashboard(request):
    user = request.user
    private_rooms = Room.objects.filter(participants=user, room_type='private')
    group_rooms = Room.objects.filter(participants=user, room_type='group')
    available_groups = Room.objects.filter(room_type='group').exclude(participants=user)

    def get_room_info(room):
        latest_message = Message.objects.filter(room=room).order_by('-timestamp').first()
        if latest_message:
            last_message = latest_message.message
            last_timestamp = latest_message.timestamp
        else:
            last_message = None
            last_timestamp = None
        unread_count = Message.objects.filter(room=room).exclude(is_read=user).count()
        # For private rooms, get the other participant's online status and superuser status
        online_status = None
        is_superuser = False
        if room.room_type == 'private':
            other_users = room.participants.exclude(id=user.id)
            if other_users.exists():
                from accounts.models import Profile
                profile = Profile.objects.filter(user=other_users.first()).first()
                online_status = profile.is_online if profile else False
                is_superuser = other_users.first().is_superuser
        return {
            'room': room,
            'last_message': last_message,
            'last_timestamp': last_timestamp,
            'unread_count': unread_count,
            'online_status': online_status,
            'is_superuser': is_superuser,
        }

    private_rooms_info = [get_room_info(room) for room in private_rooms]
    group_rooms_info = [get_room_info(room) for room in group_rooms]
    available_groups_info = [get_room_info(room) for room in available_groups]
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'dashboard.html', {
        'private_rooms_info': private_rooms_info,
        'group_rooms_info': group_rooms_info,
        'available_groups_info': available_groups_info,
        'user': user,
        'users': users,
    })

@csrf_exempt
@login_required(login_url='/accounts/login/')
def ajax_create_private_room(request):
    if request.method == 'POST':
        other_username = request.POST.get('other_username', '').strip().lower()
        if not other_username or other_username == request.user.username.lower():
            return JsonResponse({'error': 'You cannot chat with yourself.'}, status=400)
        try:
            other_user = User.objects.get(username__iexact=other_username)
        except User.DoesNotExist:
            return JsonResponse({'error': f"User '{other_username}' not found."}, status=404)
        private_rooms = Room.objects.filter(room_type='private', participants=request.user).filter(participants=other_user)
        for room in private_rooms:
            if room.participants.count() == 2:
                return JsonResponse({'room_name': room.room_name, 'status': 'exists'})
        room_name = f"private_{min(request.user.id, other_user.id)}_{max(request.user.id, other_user.id)}"
        room, created = Room.objects.get_or_create(room_name=room_name, room_type='private')
        room.participants.set([request.user, other_user])
        return JsonResponse({'room_name': room.room_name, 'status': 'created'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required(login_url='/accounts/login/')
def ajax_create_group_room(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name', '').strip()
        # Robustly parse user_ids (handle both list and comma-separated string)
        user_ids = request.POST.getlist('user_ids[]')
        if not user_ids:
            user_ids_str = request.POST.get('user_ids', '')
            if user_ids_str:
                user_ids = user_ids_str.split(',')
        if not group_name:
            return JsonResponse({'error': 'Group name required.'}, status=400)
        if Room.objects.filter(room_name=group_name, room_type='group').exists():
            return JsonResponse({'error': 'Group name already exists.'}, status=400)
        room = Room.objects.create(room_name=group_name, room_type='group')
        room.participants.add(request.user)
        users = User.objects.filter(id__in=user_ids)
        for u in users:
            room.participants.add(u)
        # Notify new group members in real time
        channel_layer = get_channel_layer()
        group_info = {
            'room_name': room.room_name,
            'room_type': room.room_type,
            'participants': [u.username for u in room.participants.all()],
        }
        for u in users:
            print(f"[DEBUG] Sending new_group_event to user_{u.username}")
            async_to_sync(channel_layer.group_send)(
                f'user_{u.username}',
                {
                    'type': 'new_group_event',
                    'group_info': group_info,
                }
            )
        # Also notify the creator
        print(f"[DEBUG] Sending new_group_event to user_{request.user.username}")
        async_to_sync(channel_layer.group_send)(
            f'user_{request.user.username}',
            {
                'type': 'new_group_event',
                'group_info': group_info,
            }
        )
        return JsonResponse({'room_name': room.room_name, 'status': 'created'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@require_GET
@login_required(login_url='/accounts/login/')
def api_get_messages(request, room_name):
    try:
        room = Room.objects.get(room_name=room_name)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    messages_qs = Message.objects.filter(room=room).order_by('timestamp').exclude(deleted_for=request.user)
    messages_list = []
    for msg in messages_qs:
        messages_list.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
            'is_self': msg.sender == request.user,
            'media_url': msg.media.url if msg.media else None,
            'status': msg.status,
        })
    return JsonResponse({'messages': messages_list, 'room_type': room.room_type, 'room_name': room.room_name})

@csrf_exempt
@login_required(login_url='/accounts/login/')
def ajax_delete_private_room(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name', '').strip()
        user = request.user
        try:
            room = Room.objects.get(room_name=room_name, room_type='private')
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Room not found.'}, status=404)
        if user not in room.participants.all():
            return JsonResponse({'error': 'You are not a participant of this chat.'}, status=403)
        # Delete the room (and cascade delete messages)
        room.delete()
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required(login_url='/accounts/login/')
def ajax_delete_group_room(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name', '').strip()
        user = request.user
        try:
            room = Room.objects.get(room_name=room_name, room_type='group')
        except Room.DoesNotExist:
            return JsonResponse({'error': 'Group not found.'}, status=404)
        if user not in room.participants.all():
            return JsonResponse({'error': 'You are not a participant of this group.'}, status=403)
        # Optionally: Only allow group creator to delete. For now, allow any participant.
        room.delete()
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'error': 'Invalid request'}, status=400)
