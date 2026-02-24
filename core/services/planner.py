from core.services.google_places import place_details, text_search
from core.services.openrouter_ai import generate_plan

INTEREST_QUERIES = {
    'comida': ['restaurante recomendado', 'helado artesanal'],
    'rumba': ['discoteca', 'cervecería artesanal'],
    'naturaleza': ['parque ecológico', 'mirador'],
    'cine': ['cine'],
    'arte': ['museo de arte', 'galería'],
    'café': ['café de especialidad'],
    'compras': ['centro comercial', 'tienda local'],
    'deporte': ['cancha deportiva', 'gimnasio'],
}


def validate_ai_json(data: dict):
    if not isinstance(data, dict):
        raise ValueError('Respuesta AI inválida.')
    for key in ['title', 'narrative', 'blocks']:
        if key not in data:
            raise ValueError(f'Falta campo obligatorio: {key}')
    for block in ['tarde', 'noche']:
        if block not in data['blocks'] or 'steps' not in data['blocks'][block]:
            raise ValueError(f'Falta bloque {block}')
        if not isinstance(data['blocks'][block]['steps'], list):
            raise ValueError(f'Bloque {block} sin steps válidos')
        for step in data['blocks'][block]['steps']:
            required = ['title', 'description', 'why', 'estimated_time_minutes', 'estimated_cost_cop', 'place']
            for field in required:
                if field not in step:
                    raise ValueError(f'Campo faltante en step: {field}')


def build_places_payload(city: str, interests: list, limit_per_interest=10):
    raw = {}
    candidates = []
    for interest in interests:
        queries = INTEREST_QUERIES.get(interest, [interest])
        for query in queries:
            results = text_search(query, city, limit=limit_per_interest)
            raw[f'{interest}:{query}'] = results
            for place in results[:5]:
                details = place_details(place.get('place_id', '')) if place.get('place_id') else {}
                item = {
                    'name': details.get('name') or place.get('name'),
                    'address': details.get('formatted_address') or place.get('formatted_address', ''),
                    'rating': details.get('rating') or place.get('rating'),
                    'maps_url': details.get('url'),
                    'price_level': details.get('price_level'),
                    'open_now': (details.get('opening_hours') or {}).get('open_now'),
                }
                if item['name']:
                    candidates.append(item)
    return raw, candidates[:30]


def create_plan(form_data: dict):
    raw_places, candidate_places = build_places_payload(form_data['city'], form_data['interests'])
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
        'instructions': {
            'blocks': ['tarde', 'noche'],
            'steps_per_block': '2-3',
            'include_maps_url': True,
        },
    }
    ai_plan = generate_plan(prompt_payload)
    validate_ai_json(ai_plan)
    return raw_places, ai_plan
