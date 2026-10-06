"""Observation discovery is replaceable; algorithms consume named raster assets."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import rasterio
from shapely.geometry import shape

from .evidence import checksum, geometry_hash, load


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


class ObservationProvider(ABC):
    @abstractmethod
    def search(self, geometry, start, end, filters):
        """Return sorted items within half-open UTC date range and spatial footprint."""

    def open_asset(self, asset):
        return rasterio.open(asset['href'])

    @abstractmethod
    def describe_source(self):
        pass

    def record_query(self, geometry, start, end, filters, items):
        return {**self.describe_source(), 'query_geometry_hash': geometry_hash(geometry),
                'time_range': [start, end], 'filters': filters,
                'query_timestamp': utc_now(), 'items': items}


class LocalRasterProvider(ObservationProvider):
    def __init__(self, config):
        self.config = config
        self.path = Path(config['inventory']).resolve()
        self.items = load(self.path)['items']
        for item in self.items:
            for asset in item['assets'].values():
                p = Path(asset['href'])
                if not p.is_absolute():
                    p = self.path.parent / p
                asset['href'] = str(p.resolve())
        if len({i['id'] for i in self.items}) != len(self.items):
            raise ValueError('Duplicate local item IDs')

    def describe_source(self):
        return {'provider': 'local-raster', 'collection': self.config['collection'],
                'inventory': str(self.path), 'inventory_sha256': checksum(self.path)}

    def search(self, geometry, start, end, filters):
        selected = []
        for item in self.items:
            # datetime.date strings and UTC timestamps compare consistently after normalization.
            instant = datetime.fromisoformat(item['datetime'].replace('Z', '+00:00'))
            if instant.tzinfo is None:
                instant = instant.replace(tzinfo=timezone.utc)
            day = instant.astimezone(timezone.utc).isoformat()[:10]
            if not start <= day < end:
                continue
            if not shape(item['geometry']).intersects(shape(geometry)):
                continue
            if any(item.get('properties', {}).get(k) != v for k, v in filters.items()):
                continue
            selected.append(item)
        return sorted(selected, key=lambda i: (i['datetime'], i['id']))


class STACProvider(ObservationProvider):
    def __init__(self, config, client=None):
        self.config = config
        self.client = client

    def describe_source(self):
        return {'provider': 'stac', 'endpoint': self.config['endpoint'], 'collection': self.config['collection']}

    def search(self, geometry, start, end, filters):
        if self.client is None:
            from pystac_client import Client
            self.client = Client.open(self.config['endpoint'])
        query = {k: {'eq': v} for k, v in filters.items()}
        found = self.client.search(collections=[self.config['collection']], intersects=geometry,
                                   datetime=f'{start}T00:00:00Z/{end}T00:00:00Z', query=query)
        result = []
        for item in found.items():
            raw = item.to_dict()
            instant = datetime.fromisoformat(raw['properties']['datetime'].replace('Z', '+00:00'))
            day = instant.astimezone(timezone.utc).isoformat()[:10]
            if not start <= day < end:
                continue  # STAC endpoint end may be inclusive.
            if any(raw['properties'].get(k) != v for k, v in filters.items()):
                continue
            assets = {}
            for name, key in self.config['asset_map'].items():
                if key not in raw['assets']:
                    raise ValueError(f'{item.id} missing mapped asset {key}')
                assets[name] = {**raw['assets'][key], 'asset_id': key,
                                **self.config.get('asset_calibration', {}).get(name, {})}
            result.append({'id': raw['id'], 'datetime': raw['properties']['datetime'],
                           'geometry': raw['geometry'], 'properties': raw['properties'], 'assets': assets})
        return sorted(result, key=lambda i: (i['datetime'], i['id']))


def provider(config):
    if config['type'] == 'local':
        return LocalRasterProvider(config)
    if config['type'] == 'stac':
        return STACProvider(config)
    raise ValueError('Provider type must be local or stac')


def validate_calibration_requirements(item, config):
    for key, expected in config.get('calibration_requirements', {}).items():
        if item.get('properties', {}).get(key) != expected:
            raise ValueError(f"{item['id']} fails calibration requirements: {key} must equal {expected}")
