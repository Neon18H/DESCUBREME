import logging
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings

TEXT_SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'
logger = logging.getLogger(__name__)


@dataclass
class GooglePlacesAPIError(Exception):
    message: str
    payload: dict[str, Any] | None = None


def _parse_response(response: requests.Response) -> dict[str, Any]:
    try:
        return response.json()
    except ValueError:
        return {'status': 'INVALID_JSON', 'raw_text': response.text}


def text_search(query: str, city: str, limit: int = 10) -> list[dict[str, Any]]:
    if not settings.GOOGLE_PLACES_API_KEY:
        raise GooglePlacesAPIError('No configuramos Google Places aún.')

    params = {
        'query': f'{query} en {city}',
        'language': 'es',
        'key': settings.GOOGLE_PLACES_API_KEY,
    }
    try:
        response = requests.get(TEXT_SEARCH_URL, params=params, timeout=15)
        payload = _parse_response(response)
        if response.status_code >= 400:
            logger.error('Google text search HTTP error: %s', payload)
            raise GooglePlacesAPIError('Google Places no respondió correctamente.', payload)

        status = payload.get('status')
        if status == 'ZERO_RESULTS':
            return []
        if status != 'OK':
            logger.error('Google text search status error: %s', payload)
            raise GooglePlacesAPIError('No encontramos lugares ahora mismo, intenta ajustar filtros.', payload)
        return payload.get('results', [])[:limit]
    except requests.RequestException as exc:
        logger.exception('Google text search request exception')
        raise GooglePlacesAPIError('No pudimos conectarnos con Google Places.') from exc


def place_details(place_id: str) -> dict[str, Any]:
    if not place_id or not settings.GOOGLE_PLACES_API_KEY:
        return {}

    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,rating,price_level,url,opening_hours',
        'language': 'es',
        'key': settings.GOOGLE_PLACES_API_KEY,
    }
    try:
        response = requests.get(DETAILS_URL, params=params, timeout=15)
        payload = _parse_response(response)
        if response.status_code >= 400 or payload.get('status') != 'OK':
            logger.warning('Google place details issue for %s: %s', place_id, payload)
            return {}
        return payload.get('result', {})
    except requests.RequestException:
        logger.exception('Google place details request exception for %s', place_id)
        return {}
