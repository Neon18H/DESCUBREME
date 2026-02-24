from collections import OrderedDict

from core.services.google_places import GooglePlacesAPIError, place_details, text_search
from core.services.openrouter_ai import generate_plan

MOOD_QUERIES = {
    'alegre': ['discoteca', 'rooftop', 'bar', 'parque de diversiones'],
    'chill': ['café', 'cervecería artesanal', 'mirador', 'parque'],
    'cine': ['cine'],
    'comida': ['restaurante', 'hamburguesas', 'helado artesanal'],
}

INTEREST_QUERIES = {
    'comida': ['restaurante', 'hamburguesas', 'helado artesanal'],
    'rumba': ['discoteca', 'rooftop', 'bar'],
    'naturaleza': ['mirador', 'parque'],
    'cine': ['cine'],
    'arte': ['museo', 'galería'],
    'café': ['café', 'coffee roaster'],
    'compras': ['centro comercial', 'mercado artesanal'],
    'deporte': ['bowling', 'cancha deportiva'],
}


class PlanGenerationError(Exception):
    def __init__(self, message: str, debug_payload: dict | None = None):
        super().__init__(message)
        self.debug_payload = debug_payload or {}


def validate_ai_json(data: dict):
    if not isinstance(data, dict):
        raise ValueError('Respuesta AI inválida.')
    required = ['title', 'city', 'mood', 'blocks', 'total_estimated_cost_cop']
    for key in required:
        if key not in data:
            raise ValueError(f'Falta campo obligatorio: {key}')
    if not isinstance(data['blocks'], list):
        raise ValueError('El campo blocks debe ser una lista.')


def _collect_queries(mood: str, interests: list[str]) -> list[str]:
    queries = []
    queries.extend(MOOD_QUERIES.get(mood, []))
    for interest in interests:
        queries.extend(INTEREST_QUERIES.get(interest, [interest]))
    return list(OrderedDict.fromkeys(queries))


def build_places_payload(city: str, mood: str, interests: list[str], limit_per_query: int = 7):
    raw: dict = {'queries': []}
    candidates = []
    seen_ids: set[str] = set()
    queries = _collect_queries(mood, interests)

    for keyword in queries:
        try:
            results = text_search(keyword, city, limit=limit_per_query)
            raw['queries'].append({'keyword': keyword, 'status': 'OK', 'results': results})
        except GooglePlacesAPIError as exc:
            raw['queries'].append({'keyword': keyword, 'status': 'ERROR', 'error': exc.payload or {'message': str(exc)}})
            raise PlanGenerationError('Tuvimos un problema consultando Google Places.', debug_payload=raw)

        for place in results:
            place_id = place.get('place_id')
            if not place_id or place_id in seen_ids:
                continue
            seen_ids.add(place_id)
            details = place_details(place_id)
            candidates.append(
                {
                    'place_id': place_id,
                    'name': details.get('name') or place.get('name'),
                    'address': details.get('formatted_address') or place.get('formatted_address', ''),
                    'rating': details.get('rating') or place.get('rating'),
                    'maps_url': details.get('url') or f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                    'price_level': details.get('price_level'),
                }
            )

    return raw, candidates[:40]


def create_plan(form_data: dict):
    raw_places, candidate_places = build_places_payload(
        form_data['city'],
        form_data['mood'],
        form_data['interests'],
    )
    if not candidate_places:
        raise PlanGenerationError('No encontramos suficientes lugares para crear tu plan.', debug_payload=raw_places)

    prompt_payload = {
        'context': {
            'city': form_data['city'],
            'mood': form_data['mood'],
            'start_time': str(form_data['start_time']),
            'end_time': str(form_data['end_time']),
            'budget_cop': form_data['budget'],
            'group_size': form_data['group_size'],
            'transport': form_data['transport'],
            'interests': form_data['interests'],
            'radius_km': form_data['radius_km'],
        },
        'places': candidate_places,
    }
    ai_plan = generate_plan(prompt_payload)
    validate_ai_json(ai_plan)
    return raw_places, ai_plan
