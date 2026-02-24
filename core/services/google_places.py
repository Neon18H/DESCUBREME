from typing import Any
from urllib.parse import quote_plus

import requests
from django.conf import settings

TEXT_SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'


class GooglePlacesAPIError(Exception):
    pass


def price_level_to_cop(price_level: int | None) -> int | None:
    mapping = {0: 15000, 1: 30000, 2: 60000, 3: 110000, 4: 180000}
    return mapping.get(price_level)


def _safe_get(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def _build_maps_url(place_id: str) -> str:
    return f'https://www.google.com/maps/search/?api=1&query=google&query_place_id={quote_plus(place_id)}'


def _build_photo_url(photo_reference: str) -> str:
    return (
        'https://maps.googleapis.com/maps/api/place/photo?maxwidth=1200'
        f'&photo_reference={quote_plus(photo_reference)}&key={settings.GOOGLE_PLACES_API_KEY}'
    )


def search_places(query: str, city: str, limit: int = 3, lat: float | None = None, lng: float | None = None) -> list[dict[str, Any]]:
    if not settings.GOOGLE_PLACES_API_KEY:
        raise GooglePlacesAPIError('GOOGLE_PLACES_API_KEY no configurada.')

    full_query = f'{query} en {city}' if city else query
    params = {'query': full_query, 'language': 'es', 'region': 'co', 'key': settings.GOOGLE_PLACES_API_KEY}
    if lat is not None and lng is not None:
        params.update({'location': f'{lat},{lng}', 'radius': 6500})
    payload = _safe_get(TEXT_SEARCH_URL, params)

    status = payload.get('status')
    if status == 'ZERO_RESULTS':
        return []
    if status != 'OK':
        raise GooglePlacesAPIError(f'Google Places respondió {status}.')

    places = []
    for place in payload.get('results', [])[:limit]:
        photo_reference = None
        photos = place.get('photos') or []
        if photos:
            photo_reference = photos[0].get('photo_reference')

        price_level = place.get('price_level')
        places.append(
            {
                'name': place.get('name', 'Lugar recomendado'),
                'place_id': place.get('place_id', ''),
                'rating': place.get('rating'),
                'user_ratings_total': place.get('user_ratings_total'),
                'price_level': price_level,
                'estimated_cost_cop': price_level_to_cop(price_level),
                'address': place.get('formatted_address') or place.get('vicinity', ''),
                'photo_reference': photo_reference,
                'photo_url': _build_photo_url(photo_reference) if photo_reference else '',
                'maps_url': _build_maps_url(place.get('place_id', '')),
                'raw_payload': place,
            }
        )
    return places
