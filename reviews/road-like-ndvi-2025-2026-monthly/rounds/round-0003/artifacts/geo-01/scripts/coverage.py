"""Report fraction of non-empty (non-transparent / non-white) pixels in a PNG."""
import sys
from PIL import Image
import numpy as np
for f in sys.argv[1:]:
    im=Image.open(f); a=np.asarray(im.convert('RGBA')).astype(int)
    alpha=a[...,3]>0; white=(a[...,:3].min(axis=2)>=250)
    valid=alpha & ~white
    print(f, im.size, im.mode, 'valid_frac=%.3f'%valid.mean(), 'mean_rgb', a[...,:3][valid].mean(axis=0).round(1) if valid.any() else None)
