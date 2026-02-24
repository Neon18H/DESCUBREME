import json
import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import Count, F, Max, OuterRef, Q, Subquery
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from core.forms import CommentForm, MessageForm, ProfileEditForm, RegisterForm
from core.models import (
    Conversation,
    FriendRequest,
    Friendship,
    Message,
    Plan,
    PlanComment,
    PlanItem,
    PlanJoin,
    PlanLike,
    PlanSave,
    UserProfile,
)
from core.services.geolocation import GeolocationError, resolve_city_from_coordinates
from core.services.planner import PlanGenerationError, generate_plan_from_prompt

logger = logging.getLogger(__name__)


class AppLoginView(LoginView):
    template_name = 'core/login.html'

    def get_success_url(self):
        return '/my/plans/'


class AppLogoutView(LogoutView):
    next_page = 'landing'


def are_friends(user_a, user_b):
    if not user_a or not user_b or user_a == user_b:
        return False
    return FriendRequest.objects.filter(
        (
            Q(from_user=user_a, to_user=user_b)
            | Q(from_user=user_b, to_user=user_a)
        ),
        state=FriendRequest.State.ACCEPTED,
    ).exists() or Friendship.are_friends(user_a, user_b)


def friendship_state(viewer, owner):
    if not viewer.is_authenticated:
        return {'state': 'none'}
    if viewer == owner:
        return {'state': 'self'}

    accepted = FriendRequest.objects.filter(
        (Q(from_user=viewer, to_user=owner) | Q(from_user=owner, to_user=viewer)),
        state=FriendRequest.State.ACCEPTED,
    ).first()
    if accepted or Friendship.are_friends(viewer, owner):
        return {'state': 'friends', 'request': accepted}

    outgoing = FriendRequest.objects.filter(from_user=viewer, to_user=owner, state=FriendRequest.State.PENDING).first()
    if outgoing:
        return {'state': 'pending_out', 'request': outgoing}

    incoming = FriendRequest.objects.filter(from_user=owner, to_user=viewer, state=FriendRequest.State.PENDING).first()
    if incoming:
        return {'state': 'pending_in', 'request': incoming}

    blocked = FriendRequest.objects.filter(
        (Q(from_user=viewer, to_user=owner) | Q(from_user=owner, to_user=viewer)),
        state=FriendRequest.State.BLOCKED,
    ).first()
    if blocked:
        return {'state': 'blocked', 'request': blocked}

    return {'state': 'none'}


def _get_conversation(user_a, user_b):
    convo, _ = Conversation.objects.get_or_create(user1=user_a, user2=user_b)
    return convo


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/my/plans/')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


@ensure_csrf_cookie
def landing(request):
    return render(request, 'core/home.html')


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _user_preferences(user):
    if not user.is_authenticated:
        return {}
    profile = getattr(user, 'profile', None)
    if not profile:
        return {}
    return {
        'likes': profile.likes_tags,
        'avoid': profile.avoid_tags,
        'hobbies': profile.hobbies_tags,
        'budget_min_cop': profile.budget_min_cop,
        'budget_max_cop': profile.budget_max_cop,
        'preferred_vibes': profile.preferred_vibes,
    }

@require_POST
def api_generate_plan(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Payload inválido.'}, status=400)

    user_prompt = (payload.get('prompt') or '').strip()
    if len(user_prompt) < 8:
        return JsonResponse({'error': 'Describe mejor tu plan (mínimo 8 caracteres).'}, status=400)

    lat = _parse_float(payload.get('lat'))
    lng = _parse_float(payload.get('lng'))
    city_name = (payload.get('city_name') or '').strip()
    country_code = (payload.get('country_code') or 'CO').strip().upper()[:2] or 'CO'

    if lat is not None and lng is not None:
        try:
            resolved = resolve_city_from_coordinates(lat, lng)
        except GeolocationError:
            resolved = None
        if resolved:
            city_name = resolved.city_name
            country_code = resolved.country_code

    if not city_name and request.user.is_authenticated and getattr(request.user, 'profile', None):
        city_name = request.user.profile.city or request.user.profile.city_default

    city_name = city_name or 'Medellín'

    try:
        result = generate_plan_from_prompt(
            user_prompt,
            city_name=city_name,
            lat=lat,
            lng=lng,
            user_preferences=_user_preferences(request.user),
        )
    except PlanGenerationError as exc:
        return JsonResponse({'error': str(exc)}, status=502)

    result['resolved_location'] = {'city_name': city_name, 'country_code': country_code}
    return JsonResponse(result)


@login_required
@require_POST
def api_save_plan(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Payload inválido.'}, status=400)

    parsed = payload.get('parsed_request') or {}
    windows = payload.get('time_windows') or []
    city = parsed.get('city') or payload.get('city_name') or 'Ciudad'
    country_code = (payload.get('country_code') or parsed.get('country') or 'CO').upper()[:2]

    plan = Plan.objects.create(
        owner=request.user,
        title=payload.get('title') or f"Plan en {city}",
        city=city,
        city_name=city,
        city_slug=slugify(city),
        country_code=country_code,
        is_shared=bool(payload.get('is_shared')),
        mood=parsed.get('mood', ''),
        group=parsed.get('group', ''),
        budget_cop=parsed.get('budget_cop'),
        prompt_text=payload.get('prompt', ''),
        plan_json=payload,
    )

    items_to_create = []
    for window in windows:
        for idx, place in enumerate(window.get('places') or [], start=1):
            items_to_create.append(
                PlanItem(
                    plan=plan,
                    time_label=window.get('label', ''),
                    order=idx,
                    place_id=place.get('place_id', ''),
                    name=place.get('name', 'Lugar recomendado'),
                    rating=place.get('rating'),
                    user_ratings_total=place.get('user_ratings_total'),
                    price_level=place.get('price_level'),
                    address=place.get('address', ''),
                    photo_reference=place.get('photo_reference', ''),
                    photo_url=place.get('photo_url', ''),
                    maps_url=place.get('maps_url', ''),
                )
            )
    PlanItem.objects.bulk_create(items_to_create)
    return JsonResponse({'ok': True, 'plan_id': str(plan.id), 'detail_url': f'/p/{plan.id}/'})


@login_required
@require_GET
def city_feed(request, city_slug):
    plans = Plan.objects.filter(is_shared=True, city_slug=city_slug).select_related('owner', 'owner__profile').prefetch_related('items').annotate(
        joins_count=Count('joins', distinct=True),
        comments_count=Count('comments', distinct=True),
    )
    plans = plans.order_by('-shared_at', '-created_at')
    from django.core.paginator import Paginator

    paginator = Paginator(plans, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    city_name = plans.first().city_name if plans.exists() else city_slug.replace('-', ' ').title()
    return render(request, 'core/city_feed.html', {'page_obj': page_obj, 'city_name': city_name, 'city_slug': city_slug})


@login_required
@require_GET
def public_plan_detail(request, plan_id):
    plan = get_object_or_404(Plan.objects.select_related('owner', 'owner__profile').prefetch_related('items', 'comments__user__profile'), id=plan_id)
    if not plan.is_shared and plan.owner != request.user:
        return HttpResponseForbidden('No tienes acceso a este plan.')
    grouped_items = {}
    for item in plan.items.all():
        grouped_items.setdefault(item.time_label, []).append(item)
    context = {
        'plan': plan,
        'grouped_items': grouped_items,
        'joined': request.user.is_authenticated and PlanJoin.objects.filter(user=request.user, plan=plan).exists(),
        'joins_count': plan.joins.count(),
        'comments': plan.comments.select_related('user', 'user__profile').all(),
        'comment_form': CommentForm(),
        'can_socialize': plan.is_shared,
    }
    return render(request, 'core/plan_detail.html', context)


@login_required
@require_POST
def save_public_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_shared=True)
    _, created = PlanSave.objects.get_or_create(user=request.user, plan=plan)
    if created:
        Plan.objects.filter(pk=plan.pk).update(saves_count=F('saves_count') + 1)
    return redirect('my_plans')


@login_required
@require_POST
def toggle_plan_public(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, owner=request.user)
    make_shared = (request.POST.get('is_shared') or '').lower() in {'true', '1', 'yes', 'on'}
    plan.is_shared = make_shared if 'is_shared' in request.POST else not plan.is_shared
    plan.is_public = plan.is_shared
    plan.shared_at = timezone.now() if plan.is_shared else None
    plan.save(update_fields=['is_shared', 'is_public', 'shared_at', 'updated_at'])
    return JsonResponse({'ok': True, 'is_shared': plan.is_shared, 'is_public': plan.is_shared, 'share_url': f'/p/{plan.id}/'})


@login_required
@require_POST
def toggle_plan_like(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_shared=True)
    with transaction.atomic():
        like, created = PlanLike.objects.get_or_create(user=request.user, plan=plan)
        if created:
            Plan.objects.filter(pk=plan.pk).update(likes_count=F('likes_count') + 1)
            liked = True
        else:
            like.delete()
            Plan.objects.filter(pk=plan.pk).update(likes_count=F('likes_count') - 1)
            liked = False
    plan.refresh_from_db(fields=['likes_count'])
    return JsonResponse({'ok': True, 'liked': liked, 'likes_count': plan.likes_count})


@login_required
@require_POST
def plan_join(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_shared=True)
    PlanJoin.objects.get_or_create(plan=plan, user=request.user)
    return redirect('public_plan_detail', plan_id=plan.id)


@login_required
@require_POST
def plan_unjoin(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_shared=True)
    PlanJoin.objects.filter(plan=plan, user=request.user).delete()
    return redirect('public_plan_detail', plan_id=plan.id)


@login_required
@require_POST
def plan_comment(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_shared=True)
    if not plan.is_shared and plan.owner != request.user:
        return HttpResponseForbidden('No tienes acceso a este plan.')
    form = CommentForm(request.POST)
    if form.is_valid():
        PlanComment.objects.create(plan=plan, user=request.user, body=form.cleaned_data['body'])
    else:
        messages.error(request, 'Comentario inválido.')
    return redirect('public_plan_detail', plan_id=plan.id)


@login_required
@require_GET
def public_profile(request, username):
    owner = get_object_or_404(User, username=username)
    owner_profile, _ = UserProfile.objects.get_or_create(user=owner, defaults={'display_name': owner.username})
    relation = friendship_state(request.user, owner)

    can_view_full = request.user == owner or (not owner_profile.is_private) or relation['state'] == 'friends'
    template_name = 'core/profile_full.html' if can_view_full else 'core/profile_public.html'
    plans = Plan.objects.filter(owner=owner, is_shared=True) if can_view_full else Plan.objects.none()
    context = {'owner': owner, 'owner_profile': owner_profile, 'plans': plans, 'friendship': relation, 'can_view_full': can_view_full}
    return render(request, template_name, context)


@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'display_name': request.user.username})

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado ✅')
            return redirect('profile_edit')
        messages.error(request, 'No se pudo guardar. Revisa los campos.')
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'core/profile_edit.html', {'form': form, 'profile': profile})


@login_required
@require_GET
def people_list(request):
    q = (request.GET.get('q') or '').strip()
    people = User.objects.exclude(id=request.user.id).select_related('profile')
    if q:
        people = people.filter(Q(username__icontains=q) | Q(profile__display_name__icontains=q) | Q(profile__city__icontains=q))
    people = people[:40]
    cards = []
    for person in people:
        profile, _ = UserProfile.objects.get_or_create(user=person, defaults={'display_name': person.username})
        cards.append({'user': person, 'profile': profile, 'friendship': friendship_state(request.user, person)})
    return render(request, 'core/people_list.html', {'q': q, 'cards': cards})


@login_required
@require_GET
def friends_list(request):
    accepted = FriendRequest.objects.filter(
        (Q(from_user=request.user) | Q(to_user=request.user)),
        state=FriendRequest.State.ACCEPTED,
    ).select_related('from_user__profile', 'to_user__profile')
    friends = [req.to_user if req.from_user == request.user else req.from_user for req in accepted]

    incoming = FriendRequest.objects.filter(to_user=request.user, state=FriendRequest.State.PENDING).select_related('from_user__profile')
    outgoing = FriendRequest.objects.filter(from_user=request.user, state=FriendRequest.State.PENDING).select_related('to_user__profile')
    return render(request, 'core/friends.html', {'friends': friends, 'incoming': incoming, 'outgoing': outgoing})


@login_required
@require_POST
def send_friend_request(request, username):
    target = get_object_or_404(User, username=username)
    target_profile, _ = UserProfile.objects.get_or_create(user=target, defaults={'display_name': target.username})
    if target == request.user:
        messages.error(request, 'No puedes agregarte a ti.')
        return redirect('people_list')
    if not target_profile.allow_friend_requests:
        messages.error(request, 'Este usuario no recibe solicitudes de amistad.')
        return redirect(request.META.get('HTTP_REFERER', 'people_list'))

    relation = friendship_state(request.user, target)
    if relation['state'] == 'friends':
        messages.info(request, 'Ya son amigos.')
    elif relation['state'] == 'pending_in':
        messages.info(request, 'Esta persona ya te envió solicitud, acepta desde Amigos.')
    elif relation['state'] == 'pending_out':
        messages.info(request, 'La solicitud ya fue enviada.')
    else:
        FriendRequest.objects.update_or_create(
            from_user=request.user,
            to_user=target,
            defaults={'state': FriendRequest.State.PENDING},
        )
        messages.success(request, 'Solicitud enviada.')
    return redirect(request.META.get('HTTP_REFERER', 'people_list'))


@login_required
@require_POST
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user, state=FriendRequest.State.PENDING)
    with transaction.atomic():
        friend_request.state = FriendRequest.State.ACCEPTED
        friend_request.save(update_fields=['state', 'updated_at'])
        Friendship.objects.get_or_create(user1=friend_request.from_user, user2=friend_request.to_user)
        FriendRequest.objects.filter(
            from_user=friend_request.to_user,
            to_user=friend_request.from_user,
            state=FriendRequest.State.PENDING,
        ).update(state=FriendRequest.State.REJECTED, updated_at=timezone.now())
    messages.success(request, 'Ahora son amigos.')
    return redirect('friends_list')


@login_required
@require_POST
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user, state=FriendRequest.State.PENDING)
    friend_request.state = FriendRequest.State.REJECTED
    friend_request.save(update_fields=['state', 'updated_at'])
    messages.info(request, 'Solicitud rechazada.')
    return redirect('friends_list')


@login_required
@require_GET
def chat_list(request):
    last_body_sq = Message.objects.filter(conversation=OuterRef('pk')).order_by('-created_at').values('body')[:1]
    last_time_sq = Message.objects.filter(conversation=OuterRef('pk')).order_by('-created_at').values('created_at')[:1]
    conversations = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        last_message=Subquery(last_body_sq),
        last_message_at=Subquery(last_time_sq),
    ).order_by('-last_message_at', '-updated_at')

    rows = []
    for convo in conversations:
        other = convo.user2 if convo.user1 == request.user else convo.user1
        unread = convo.messages.filter(is_read=False).exclude(sender=request.user).count()
        rows.append({'conversation': convo, 'other': other, 'unread': unread})
    return render(request, 'core/chat_list.html', {'rows': rows})


@login_required
@require_GET
def chat_thread(request, username):
    other = get_object_or_404(User, username=username)
    if not are_friends(request.user, other):
        return HttpResponseForbidden('Solo puedes chatear con amistades aceptadas.')
    conversation = _get_conversation(request.user, other)
    Message.objects.filter(conversation=conversation, is_read=False).exclude(sender=request.user).update(is_read=True)
    messages_qs = conversation.messages.select_related('sender').order_by('created_at')[:200]
    return render(request, 'core/chat_thread.html', {
        'other': other,
        'conversation': conversation,
        'messages_list': messages_qs,
        'form': MessageForm(),
    })


@login_required
@require_POST
def chat_send(request, username):
    other = get_object_or_404(User, username=username)
    if not are_friends(request.user, other):
        return HttpResponseForbidden('Solo puedes chatear con amistades aceptadas.')
    conversation = _get_conversation(request.user, other)
    form = MessageForm(request.POST)
    if form.is_valid():
        Message.objects.create(conversation=conversation, sender=request.user, body=form.cleaned_data['body'])
        Conversation.objects.filter(id=conversation.id).update(updated_at=timezone.now())
    else:
        messages.error(request, 'Mensaje inválido.')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': form.is_valid()})
    return redirect('chat_thread', username=other.username)


@login_required
@require_GET
def chat_poll(request, username):
    other = get_object_or_404(User, username=username)
    if not are_friends(request.user, other):
        return JsonResponse({'error': 'forbidden'}, status=403)
    conversation = _get_conversation(request.user, other)

    after_id = request.GET.get('after')
    after_iso = request.GET.get('after_iso')
    new_messages = conversation.messages.select_related('sender').order_by('created_at')
    if after_id and after_id.isdigit():
        new_messages = new_messages.filter(id__gt=int(after_id))
    elif after_iso:
        parsed = parse_datetime(after_iso)
        if parsed:
            new_messages = new_messages.filter(created_at__gt=parsed)

    new_messages = new_messages[:50]
    payload = [
        {
            'id': msg.id,
            'sender': msg.sender.username,
            'is_me': msg.sender_id == request.user.id,
            'body': msg.body,
            'created_at': msg.created_at.isoformat(),
        }
        for msg in new_messages
    ]
    Message.objects.filter(id__in=[m['id'] for m in payload], is_read=False).exclude(sender=request.user).update(is_read=True)
    return JsonResponse({'messages': payload})


@login_required
def my_plans(request):
    created_plans = Plan.objects.filter(owner=request.user).prefetch_related('items')
    saved_plans = Plan.objects.filter(saves__user=request.user).exclude(owner=request.user).distinct()
    return render(request, 'core/my_plans.html', {'created_plans': created_plans, 'saved_plans': saved_plans})
