import json
import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from core.forms import ProfileEditForm, RegisterForm
from core.models import FriendRequest, Friendship, Plan, PlanItem, PlanLike, PlanSave, UserProfile
from core.services.planner import PlanGenerationError, generate_plan_from_prompt

logger = logging.getLogger(__name__)


class AppLoginView(LoginView):
    template_name = 'core/login.html'

    def get_success_url(self):
        return '/my/plans/'


class AppLogoutView(LogoutView):
    next_page = 'landing'


def _friendship_status(viewer, owner):
    if not viewer.is_authenticated or viewer == owner:
        return {'state': 'self' if viewer == owner else 'anon'}

    if Friendship.are_friends(viewer, owner):
        return {'state': 'friends'}

    sent_request = FriendRequest.objects.filter(
        from_user=viewer,
        to_user=owner,
        status=FriendRequest.Status.PENDING,
    ).first()
    if sent_request:
        return {'state': 'sent', 'request': sent_request}

    received_request = FriendRequest.objects.filter(
        from_user=owner,
        to_user=viewer,
        status=FriendRequest.Status.PENDING,
    ).first()
    if received_request:
        return {'state': 'received', 'request': received_request}

    return {'state': 'none'}


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


@require_POST
def api_generate_plan(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Payload inválido.'}, status=400)

    user_prompt = (payload.get('prompt') or '').strip()
    if len(user_prompt) < 8:
        return JsonResponse({'error': 'Describe mejor tu plan (mínimo 8 caracteres).'}, status=400)

    try:
        result = generate_plan_from_prompt(user_prompt)
    except PlanGenerationError as exc:
        return JsonResponse({'error': str(exc)}, status=502)

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
    city = parsed.get('city') or 'Ciudad'

    plan = Plan.objects.create(
        owner=request.user,
        title=payload.get('title') or f"Plan en {city}",
        city=city,
        city_slug=slugify(city),
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
    return JsonResponse({'ok': True, 'plan_id': str(plan.id), 'detail_url': f'/p/{plan.share_code}/'})


@require_GET
def city_feed(request, city_slug):
    plans = Plan.objects.filter(is_public=True, city_slug=city_slug).select_related('owner', 'owner__profile')
    from django.core.paginator import Paginator

    paginator = Paginator(plans, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    city_name = plans.first().city if plans.exists() else city_slug.replace('-', ' ').title()
    return render(request, 'core/city_feed.html', {'page_obj': page_obj, 'city_name': city_name, 'city_slug': city_slug})


@require_GET
def public_plan_detail(request, share_code):
    plan = get_object_or_404(Plan.objects.select_related('owner', 'owner__profile').prefetch_related('items'), share_code=share_code, is_public=True)
    grouped_items = {}
    for item in plan.items.all():
        grouped_items.setdefault(item.time_label, []).append(item)
    liked = request.user.is_authenticated and PlanLike.objects.filter(user=request.user, plan=plan).exists()
    saved = request.user.is_authenticated and PlanSave.objects.filter(user=request.user, plan=plan).exists()
    return render(request, 'core/plan_detail.html', {'plan': plan, 'grouped_items': grouped_items, 'liked': liked, 'saved': saved})


@login_required
@require_POST
def save_public_plan(request, share_code):
    plan = get_object_or_404(Plan, share_code=share_code, is_public=True)
    _, created = PlanSave.objects.get_or_create(user=request.user, plan=plan)
    if created:
        Plan.objects.filter(pk=plan.pk).update(saves_count=F('saves_count') + 1)
    return redirect('my_plans')


@login_required
@require_POST
def toggle_plan_public(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, owner=request.user)
    plan.is_public = not plan.is_public
    plan.save(update_fields=['is_public', 'updated_at'])
    return JsonResponse({'ok': True, 'is_public': plan.is_public, 'share_url': f'/p/{plan.share_code}/'})


@login_required
@require_POST
def toggle_plan_like(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_public=True)
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


@require_GET
def public_profile(request, username):
    owner = get_object_or_404(User, username=username)
    owner_profile, _ = UserProfile.objects.get_or_create(
        user=owner,
        defaults={'display_name': owner.get_full_name() or owner.username},
    )
    relation = _friendship_status(request.user, owner)
    can_view_plans = True
    if owner_profile.is_private and relation.get('state') not in {'self', 'friends'}:
        can_view_plans = False
    plans = Plan.objects.filter(owner=owner, is_public=True) if can_view_plans else Plan.objects.none()
    context = {
        'owner': owner,
        'owner_profile': owner_profile,
        'plans': plans,
        'friendship': relation,
        'can_view_plans': can_view_plans,
    }
    return render(request, 'core/profile_detail.html', context)


@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'display_name': request.user.username},
    )

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            profile.refresh_from_db()
            logger.info('Profile saved and reloaded for user_id=%s', request.user.id)
            messages.success(request, 'Perfil actualizado ✅')
            return redirect('profile_edit')

        messages.error(request, 'No se pudo guardar. Revisa los campos.')
        logger.warning('ProfileEditForm errors: %s', form.errors.as_json())
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'core/profile_edit.html', {'form': form, 'profile': profile})


@login_required
@require_GET
def friends_search(request):
    q = (request.GET.get('q') or '').strip()
    results = User.objects.none()
    if q:
        results = User.objects.select_related('profile').filter(
            Q(username__icontains=q) | Q(profile__display_name__icontains=q)
        ).exclude(id=request.user.id)[:30]
    return render(request, 'core/friends_search.html', {'results': results, 'q': q})


@login_required
@require_GET
def requests_list(request):
    received = FriendRequest.objects.select_related('from_user__profile').filter(to_user=request.user, status=FriendRequest.Status.PENDING)
    sent = FriendRequest.objects.select_related('to_user__profile').filter(from_user=request.user, status=FriendRequest.Status.PENDING)
    return render(request, 'core/requests.html', {'received': received, 'sent': sent})


@login_required
@require_POST
def send_friend_request(request, user_id):
    target = get_object_or_404(User.objects.select_related('profile'), id=user_id)
    if target == request.user:
        messages.error(request, 'No puedes agregarte a ti.')
        return redirect(request.META.get('HTTP_REFERER', 'friends_search'))
    if Friendship.are_friends(request.user, target):
        messages.info(request, 'Ya son amigos.')
        return redirect(request.META.get('HTTP_REFERER', 'friends_search'))
    if not target.profile.allow_friend_requests:
        messages.error(request, 'Este usuario no recibe solicitudes de amistad.')
        return redirect(request.META.get('HTTP_REFERER', 'friends_search'))

    FriendRequest.objects.get_or_create(
        from_user=request.user,
        to_user=target,
        status=FriendRequest.Status.PENDING,
    )
    messages.success(request, 'Solicitud enviada.')
    return redirect(request.META.get('HTTP_REFERER', 'friends_search'))


@login_required
@require_POST
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user, status=FriendRequest.Status.PENDING)
    with transaction.atomic():
        Friendship.objects.get_or_create(user1=friend_request.from_user, user2=friend_request.to_user)
        friend_request.status = FriendRequest.Status.ACCEPTED
        friend_request.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Ahora son amigos.')
    return redirect('requests_list')


@login_required
@require_POST
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user, status=FriendRequest.Status.PENDING)
    friend_request.status = FriendRequest.Status.REJECTED
    friend_request.save(update_fields=['status', 'updated_at'])
    messages.info(request, 'Solicitud rechazada.')
    return redirect('requests_list')


@login_required
@require_POST
def remove_friend(request, user_id):
    other = get_object_or_404(User, id=user_id)
    user1, user2 = sorted([request.user.id, other.id])
    deleted, _ = Friendship.objects.filter(user1_id=user1, user2_id=user2).delete()
    if not deleted:
        return HttpResponseForbidden('No son amigos.')
    messages.info(request, 'Amistad eliminada.')
    return redirect(request.META.get('HTTP_REFERER', 'friends_list'))


@login_required
@require_GET
def friends_list(request):
    friendships = Friendship.objects.select_related('user1__profile', 'user2__profile').filter(
        Q(user1=request.user) | Q(user2=request.user)
    )
    friends = [f.user2 if f.user1 == request.user else f.user1 for f in friendships]
    return render(request, 'core/friends_list.html', {'friends': friends})


@login_required
def my_plans(request):
    created_plans = Plan.objects.filter(owner=request.user).prefetch_related('items')
    saved_plans = Plan.objects.filter(saves__user=request.user).exclude(owner=request.user).distinct()
    return render(request, 'core/my_plans.html', {'created_plans': created_plans, 'saved_plans': saved_plans})
