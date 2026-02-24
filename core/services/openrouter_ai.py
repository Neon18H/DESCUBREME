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
        'temperature': 0.4,
        'response_format': {'type': 'json_object'},
    }
    response = requests.post(
        settings.OPENROUTER_BASE_URL,
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _extract_json(response_data: dict) -> dict:
    content = response_data['choices'][0]['message']['content']
    return json.loads(content)


def generate_plan(prompt_payload: dict) -> dict:
    if not settings.OPENROUTER_API_KEY:
        raise OpenRouterError('OPENROUTER_API_KEY no configurada.')

    system_prompt = (
        'Eres planificador experto. Devuelve SOLO JSON válido, sin markdown. '
        'Schema exacto: '
        '{"title":"...","city":"...","mood":"...",'
        '"blocks":[{"name":"tarde","steps":[{"title":"","description":"","why":"",'
        '"estimated_time_minutes":60,"estimated_cost_cop":30000,'
        '"place":{"name":"","address":"","rating":4.5,"maps_url":""}}]},'
        '{"name":"noche","steps":[]}],"total_estimated_cost_cop":123456}'
    )
    user_prompt = json.dumps(prompt_payload, ensure_ascii=False)
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt},
    ]

    try:
        return _extract_json(_request(messages))
    except (requests.RequestException, KeyError, json.JSONDecodeError) as first_error:
        fix_messages = messages + [
            {
                'role': 'user',
                'content': 'Tu salida anterior no fue JSON válido. Corrígela y entrega SOLO JSON válido, sin texto adicional.',
            }
        ]
        try:
            return _extract_json(_request(fix_messages))
        except (requests.RequestException, KeyError, json.JSONDecodeError) as retry_error:
            raise OpenRouterError('No fue posible obtener JSON válido desde OpenRouter.') from retry_error
