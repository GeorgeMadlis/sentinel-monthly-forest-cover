"""Date-only configuration is inclusive; generated windows are half-open UTC dates."""
from datetime import date, timedelta
import calendar


def period(p):
    start, end = date.fromisoformat(str(p['start'])), date.fromisoformat(str(p['end'])) + timedelta(days=1)
    if end <= start:
        raise ValueError('Period end precedes start')
    return start, end


def monthly(year, month):
    return {'start': date(year, month, 1).isoformat(),
            'end': date(year, month, calendar.monthrange(year, month)[1]).isoformat()}


def windows(config):
    t = config['temporal']
    mode = t['mode']
    start, end = period(t['target'])
    refs = [period(p) for p in t['reference_periods']]
    if not refs or any(e > start for s, e in refs):
        raise ValueError('Nonempty reference periods must precede target')
    if mode == 'monthly':
        if start.day != 1 or end != start.replace(day=1) + timedelta(days=calendar.monthrange(start.year, start.month)[1]):
            raise ValueError('Monthly target must be a full calendar month')
        if any(s.month != start.month or s.day != 1 or e != s + timedelta(days=calendar.monthrange(s.year, s.month)[1]) for s, e in refs):
            raise ValueError('Monthly references must be the same full calendar month')
        pairs = [(start, end, refs)]
    elif mode in ('matched-season', 'matched-season-moving-window'):
        if t.get('alignment') != 'calendar-date':
            raise ValueError('Matched-season requires alignment: calendar-date')
        if any((s.month, s.day) != (start.month, start.day) or ((e-timedelta(days=1)).month, (e-timedelta(days=1)).day) != ((end-timedelta(days=1)).month, (end-timedelta(days=1)).day) for s, e in refs):
            raise ValueError('Matched-season endpoints must match calendar dates')
        pairs = [(start, end, refs)] if mode == 'matched-season' else moving(t, start, end, refs, calendar_align=True)
    elif mode == 'moving-window':
        if t.get('alignment') != 'relative-day':
            raise ValueError('Moving-window requires alignment: relative-day')
        if any(e-s != end-start for s, e in refs):
            raise ValueError('Relative-day periods must have equal duration')
        pairs = moving(t, start, end, refs)
    else:
        raise ValueError(f'Unsupported temporal mode: {mode}')
    return [{'id': f'w{i:04d}', 'target': [s.isoformat(), e.isoformat()],
             'references': [[a.isoformat(), b.isoformat()] for a, b in r]} for i, (s, e, r) in enumerate(pairs)]


def moving(t, start, end, refs, calendar_align=False):
    days, step = int(t['window_days']), int(t['step_days'])
    if days <= 0 or step <= 0:
        raise ValueError('window_days and step_days must be positive')
    pairs = []
    current = start
    while current + timedelta(days=days) <= end:
        stop = current + timedelta(days=days)
        aligned = []
        for s, e in refs:
            if calendar_align:
                # Explicit failure for unavailable Feb 29, never silently shift seasons.
                a = current.replace(year=s.year + current.year-start.year)
                inclusive = (stop-timedelta(days=1)).replace(year=s.year + (stop-timedelta(days=1)).year-start.year)
                b = inclusive + timedelta(days=1)
            else:
                a, b = s + (current-start), s + (stop-start)
            if not (s <= a < b <= e):
                raise ValueError('Aligned window outside reference period')
            aligned.append((a, b))
        pairs.append((current, stop, aligned))
        current += timedelta(days=step)
    if not pairs:
        raise ValueError('No complete temporal windows; partial windows are not emitted')
    return pairs
