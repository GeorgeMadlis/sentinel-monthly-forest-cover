"""Render overview maps (EPSG:3301) of ROIs with official layers. Usage: python -I render_map.py WORKS_DIR"""
import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import shape
from shapely.ops import transform, unary_union
from pyproj import Transformer
d = sys.argv[1]
tr = Transformer.from_crs(4326, 3301, always_xy=True).transform
rois = {f['properties']['id']: transform(tr, shape(f['geometry'])) for f in json.load(open(f'{d}/../../inputs/prior_rois.geojson'))['features']}
def load(p): return json.load(open(f'{d}/downloads/{p}'))['features']
def plotgeom(ax, g, **kw):
    gs = getattr(g, 'geoms', [g])
    for x in gs:
        if x.geom_type == 'Polygon':
            ax.fill(*x.exterior.xy, **kw)
        elif x.geom_type in ('LineString',):
            ax.plot(*x.xy, **{k: v for k, v in kw.items() if k in ('color', 'lw', 'alpha', 'zorder')})
        elif hasattr(x, 'geoms'):
            plotgeom(ax, x, **kw)
rb = unary_union([shape(f['geometry']) for f in load('plan/rb_planeeringutrass.json')])
par_rb = unary_union([shape(f['geometry']).buffer(0) for f in load('kataster/linear_parcels.json') if f['properties']['l_aadress'].startswith('Rapla-Pärnu raudtee')])
par_r4 = unary_union([shape(f['geometry']).buffer(0) for f in load('kataster/linear_parcels.json') if 'Pärnu-Ikla' in f['properties']['l_aadress'] and f['properties']['registr'][:4] in ('2025', '2026')])
rd = unary_union([shape(f['geometry']).buffer(0) for s in ('roi01', 'roi02') for f in load(f'metsaregister/teatis_{s}.json') if f['properties']['too_kood'] == 'RD'])
for name, (x0, y0, x1, y1) in {'map_roi01': (534300, 6475900, 548000, 6490000), 'map_roi02': (528200, 6485300, 533000, 6494600)}.items():
    fig, ax = plt.subplots(figsize=(9, 9))
    plotgeom(ax, rb, color='#f2c94c', alpha=0.45, lw=0, label='RB 2018 corridor')
    plotgeom(ax, par_rb, color='#9b51e0', alpha=0.6, lw=0)
    plotgeom(ax, par_r4, color='#2d9cdb', alpha=0.6, lw=0)
    plotgeom(ax, rd, color='#eb5757', alpha=0.6, lw=0)
    for s in ('roi01', 'roi02'):
        for f in load(f'etak/e_501_tee_j_{s}.json'):
            p = f['properties']
            if p['tyyp_tekst'] in ('Põhimaantee', 'Tugimaantee', 'Kõrvalmaantee'):
                g = shape(f['geometry']); ax.plot(*g.xy, color='black' if p['tyyp_tekst'] != 'Kõrvalmaantee' else '#777', lw=1.6 if p['tyyp_tekst'] == 'Põhimaantee' else 0.8)
        for f in load(f'etak/e_502_roobastee_j_{s}.json'):
            g = shape(f['geometry']); ax.plot(*g.xy, color='#333', lw=1.2, ls='--')
    for rid, g in rois.items():
        plotgeom(ax, g, color='#27ae60', alpha=0.55, lw=0)
        c = g.representative_point(); ax.annotate(rid, (c.x, c.y), fontsize=8, color='#1e7d45')
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
    ax.set_title(f'{name}: green=ROI, yellow=RB 2018 county-plan corridor, purple=“Rapla-Pärnu raudtee” parcels,\nblue=road-4 parcels registered 2025-26, red=RD (raadamine) forest notices; black=national roads, dashed=ETAK rail', fontsize=8)
    ax.tick_params(labelsize=7); ax.set_xlabel('EPSG:3301 X (m)', fontsize=7); ax.set_ylabel('EPSG:3301 Y (m)', fontsize=7)
    fig.text(0.01, 0.01, 'Data: Maa- ja Ruumiamet ETAK, cadastre, planning WFS; Keskkonnaagentuur Metsaregister (gsavalik.envir.ee), retrieved 2026-10-24. Derived figure.', fontsize=6)
    fig.savefig(f'{d}/images/{name}.png', dpi=130, bbox_inches='tight'); plt.close(fig)
print('ok')
