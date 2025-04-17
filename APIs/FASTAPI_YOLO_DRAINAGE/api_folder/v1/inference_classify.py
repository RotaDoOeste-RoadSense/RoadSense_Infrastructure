from ultralytics import YOLO
import torchvision
import torchvision.transforms.functional as F
from torchvision.transforms import InterpolationMode

model = YOLO('v1/weights/best_classify.pt').cuda()
def drainage_classify(img):
    img_tensor = torchvision.transforms.ToTensor()(img).cuda().unsqueeze(0)
    img_resized = F.resize(img_tensor, size=(640, 640), interpolation=InterpolationMode.BILINEAR)
    p = model.predict(img_resized,verbose=False)[0]
    id = p.probs.top1
    conf = p.probs.top1conf
    if all([id==1,conf>0.6]):
        return {'result':'Ruim'}
    return {'result':'Bom'}
