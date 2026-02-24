import json

import requests
from django.conf import settings


class OpenRouterError(Exception):
    pass


def _headers() -> dict[str, str]:
    headers = {
        'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }
    if settings.OPENROUTER_SITE_URL:
        headers['HTTP-Referer'] = settings.OPENROUTER_SITE_URL
    if settings.OPENROUTER_APP_NAME:
        headers['X-Title'] = settings.OPENROUTER_APP_NAME
    return headers


def _request(messages: list[dict[str, str]]) -> dict:
    payload = {
        'model': settings.OPENROUTER_MODEL,
        'messages': messages,
        'temperature': 0.2,
        'response_format': {'type': 'json_object'},
    }
    response = requests.post(settings.OPENROUTER_BASE_URL, headers=_headers(), json=payload, timeout=35)
    response.raise_for_status()
    return response.json()


def _extract_json(response_data: dict) -> dict:
    content = response_data['choices'][0]['message']['content']
    return json.loads(content)


def parse_user_prompt(user_prompt: str) -> dict:
    if not settings.OPENROUTER_API_KEY:
        raise OpenRouterError('OPENROUTER_API_KEY no configurada.')

    schema_hint = {
        'city': 'Medellín',
        'country': 'CO',
        'budget_cop': 120000,
        'mood': 'alegre',
        'group': 'amigos',
        'time_windows': [
            {'label': 'Tarde', 'start': '15:00', 'end': '18:30', 'vibes': ['chill'], 'place_types': ['cafe', 'ice_cream', 'park']},
            {'label': 'Noche', 'start': '19:00', 'end': '23:30', 'vibes': ['rumba suave'], 'place_types': ['bar', 'brewery', 'live music']},
        ],
        'constraints': {'max_distance_km': 8, 'avoid': ['muy caro'], 'prioritize': ['rating>=4.4', 'popular']},
    }
    messages = [
        {
            'role': 'system',
            'content': (
                'Eres un parser experto para una app de planes. Devuelve SOLO JSON válido y estricto, sin markdown ni texto extra. '
                'Si faltan datos, infiérelos de forma razonable para Colombia. Estructura exacta esperada: '
                f'{json.dumps(schema_hint, ensure_ascii=False)}'
            ),
        },
        {'role': 'user', 'content': user_prompt},
    ]

    try:
        return _extract_json(_request(messages))
    except (requests.RequestException, KeyError, json.JSONDecodeError):
        retry_messages = messages + [
            {'role': 'user', 'content': 'Devuelve SOLO JSON válido. Sin comentarios, sin texto adicional.'}
        ]
        try:
            return _extract_json(_request(retry_messages))
        except (requests.RequestException, KeyError, json.JSONDecodeError) as exc:
            raise OpenRouterError('No fue posible obtener JSON válido desde OpenRouter.') from exc
