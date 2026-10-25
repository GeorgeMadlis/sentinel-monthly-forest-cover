"""List orthophoto files (with flight dates in filenames) per 1:10000 sheet from the Maa- ja Ruumiamet geoportaal download search (page 610). Saves raw HTML + summary JSON."""
import sys,re,json,hashlib,datetime,urllib.request,pathlib
out=pathlib.Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
summary=[]
for sheet in sys.argv[2:]:
    for typ in ['ortofoto_eesti_rgb','ortofoto_eesti_ngr']:
        u=f'https://geoportaal.maaamet.ee/index.php?lang_id=1&plugin_act=otsing&page_id=610&kaardiruut={sheet}&andmetyyp={typ}'
        ts=datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
        b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'geo-01-research/1.0'}),timeout=60).read()
        f=out/f'sheet_{sheet}_{typ}.html'; f.write_bytes(b)
        names=sorted(set(re.findall(r'(\d+_OF_\w+?_GeoTIFF_[\d_\-]+)\.zip',b.decode('utf-8','replace'))),reverse=True)
        dates=[n.split('GeoTIFF_')[1] for n in names]
        summary.append({'sheet':sheet,'type':typ,'url':u,'retrieved_utc':ts,'sha256':hashlib.sha256(b).hexdigest(),'file':str(f),'geotiff_flight_dates':dates})
        print(sheet,typ,dates[:5])
json.dump(summary,open(out/'sheet_dates_summary.json','w'),indent=1)
