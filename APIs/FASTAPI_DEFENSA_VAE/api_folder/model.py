from alibi_detect.utils.saving import save_detector, load_detector 
import numpy as np
import os

import tensorflow as tf
physical_devices = tf.config.list_physical_devices('GPU') 
tf.config.experimental.set_memory_growth(physical_devices[0], True)
from PIL import Image

class Model():

    def __init__(self, model_path='weights/patches_perspectiva_0.8.h5'):
        self.model = load_detector(model_path)

    def __preprocess__(self, image):
        image = tf.image.resize(image, (64, 64))
        image = tf.convert_to_tensor(image, dtype=tf.float32)
        image = image / 255.0
        image = tf.expand_dims(image, axis=0)
        return image
    
    def __call__(self, image, threshold=0.015):
        image = self.__preprocess__(image)
        output = self.model.predict(image) 
        score = output['data']['instance_score'][0]
        outlier = output['data']['is_outlier'][0] 
        feature = output['data']['feature_score'][0]
        results = {'scores' : [], 'positions' : [], 'medias' : []}
        for j in range(3):
            check_image = feature[:, :, j]
            y, x = np.unravel_index(np.argmax(check_image, axis=None), check_image.shape)
            results['scores'].append(np.max(check_image))
            results['positions'].append((x,y))
            results['medias'].append(np.mean(check_image))
        results['is_outlier'] = outlier > threshold
        results['score'] = score
        results['feature'] = feature
        return results
    

# model = Model()
# image_path = 'omni7_20220307_155200_14809959_Panoramic_010864_17614_124-5219_cam1.jpg' 
# image = Image.open(image_path)
# image = np.array(image)
# results = model(image)
# print(results)
# del model