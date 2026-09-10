import sys
from PIL import Image
d=sys.argv[1]; out=sys.argv[2]
names=['C1_start_corridor','C2_start_lookdown','C3_offpath_trunks','C4_path_ahead','C5_fugaku_approach','C6_arbitrary_east']
ims=[Image.open(f'{d}/{n}.png').resize((640,400)) for n in names]
sheet=Image.new('RGB',(1280,1200))
for k,im in enumerate(ims): sheet.paste(im,((k%2)*640,(k//2)*400))
sheet.save(out,quality=88); print(out)
