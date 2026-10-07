from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=Path(__file__).parent;j=json.loads((R/'roi_metrics.json').read_text());fig,axes=plt.subplots(1,3,figsize=(13,4))
for ax,key,label in zip(axes,['ndvi_change','vv_change','vh_change'],['NDVI target − reference mean','VV target − reference median (dB)','VH target − reference median (dB)']):
 for i,r in enumerate(j):
  values=[r[key+'_p10'],r[key+'_median'],r[key+'_p90']];ax.plot([values[0],values[2]],[i,i],color='steelblue');ax.scatter(values[1],i,color='navy',s=30)
 ax.set_yticks(range(len(j)),[r['roi_id'] for r in j]);ax.set_xlabel(label);ax.grid(axis='x',alpha=.25);ax.axvline(0,color='gray',lw=.7)
 if key=='vv_change':ax.axvline(-1.5,color='red',ls='--',label='VV gate');ax.legend()
 if key=='vh_change':ax.axvline(-1,color='red',ls='--',label='VH gate');ax.legend()
axes[0].set_title('Points: medians; bars: pixel p10–p90\nSpatial distributions, not confidence intervals',fontsize=10)
fig.suptitle('Continuous signals in provisional sampling buffers and visual controls');fig.tight_layout();fig.savefig(R/'continuous_signal_summary.png',dpi=160);fig.savefig(R/'continuous_signal_summary.pdf');plt.close(fig)
e=json.loads((R/'threshold_experiments.json').read_text())['settings'];fig,ax=plt.subplots(figsize=(10,4));x=np.arange(len(e));ax.plot(x,[v['optical']*.04 for v in e],'-o',label='robust optical');ax.plot(x,[v['and']*.04 for v in e],'-o',label='paired AND');ax.plot(x,[v['or']*.04 for v in e],'-o',label='paired OR');ax.set_xticks(x,[f"{v['k']}\n{v['delta_min']}\n{v['epsilon']}" for v in e],fontsize=8);ax.set_xlabel('Setting: k / minimum NDVI drop / noise floor');ax.set_ylabel('Candidate hectares, all land cover');ax.set_title('Prespecified sensitivity; stability comparison, no accuracy labels');ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(R/'threshold_sensitivity.png',dpi=160);fig.savefig(R/'threshold_sensitivity.pdf');plt.close(fig)
