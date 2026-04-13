"""
Management command: warmtiles
─────────────────────────────
Pre-populates the tile cache for zoom levels 0-5 (1,365 tiles total for the
whole globe).  Run this once after deployment so users immediately get
fast, locally-served tiles at any zoom level that shows the full Earth.

Usage:
    python manage.py warmtiles
    python manage.py warmtiles --provider esri-imagery --max-zoom 4
    python manage.py warmtiles --max-zoom 7 --delay 0.1

Zoom tile counts:
    Level 0 →     1 tile
    Level 1 →     4 tiles
    Level 2 →    16 tiles
    Level 3 →    64 tiles
    Level 4 →   256 tiles
    Level 5 →  1024 tiles   (total 0-5: 1,365)
    Level 6 →  4096 tiles   (total 0-6: 5,461 — takes a few minutes)
"""
import os
import time
import requests
from django.core.management.base import BaseCommand

from core.tile_proxy import PROVIDERS, _cache_path, _FETCH_HEADERS


class Command(BaseCommand):
    help = 'Pre-warm tile cache for low zoom levels (global coverage)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider', default='esri-street',
            help='Provider to warm (default: esri-street)',
        )
        parser.add_argument(
            '--max-zoom', type=int, default=5,
            help='Highest zoom level to pre-fetch (default: 5)',
        )
        parser.add_argument(
            '--delay', type=float, default=0.05,
            help='Seconds to wait between upstream requests (default: 0.05)',
        )

    def handle(self, *args, **options):
        provider = options['provider']
        max_zoom = options['max_zoom']
        delay = options['delay']

        if provider not in PROVIDERS:
            self.stderr.write(self.style.ERROR(f'Unknown provider: {provider}. '
                                               f'Choose from: {", ".join(PROVIDERS)}'))
            return

        total = sum(4 ** z for z in range(max_zoom + 1))
        self.stdout.write(
            f'Warming "{provider}" tiles zoom 0-{max_zoom}  '
            f'({total} tiles, skipping already-cached)…'
        )

        prov = PROVIDERS[provider]
        fetched = skipped = failed = 0

        for z in range(max_zoom + 1):
            n = 2 ** z
            for x in range(n):
                for y in range(n):
                    path = _cache_path(provider, z, x, y)
                    if os.path.exists(path):
                        skipped += 1
                        continue

                    upstream = prov['url'].format(z=z, x=x, y=y)
                    try:
                        resp = requests.get(upstream, headers=_FETCH_HEADERS, timeout=15)
                        resp.raise_for_status()
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        with open(path, 'wb') as fh:
                            fh.write(resp.content)
                        fetched += 1
                        if delay:
                            time.sleep(delay)
                    except Exception as exc:
                        failed += 1
                        self.stdout.write(f'  FAIL z={z} x={x} y={y}: {exc}')

            self.stdout.write(f'  Zoom {z} done')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone!  Fetched: {fetched} | Skipped (cached): {skipped} | Failed: {failed}'
        ))
