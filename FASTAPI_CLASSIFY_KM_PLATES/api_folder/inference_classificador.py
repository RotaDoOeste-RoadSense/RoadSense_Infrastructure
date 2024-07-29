import cv2
from timm.data.transforms_factory import create_transform
from timm.models import create_model
import torch
from PIL import Image
import numpy as np

def load_classifier(folder_path, num_classes=2, model_arc='resnet50'):
    device = torch.device('cuda')
    model = create_model(
            model_arc,
            num_classes=num_classes,
            in_chans=3,
            pretrained=False,
            checkpoint_path=folder_path,
        )
    model = model.to(device)
    model.eval()
    return model
transform_2 = create_transform(input_size=(3, 224, 224), interpolation='bicubic', mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225), crop_pct=None)
model = load_classifier('model_best.pth.tar')
def inference(my_image):
    my_image = np.array(my_image)
    if my_image.shape[2] == 3:  # Se for uma imagem colorida
        img_rgb = cv2.cvtColor(my_image, cv2.COLOR_BGR2RGB)
    else:
        img_rgb = my_image
    pil_image = Image.fromarray(img_rgb)
    img = transform_2(pil_image).unsqueeze(0)
    img = img.to('cuda')
    with torch.no_grad():
      outputs = model(img)
      outputs = outputs.softmax(-1)
      outputs = outputs.cpu().numpy()  
    outputs = np.argmax(outputs[0])
    return outputs