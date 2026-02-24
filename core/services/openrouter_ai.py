import json

import requests
from django.conf import settings


class OpenRouterError(Exception):
    pass


def _request(messages):
    headers = {
        'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': settings.APP_REFERER,
        'X-Title': 'Descubriendo MVP',
    }
    payload = {
        'model': settings.OPENROUTER_MODEL,
        'messages': messages,
        'temperature': 0.5,
        'response_format': {'type': 'json_object'},
    }
    response = requests.post(settings.OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def generate_plan(prompt_payload: dict) -> dict:
    if not settings.OPENROUTER_API_KEY:
        raise OpenRouterError('OPENROUTER_API_KEY no configurada.')

    system_prompt = (
        'Eres un planificador experto de ocio urbano en Colombia. '
        'Responde SOLO JSON válido sin markdown. '
        'Estructura requerida: {"title":"", "narrative":"", "blocks":{"tarde":{"steps":[]},"noche":{"steps":[]}} }.'
    )
    user_prompt = json.dumps(prompt_payload, ensure_ascii=False)
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]

    try:
        data = _request(messages)
        content = data['choices'][0]['message']['content']
        return json.loads(content)
    except (requests.RequestException, KeyError, json.JSONDecodeError) as exc:
        fix_messages = messages + [
            {
                'role': 'user',
                'content': 'Corrige y devuelve únicamente JSON válido siguiendo la estructura indicada.',
            }
        ]
        try:
            data = _request(fix_messages)
            content = data['choices'][0]['message']['content']
            return json.loads(content)
        except Exception as retry_exc:
            raise OpenRouterError('No fue posible generar un JSON válido desde OpenRouter.') from retry_exc
