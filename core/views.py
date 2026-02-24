from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.forms import PlanGeneratorForm
from core.models import Plan, PlanStep
from core.services.planner import create_plan


def landing(request):
    return render(request, 'core/landing.html')


def generate_plan_view(request):
    if request.method == 'POST':
        form = PlanGeneratorForm(request.POST)
        if form.is_valid():
            try:
                raw_places, ai_plan = create_plan(form.cleaned_data)
                plan = Plan.objects.create(
                    city=form.cleaned_data['city'],
                    mood=form.cleaned_data['mood'],
                    start_time=form.cleaned_data['start_time'],
                    end_time=form.cleaned_data['end_time'],
                    budget_cop=form.cleaned_data['budget'],
                    group_size=form.cleaned_data['group_size'],
                    transport=form.cleaned_data['transport'],
                    interests=form.cleaned_data['interests'],
                    raw_places=raw_places,
                    ai_plan_json=ai_plan,
                    title=ai_plan.get('title', 'Plan personalizado'),
                    is_saved=False,
                )
                order_count = 1
                for block in ['tarde', 'noche']:
                    for step in ai_plan['blocks'][block]['steps']:
                        place = step.get('place', {})
                        PlanStep.objects.create(
                            plan=plan,
                            block=block,
                            order=order_count,
                            place_name=place.get('name') or step.get('title', 'Sitio recomendado'),
                            address=place.get('address', ''),
                            rating=place.get('rating'),
                            maps_url=place.get('maps_url', ''),
                            est_time_minutes=step.get('estimated_time_minutes'),
                            est_cost_cop=step.get('estimated_cost_cop'),
                            why=step.get('why', ''),
                            description=step.get('description', ''),
                        )
                        order_count += 1
                return redirect('plan_results', plan_id=plan.id)
            except Exception:
                return render(request, 'core/error.html', {'message': 'No pudimos generar tu plan ahora. Intenta nuevamente.'})
    else:
        form = PlanGeneratorForm()
    return render(request, 'core/generate.html', {'form': form})


def plan_results(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    return render(request, 'core/results.html', {'plan': plan})


@require_POST
def save_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    plan.is_saved = True
    plan.save(update_fields=['is_saved'])
    messages.success(request, 'Plan guardado con éxito.')
    return redirect('plan_results', plan_id=plan.id)


def saved_plans(request):
    plans = Plan.objects.filter(is_saved=True)
    return render(request, 'core/saved_plans.html', {'plans': plans})


def plan_detail(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    return render(request, 'core/plan_detail.html', {'plan': plan})


@require_POST
def delete_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    plan.delete()
    messages.info(request, 'Plan eliminado.')
    return redirect('saved_plans')
