import cv2
import matplotlib.pyplot as plt
import os
from model import Model
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import cv2
from skimage.metrics import structural_similarity as ssim
from time import time


def compute_ms_ssim(img1, img2):
    # Converte para escala de cinza se necessário
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    if img1.shape != img2.shape:
        min_shape = min(img1.shape[0], img2.shape[0])

        img1 = cv2.resize(img1, (min_shape, min_shape), cv2.INTER_AREA)
        img2 = cv2.resize(img2, (min_shape, min_shape), cv2.INTER_AREA)
    
    # Calcula MS-SSIM
    score, _ = ssim(img1, img2, full=True, multichannel=False)
    return score


def get_similarities(patches):
    shapes = []
    similaridades = []
    for i in range(len(patches)):
        similaridade = None
        if i < len(patches) - 1:

            #similaridade = compute_ms_ssim(patches[i], patches[i+1])
            similaridade = compute_ms_ssim(patches[i], (patches[i+1]))

        if i > 0:
            #similaridade_anterior = compute_ms_ssim(patches[i], patches[i-1])
            similaridade_anterior = compute_ms_ssim(patches[i], patches[i-1])
            if similaridade is not None:
                similaridade = (similaridade + similaridade_anterior) / 2
            else:
                similaridade = similaridade_anterior
        shapes.append(patches[i].shape[0])
        if similaridade is not None:
            similaridades.append(similaridade)

    min_shape = min(shapes)

    cx , cy = min_shape // 2, min_shape // 2

    new_patches = [cv2.resize(y, (min_shape, min_shape)) for y in patches]

    for element, distance in zip(new_patches, similaridades):
        if 0 <= distance <= 0.33:
            color = (0, 0, 255)
        elif 0.33 < distance <= 0.66:
            color = (0,255,255) 
        elif distance > 0.66:
            color = (0, 255, 0)
        cv2.putText(element, f'{distance:.2f}', (cx, cy), 2, 1 , color)

    image = cv2.hconcat(new_patches)
    #cv2.imwrite(f'{outdir}/{filename}.png', image)
    if len(similaridades) > 0:
        return {'min' : np.min(similaridades), 'avg': np.mean(similaridades), 'std': np.std(similaridades), 'similaridades' : similaridades}
    else:
        return {'min' : -1, 'avg' : -1, 'std' : -1, 'similaridades': []}

def extrair_crops_quadrados(crop):
    h_crop, w_crop = crop.shape[:2]
    patches = []
    boxes = []
    # Define o tamanho do quadrado como o lado menor da área
    if w_crop >= h_crop:
        square_size = h_crop
        num_crops = w_crop // square_size  # quantos quadrados cabem horizontalmente
        for i in range(num_crops):
            x_start = i * square_size
            x_end = x_start + square_size
            patch = crop[0:h_crop, x_start:x_end]
            patches.append(patch)
            boxes.append([x_start, 0, x_end, h_crop])
    else:
        square_size = w_crop
        num_crops = h_crop // square_size  # quantos quadrados cabem verticalmente
        for i in range(num_crops):
            y_start = i * square_size
            y_end = y_start + square_size
            patch = crop[y_start:y_end, 0:w_crop]
            patches.append(patch)
            boxes.append([0, y_start, w_crop, y_end])
    return patches, boxes

def crop_image(image, box):
    return image[box[1]:box[3], box[0]:box[2], :]

def corta(img, cx, cy, size=512):
    left = cx - size//2
    right = cx + size//2
    if left < 0:
        left = 0
    if left > img.shape[1]:
        right = img.shape[1]
    top = cy - size//2
    if top < 0:
        top = 0
    bottom = cy + size//2
    if bottom > img.shape[0]:
        bottom = img.shape[0]
    if len(img.shape) == 3:
        return img[top:bottom, left:right, :], (top, bottom, left, right)
    elif len(img.shape) == 2:
        return img[top:bottom, left:right], (top, bottom, left, right)

def custom_round(valor):
    return int(valor + 0.5)

model = Model()

def check_point_in_box(box, point):
    px, py = point
    if box[0] < px < box[2]:
        if box[1] < py < box[3]:
            return True
    return False

def predict_old(image, box):
    #image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    box_length = box[2] - box[0]
    box_height = box[3] - box[1]
    if box_length == 0 or box_height == 0:
        raise ValueError("Invalid Box")
    size = 256
    div = box_length / size
    div = custom_round(div)
    x1, y1, x2, y2 = box
    img_h, img_w = image.shape[:2]
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(img_w, x2)
    y2 = min(img_h, y2)
    patches = []
    x2_aux = x2
    k = 0
    erros = []
    if div > 1:
        for k in range(div):
            x2 = (k+1) * size
            cx, cy = (x2 + x1) // 2, (y1 + y2) // 2
            crop, (top, bottom, left, right) = corta(image, cx, cy, size)
            if crop.shape[:2] == (256, 256):
                
                #outlier, map_combined, position = model(crop)
                outlier = model(crop)
                crop = cv2.resize(crop, (64, 64))
                map_combined = outlier['feature'][:, : ,np.argmax(outlier['scores'])]
                position = outlier['positions'][np.argmax(outlier['scores'])]
                erros.append(outlier['score'])
                position_check = position[0] + left , position[1] + top
                location_check = check_point_in_box(box, position_check)
                if outlier['is_outlier'] and location_check:
                    print(k, outlier, position, position_check, location_check)
                    cv2.circle(crop, position, 2, (255, 0, 0), 2)
                    patches.append(True)
                    # fig, axes = plt.subplots(1, 2, figsize=(12, 9))
                    # imagem_inicial = axes[0].imshow(crop, cmap='jet')
                    # axes[0].set_title('Imagem Inicial')
                    # axes[0].axis('off')
                    # orig_image = axes[1].imshow(map_combined, cmap='jet')
                    # axes[1].set_title('Imagem Original')
                    # axes[1].axis('off')
                    # plt.show()
            x1 = x2
    is_outlier = bool(np.any(patches))
    if len(erros) == 0:
        return {'is_outlier' : is_outlier  ,'score' : -1}
    return {'is_outlier' : is_outlier ,'score' : float(np.max(erros))}


def predict(image, box):
    start = time()
    box_length = box[2] - box[0]
    box_height = box[3] - box[1]
    if box_length == 0 or box_height == 0:
        raise ValueError("Invalid Box")
    crop_orig = image[box[1] : box[3], box[0] : box[2], :]
    patches, boxes = extrair_crops_quadrados(crop_orig)    
    erros = [] 
    results = []   

    for crop in patches:
        outlier = model(crop)
        erros.append(outlier['score'])
        if outlier['is_outlier'] :
            results.append(True)

    is_outlier = bool(np.any(results))
    
    if len(erros) == 0:
        return {'is_outlier' : is_outlier  ,'score' : -1}
    return {'is_outlier' : is_outlier ,'score' : float(np.max(erros))}


def predict_crop(image):
    patches, boxes = extrair_crops_quadrados(image)    
    erros = [] 
    results = []   
    
    for crop in patches:
        outlier = model(crop)
        erros.append(outlier['score'])

        if outlier['is_outlier'] :
            results.append(True)
      
    is_outlier = bool(np.any(results))
  
    if len(erros) == 0:
        return {'is_outlier' : is_outlier  ,'score' : -1}
    return {'is_outlier' : is_outlier ,'score' : float(np.max(erros))}


def predict_crop_similarities(image):
    patches, boxes = extrair_crops_quadrados(image)    
    erros = [] 
    results = []   
    outlier = get_similarities(patches)

    erros = outlier['similaridades']

    is_outlier = outlier['avg'] < 0.80

    is_outlier = bool(is_outlier)

    if len(erros) == 0:
        return {'is_outlier' : is_outlier  ,'score' : -1}
    return {'is_outlier' : is_outlier ,'score' : float(outlier['avg']), 'similaridades' : outlier['similaridades']}

