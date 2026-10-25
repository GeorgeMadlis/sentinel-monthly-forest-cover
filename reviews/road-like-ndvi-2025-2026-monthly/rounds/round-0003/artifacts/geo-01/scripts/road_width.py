"""Estimate paved-carriageway width of the existing road beside ROI-02-S1 from horizontal brightness transects (0.6 m/px windows).
Bright, low-saturation pixels (min RGB >= thr) are counted as pavement; width corrected by road azimuth cos factor."""
import sys,math
from PIL import Image
import numpy as np
for f in sys.argv[1:]:
    a=np.asarray(Image.open(f).convert('RGB')).astype(int)
    res=[];cents=[]
    for row in range(150,651,50):
        r=a[row,550:950]; mn=r.min(axis=1); sat=r.max(axis=1)-mn
        thr=max(150,np.percentile(mn,97)-25)
        m=(mn>=thr)&(sat<45)
        # longest run
        best=(0,0);s=None
        for i,v in enumerate(list(m)+[False]):
            if v and s is None: s=i
            if not v and s is not None:
                if i-s>best[1]-best[0]: best=(s,i)
                s=None
        res.append(best[1]-best[0]); cents.append(550+(best[0]+best[1])/2)
    # azimuth from centre drift
    dx=np.polyfit(range(150,651,50),cents,1)[0]; ang=math.atan(dx)
    w=np.median(res)*0.6*math.cos(ang)
    print(f.split('/')[-1],'run_px',res,'slope dx/dy=%.2f'%dx,'median_width_m=%.1f'%w)
