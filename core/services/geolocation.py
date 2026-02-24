from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings
from django.utils.text import slugify

GOOGLE_GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
NOMINATIM_REVERSE_URL = 'https://nominatim.openstreetmap.org/reverse'


@dataclass
class ResolvedLocation:
    city_name: str
    city_slug: str
    country_code: str


class GeolocationError(Exception):
    pass


def _normalize(city_name: str, country_code: str = 'CO') -> ResolvedLocation:
    cleaned_city = (city_name or 'Colombia').strip()
    code = (country_code or 'CO').upper()[:2]
    return ResolvedLocation(city_name=cleaned_city, city_slug=slugify(cleaned_city), country_code=code)


def _city_from_google(lat: float, lng: float) -> ResolvedLocation | None:
    if not settings.GOOGLE_PLACES_API_KEY:
        return None
    response = requests.get(
        GOOGLE_GEOCODE_URL,
        params={'latlng': f'{lat},{lng}', 'key': settings.GOOGLE_PLACES_API_KEY, 'language': 'es'},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get('status') != 'OK':
        return None

    for result in payload.get('results', []):
        city = ''
        country = 'CO'
        for component in result.get('address_components', []):
            types = component.get('types', [])
            if 'locality' in types or 'administrative_area_level_2' in types:
                city = component.get('long_name', city)
            if 'country' in types:
                country = component.get('short_name', country)
        if city:
            return _normalize(city, country)
    return None


def _city_from_nominatim(lat: float, lng: float) -> ResolvedLocation | None:
    response = requests.get(
        NOMINATIM_REVERSE_URL,
        params={'lat': lat, 'lon': lng, 'format': 'jsonv2', 'accept-language': 'es'},
        headers={'User-Agent': 'DescubremeBot/1.0'},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    address = payload.get('address', {})
    city = address.get('city') or address.get('town') or address.get('municipality') or address.get('state_district')
    country_code = (address.get('country_code') or 'co').upper()
    if not city:
        return None
    return _normalize(city, country_code)


def resolve_city_from_coordinates(lat: float | None, lng: float | None) -> ResolvedLocation | None:
    if lat is None or lng is None:
        return None
    try:
        return _city_from_google(lat, lng) or _city_from_nominatim(lat, lng)
    except requests.RequestException as exc:
        raise GeolocationError('No fue posible resolver la ciudad por GPS.') from exc
