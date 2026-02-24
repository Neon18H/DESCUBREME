from typing import Dict, List

import requests
from django.conf import settings

TEXT_SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'


class GooglePlacesError(Exception):
    pass


def text_search(query: str, city: str, limit: int = 10) -> List[Dict]:
    if not settings.GOOGLE_PLACES_API_KEY:
        return []
    params = {
        'query': f'{query} en {city}',
        'key': settings.GOOGLE_PLACES_API_KEY,
        'language': 'es',
    }
    try:
        response = requests.get(TEXT_SEARCH_URL, params=params, timeout=12)
        response.raise_for_status()
        data = response.json()
        if data.get('status') not in ['OK', 'ZERO_RESULTS']:
            raise GooglePlacesError(data.get('error_message', 'Error en Google Places Text Search'))
        return data.get('results', [])[:limit]
    except requests.RequestException as exc:
        raise GooglePlacesError('No se pudo conectar con Google Places.') from exc


def place_details(place_id: str) -> Dict:
    if not settings.GOOGLE_PLACES_API_KEY:
        return {}
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,rating,price_level,url,opening_hours',
        'language': 'es',
        'key': settings.GOOGLE_PLACES_API_KEY,
    }
    try:
        response = requests.get(DETAILS_URL, params=params, timeout=12)
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 'OK':
            return {}
        return data.get('result', {})
    except requests.RequestException:
        return {}
