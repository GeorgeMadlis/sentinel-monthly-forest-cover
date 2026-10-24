"""Scientific contact sheet; display existing reproduced masks without changing them."""
from pathlib import Path
from PIL import Image,ImageDraw

out=Path(__file__).resolve().parents[1]
methods=['fixed','fixed_and_radar','sigma','sigma_and_radar']
sheet=Image.new('RGB',(1600,1100),'white');draw=ImageDraw.Draw(sheet)
for row,rid in enumerate(['ROI-01','ROI-02','CONTROL-01','CONTROL-02']):
    for col,method in enumerate(methods):
        im=Image.open(out/'inspect/crops'/f'{rid}-{method}.png').convert('RGB')
        if rid.startswith('CONTROL'):
            im=im.resize((216,216),Image.Resampling.NEAREST)
        else:
            im.thumbnail((388,220))
        x=col*400;y=row*275
        draw.text((x+5,y+6),rid+' '+method,fill='black');sheet.paste(im,(x+5,y+28))
        if rid.startswith('CONTROL'):draw.text((x+5,y+250),'20 m source pixels enlarged for display',fill='black')
sheet.save(out/'inspect/mask_contact_sheet.png')
print('Mask contact sheet: four existing rules, four unchanged sampling regions')
