from collections import OrderedDict

from core.services.google_places import GooglePlacesAPIError, search_places
from core.services.openrouter_ai import OpenRouterError, parse_user_prompt


class PlanGenerationError(Exception):
    pass


def validate_parsed_json(data: dict) -> dict:
    required = ['city', 'country', 'budget_cop', 'mood', 'group', 'time_windows', 'constraints']
    if not isinstance(data, dict):
        raise PlanGenerationError('Respuesta inválida del parser.')
    for key in required:
        if key not in data:
            raise PlanGenerationError(f'Falta campo obligatorio: {key}')
    if not isinstance(data['time_windows'], list) or not data['time_windows']:
        raise PlanGenerationError('time_windows debe contener al menos una franja horaria.')
    return data


def _window_queries(window: dict, city: str) -> list[str]:
    vibes = window.get('vibes', [])
    place_types = window.get('place_types', [])
    combos = []
    for place_type in place_types[:3]:
        vibe = vibes[0] if vibes else 'plan recomendado'
        combos.append(f'{place_type} {vibe} {city}'.strip())
    if not combos:
        combos.append(f"{window.get('label', 'plan')} {city}".strip())
    return list(OrderedDict.fromkeys(combos))


def generate_plan_from_prompt(prompt: str, places_per_window: int = 3) -> dict:
    try:
        parsed = validate_parsed_json(parse_user_prompt(prompt))
    except OpenRouterError as exc:
        raise PlanGenerationError(str(exc)) from exc

    enriched_windows = []
    for window in parsed['time_windows']:
        city = parsed.get('city', '')
        all_places = []
        seen_ids = set()
        for query in _window_queries(window, city):
            try:
                results = search_places(query=query, city=city, limit=places_per_window)
            except GooglePlacesAPIError as exc:
                raise PlanGenerationError(str(exc)) from exc
            for place in results:
                place_id = place.get('place_id')
                if not place_id or place_id in seen_ids:
                    continue
                seen_ids.add(place_id)
                all_places.append(place)
        enriched_windows.append({**window, 'places': all_places[:places_per_window + 1]})

    return {'prompt': prompt, 'parsed_request': parsed, 'time_windows': enriched_windows}
