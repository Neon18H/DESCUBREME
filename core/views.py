import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.forms import RegisterForm
from core.models import FavoritePlace, FavoritePlan
from core.services.planner import PlanGenerationError, generate_plan_from_prompt


class AppLoginView(LoginView):
    template_name = 'core/login.html'

    def get_success_url(self):
        return '/mis-planes/'


class AppLogoutView(LogoutView):
    next_page = 'landing'


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/mis-planes/')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


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
def api_save_place(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Payload inválido.'}, status=400)

    parsed = payload.get('parsed_request') or {}
    place = payload.get('place') or {}
    window = payload.get('window') or {}

    if not place.get('place_id'):
        return JsonResponse({'error': 'Lugar inválido.'}, status=400)

    favorite_plan = FavoritePlan.objects.create(
        user=request.user,
        prompt=payload.get('prompt', ''),
        city=parsed.get('city', ''),
        country=parsed.get('country', ''),
        mood=parsed.get('mood', ''),
        group=parsed.get('group', ''),
        budget_cop=parsed.get('budget_cop') or 0,
        source_payload=payload,
    )

    FavoritePlace.objects.create(
        favorite_plan=favorite_plan,
        window_label=window.get('label', ''),
        window_start=window.get('start', ''),
        window_end=window.get('end', ''),
        name=place.get('name', 'Lugar recomendado'),
        place_id=place.get('place_id', ''),
        rating=place.get('rating'),
        user_ratings_total=place.get('user_ratings_total'),
        price_level=place.get('price_level'),
        estimated_cost_cop=place.get('estimated_cost_cop'),
        address=place.get('address', ''),
        photo_url=place.get('photo_url', ''),
        maps_url=place.get('maps_url', ''),
        raw_payload=place.get('raw_payload') or {},
    )

    return JsonResponse({'ok': True, 'message': 'Lugar guardado en tus planes.'})


@login_required
def my_plans(request):
    plans = FavoritePlan.objects.filter(user=request.user).prefetch_related('places')
    return render(request, 'core/plans.html', {'plans': plans})


@login_required
def delete_favorite_plan(request, plan_id):
    plan = get_object_or_404(FavoritePlan, id=plan_id, user=request.user)
    plan.delete()
    messages.info(request, 'Plan eliminado.')
    return redirect('my_plans')
