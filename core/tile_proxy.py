"""
Tile caching proxy — fetches map tiles from upstream providers,
saves them to disk, and serves cached copies on subsequent requests.

After a week of normal use, all commonly-viewed areas will be locally
cached and zero requests will go to upstream providers.

Providers supported:
    esri-street   → ESRI World Street Map          (default)
    esri-imagery  → ESRI World Imagery             (aerial/satellite)
    esri-natgeo   → ESRI National Geographic       (NatGeo cartographic)
    esri-topo     → ESRI World Topo Map            (topographic)
    esri-relief   → ESRI World Shaded Relief       (terrain shading, no labels)
    esri-dark     → ESRI Dark Gray Canvas          (dark minimal)
    osm           → OpenStreetMap                  (community)
    carto-light   → CartoDB Positron               (clean light)
    carto-dark    → CartoDB Dark Matter            (dark, high-contrast)
    nasa-night    → NASA Black Marble (VIIRS)      (night-time city lights)
    nasa-day      → NASA MODIS True Colour         (daytime Earth from space)
    opentopomap   → OpenTopoMap                    (hiking / relief detail)

Coordinate-order note
---------------------
ESRI and NASA GIBS tiles use  {z}/{y}/{x}  (TileMatrix / TileRow / TileCol).
OSM, CartoDB and OpenTopoMap use  {z}/{x}/{y}.
The proxy handles this internally; the frontend always sends {z}/{x}/{y}.
"""
import os
import logging

import requests
from django.http import HttpResponse, Http404

logger = logging.getLogger(__name__)

# Root directory for persisted tile cache
TILE_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'cache', 'tiles'
)

PROVIDERS = {
    # ── ESRI (z/y/x order) ───────────────────────────────────────────
    'esri-street': {
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/'
               'World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
    'esri-imagery': {
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/'
               'World_Imagery/MapServer/tile/{z}/{y}/{x}',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
    'esri-natgeo': {
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/'
               'NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
    'esri-topo': {
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/'
               'World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
    'esri-relief': {
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/'
               'World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
    'esri-dark': {
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/'
               'Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
    # ── OSM-convention (z/x/y order) ─────────────────────────────────
    'osm': {
        'url': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        'content_type': 'image/png',
        'ext': 'png',
    },
    'carto-light': {
        'url': 'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
        'content_type': 'image/png',
        'ext': 'png',
    },
    'carto-dark': {
        'url': 'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
        'content_type': 'image/png',
        'ext': 'png',
    },
    'opentopomap': {
        'url': 'https://tile.opentopomap.org/{z}/{x}/{y}.png',
        'content_type': 'image/png',
        'ext': 'png',
    },
    'osm-hot': {
        # OSM Humanitarian — warm palette used in disaster/aid mapping
        'url': 'https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        'content_type': 'image/png',
        'ext': 'png',
    },
    # ── ESRI specialty ───────────────────────────────────────────────
    'esri-ocean': {
        # Ocean Base — beautiful bathymetric depth shading
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/'
               'Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
    'esri-physical': {
        # Physical Map — natural terrain colours, no political borders
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/'
               'World_Physical_Map/MapServer/tile/{z}/{y}/{x}',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
    # ── CartoDB Voyager ──────────────────────────────────────────────
    'carto-voyager': {
        # Voyager — polished mid-tone design between light and dark
        'url': 'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
        'content_type': 'image/png',
        'ext': 'png',
    },
    # ── NASA GIBS (z/y/x order) ──────────────────────────────────────
    'nasa-day': {
        # MODIS Terra true-colour composite — verified 200 OK
        'url': 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/'
               'MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-06-01/'
               'GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
        'content_type': 'image/jpeg',
        'ext': 'jpg',
    },
}

_FETCH_HEADERS = {
    'User-Agent': 'SattTrack/2.0 (satellite tracking educational application)',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
}


def _cache_path(provider: str, z: int, x: int, y: int) -> str:
    ext = PROVIDERS[provider]['ext']
    return os.path.join(TILE_CACHE_DIR, provider, str(z), str(x), f'{y}.{ext}')


def serve_tile(request, provider: str, z: int, x: int, y: int) -> HttpResponse:
    """
    GET /tiles/<provider>/<z>/<x>/<y>/

    Returns the tile image.  Disk cache is checked first; on a cache miss
    the tile is fetched from the upstream provider, written to disk, and
    returned.  All subsequent requests for the same tile are served from
    disk with no upstream call.
    """
    if provider not in PROVIDERS:
        raise Http404(f'Unknown tile provider: {provider}')

    path = _cache_path(provider, z, x, y)

    # ── Serve from disk cache ─────────────────────────────────────────
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            data = fh.read()
        resp = HttpResponse(data, content_type=PROVIDERS[provider]['content_type'])
        resp['Cache-Control'] = 'public, max-age=604800'   # 7 days
        resp['X-Tile-Source'] = 'cache'
        return resp

    # ── Fetch from upstream ───────────────────────────────────────────
    prov = PROVIDERS[provider]
    upstream = prov['url'].format(z=z, x=x, y=y)

    try:
        up_resp = requests.get(upstream, headers=_FETCH_HEADERS, timeout=10)
        up_resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning('Tile upstream fetch failed %s: %s', upstream, exc)
        return HttpResponse(status=503)

    tile_data = up_resp.content

    # ── Persist to disk ───────────────────────────────────────────────
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, 'wb') as fh:
            fh.write(tile_data)
    except OSError as exc:
        logger.warning('Could not write tile cache %s: %s', path, exc)

    resp = HttpResponse(tile_data, content_type=prov['content_type'])
    resp['Cache-Control'] = 'public, max-age=604800'
    resp['X-Tile-Source'] = 'upstream'
    return resp
