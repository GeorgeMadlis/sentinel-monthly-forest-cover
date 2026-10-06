"""Provenance-checked source cache; default to verified HTTP range access."""
from pathlib import Path
from hashlib import sha256
from urllib.request import Request, urlopen
import shutil
import rasterio
from .evidence import load, write_json, checksum
from .providers import utc_now


def supports_ranges(url):
    with urlopen(Request(url, headers={'Range': 'bytes=0-0'}), timeout=30) as response:
        return response.status == 206 and response.headers.get('Content-Range', '').startswith('bytes 0-0/')


def download(url, path):
    with urlopen(url, timeout=120) as response, open(path, 'wb') as dest:
        shutil.copyfileobj(response, dest)


class AssetResolver:
    def __init__(self, cache, policy='auto', range_probe=supports_ranges, downloader=download):
        if policy not in ('auto', 'remote', 'cache'):
            raise ValueError('Access policy must be auto, remote or cache')
        self.cache = Path(cache).resolve()
        self.policy, self.probe, self.download = policy, range_probe, downloader
        self.records = {}

    def resolve(self, item, key, asset, remote_failed=False):
        url = asset['href']
        identity = {'item_id': item['id'], 'asset_key': key, 'source_url': url,
                    'acquisition_timestamp': item['datetime']}
        name = sha256((item['id']+'\n'+key+'\n'+url).encode()).hexdigest()
        path = self.cache / (name+'.tif')
        meta = path.with_suffix('.json')
        mode, reason, href = 'remote_cog', 'HTTP range request verified; AOI windows only', url
        cached = False
        if meta.exists() and path.exists():
            record = load(meta)
            try:
                with rasterio.open(path) as src:
                    src.read(1, window=((0, 1), (0, 1)))
                    valid = src.crs is not None
                cached = valid and all(record.get(k) == v for k,v in identity.items()) and record.get('sha256') == checksum(path)
            except (OSError, rasterio.errors.RasterioError):
                cached = False
        if cached:
            mode, reason, href = 'cached_cog', 'Exact source identity, checksum and raster readability verified', str(path)
        elif '://' not in url:
            with rasterio.open(url) as src:
                if not src.crs:
                    raise ValueError('Local source has no CRS')
                src.read(1, window=((0,1),(0,1)))
            mode, reason, href = 'local_raster', 'Existing local georeferenced raster', str(Path(url).resolve())
        else:
            try:
                ranges = False if remote_failed or self.policy == 'cache' else self.probe(url)
            except OSError:
                ranges = False
            if self.policy == 'remote' and not ranges:
                raise IOError('Remote-only access requested but range access failed')
            if not ranges:
                self.cache.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix('.part')
                try:
                    self.download(url, temporary)
                    with rasterio.open(temporary) as src:
                        if not src.crs:
                            raise ValueError('Downloaded source has no CRS')
                        src.read(1, window=((0,1),(0,1)))
                    temporary.replace(path)
                finally:
                    temporary.unlink(missing_ok=True)
                write_json(meta, {**identity, 'local_path': str(path), 'file_size': path.stat().st_size,
                                  'sha256': checksum(path), 'download_timestamp': utc_now()})
                mode, reason, href = 'cached_cog', 'Explicit cache policy or failed range/window access', str(path)
        record = {**identity, 'access_mode': mode, 'rationale': reason}
        if mode != 'remote_cog':
            record.update(local_path=href, file_size=Path(href).stat().st_size, sha256=checksum(href))
            if mode == 'cached_cog':
                record['download_timestamp'] = load(meta)['download_timestamp']
        self.records[(item['id'],key)] = record
        return {**asset, 'href': href}, record
