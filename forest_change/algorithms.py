"""Pure array semantics, independent of catalogue and raster IO."""
import warnings
import numpy as np
from scipy.ndimage import label

OPTICAL = {'NDVI': ('nir', 'red'), 'NDMI': ('nir', 'swir1'), 'NBR': ('nir', 'swir2')}


def normalized_difference(a, b):
    out = np.full(a.shape, np.nan, dtype='float32')
    np.divide(a-b, a+b, out=out, where=np.isfinite(a) & np.isfinite(b) & ((a+b) != 0))
    return out


def feature(name, bands, units='db'):
    if name in OPTICAL:
        a, b = OPTICAL[name]
        return normalized_difference(bands[a], bands[b])
    if name in ('VV', 'VH'):
        x = bands[name]
        if units == 'linear':
            return np.where(x > 0, 10*np.log10(np.where(x > 0, x, np.nan)), np.nan)
        if units != 'db':
            raise ValueError('SAR units must be db or linear')
        return x
    if name == 'VV_MINUS_VH_DB':
        return feature('VV', bands, units) - feature('VH', bands, units)
    raise ValueError(f'Unsupported feature: {name}')


def aggregate(stack, method):
    if method not in ('mean', 'median', 'std'):
        raise ValueError(f'Unsupported aggregation: {method}')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        return {'mean': np.nanmean, 'median': np.nanmedian, 'std': np.nanstd}[method](stack, axis=0).astype('float32')


def fuse(optical, sar, mode, optical_weight=.7, sar_weight=.3, threshold=.5):
    """NaN denotes unavailable evidence; never treat missingness as absence."""
    ov, sv = np.isfinite(optical), np.isfinite(sar)
    o, s = optical == 1, sar == 1
    both = ov & sv
    agreement = np.where(both, o == s, np.nan).astype('float32')
    disagreement = np.where(both, o != s, np.nan).astype('float32')
    if mode == 'optical_only':
        result = optical.copy()
    elif mode == 'sar_only':
        result = sar.copy()
    elif mode in ('optical_and_sar', 'optical_or_sar'):
        result = np.where(both, (o & s) if mode == 'optical_and_sar' else (o | s), np.nan).astype('float32')
    elif mode == 'weighted_confidence':
        if optical_weight < 0 or sar_weight < 0 or not np.isclose(optical_weight+sar_weight, 1) or not 0 <= threshold <= 1:
            raise ValueError('Nonnegative fusion weights must sum to one; threshold must lie in [0,1]')
        score = optical_weight*optical + sar_weight*sar
        result = np.where(both, score >= threshold, np.nan).astype('float32')
    else:
        raise ValueError(f'Unsupported fusion mode: {mode}')
    return result, agreement, disagreement


def clean(mask, minimum):
    if minimum <= 1:
        return mask
    labels, _ = label(mask == 1, structure=np.ones((3, 3)))
    sizes = np.bincount(labels.ravel())
    return np.where(np.isfinite(mask), (labels > 0) & (sizes[labels] >= minimum), np.nan).astype('float32')
