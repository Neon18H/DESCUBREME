import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from core.forms import RegisterForm, UserProfileForm
from core.models import Plan, PlanItem, PlanLike, PlanSave
from core.services.planner import PlanGenerationError, generate_plan_from_prompt


class AppLoginView(LoginView):
    template_name = 'core/login.html'

    def get_success_url(self):
        return '/my/plans/'


class AppLogoutView(LogoutView):
    next_page = 'landing'


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
    owner = get_object_or_404(User.objects.select_related('profile'), username=username)
    plans = Plan.objects.filter(owner=owner, is_public=True)
    return render(request, 'core/profile.html', {'owner': owner, 'plans': plans})


@login_required
def profile_settings(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado.')
            return redirect('profile_settings')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'core/profile_edit.html', {'form': form})


@login_required
def my_plans(request):
    created_plans = Plan.objects.filter(owner=request.user).prefetch_related('items')
    saved_plans = Plan.objects.filter(saves__user=request.user).exclude(owner=request.user).distinct()
    return render(request, 'core/my_plans.html', {'created_plans': created_plans, 'saved_plans': saved_plans})
