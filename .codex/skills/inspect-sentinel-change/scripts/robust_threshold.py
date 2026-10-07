"""Experimental tile-level robust NDVI scoring; no geospatial IO or road labels."""
import warnings
import numpy as np


def robust_candidate(reference, target, *, k=2.5, delta_min=0.15, epsilon=0.02, min_count=5):
    reference = np.asarray(reference, dtype=float)
    target = np.asarray(target, dtype=float)
    if reference.ndim < 2 or reference.shape[1:] != target.shape:
        raise ValueError("Reference must be (time, ...) matching target shape")
    if k <= 0 or delta_min <= 0 or epsilon <= 0 or min_count < 2:
        raise ValueError("Invalid screening parameters")
    reference = np.where(np.isfinite(reference) & (np.abs(reference) <= 1), reference, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        median = np.nanmedian(reference, axis=0)
        mad = np.nanmedian(np.abs(reference - median), axis=0)
    count = np.sum(np.isfinite(reference), axis=0)
    valid = (count >= min_count) & np.isfinite(target) & (np.abs(target) <= 1) & np.isfinite(median)
    drop = median - target
    scale = np.maximum(1.4826 * mad, epsilon)
    score = np.where(valid, drop / scale, np.nan)
    candidate = np.full(target.shape, 255, dtype=np.uint8)
    candidate[valid] = ((score[valid] > k) & (drop[valid] > delta_min)).astype(np.uint8)
    return dict(candidate=candidate, valid=valid, count=count, median=median, mad=mad, score=score)


def self_test():
    x = np.full((5, 4), 0.6)
    x[:, 2] = np.nan
    x[0, 3] = np.nan
    r = robust_candidate(x, np.array([0.3, 0.6, 0.3, 0.3]))
    assert r['candidate'].tolist() == [1, 0, 255, 255]
    assert np.isnan(r['score'][2:]).all()
    # Strict score boundary: constant baseline with declared floor.
    r = robust_candidate(np.full((5, 1), 0.5), np.array([0.25]), k=2.5, epsilon=0.1, delta_min=0.1)
    assert r['candidate'][0] == 0
    r = robust_candidate(np.full((5, 1), 0.5), np.array([0.25]), k=2, epsilon=0.1, delta_min=0.25)
    assert r['candidate'][0] == 0
    try:
        robust_candidate(x, np.zeros(3))
    except ValueError:
        pass
    else:
        raise AssertionError('Shape mismatch accepted')
    print('5 synthetic checks passed; no real-data accuracy claim')

if __name__ == '__main__':
    self_test()
