
import pickle as pkl
import numpy as np
import os
import shutil

filepath = 'filenames_para_direita.pkl'

with open(filepath, 'rb') as f:

    data = pkl.load(f)

n_samples = 1000

direita = data['direita']

id = 1

outdir = f'task_pa_direita_{id}'
os.makedirs(outdir, exist_ok=True)

if not os.path.exists('used.npy'):

    used = []

else:

    used = np.load('used.npy')
    used = list(used)

folder = "/mnt/teste2/Viagem3/"

for classe in direita:
    print(classe)

    images_list = direita[classe]

    np.random.shuffle(images_list)

    count = 0
    index = 0
    while count < n_samples and index <= len(images_list):
        filename = images_list[index]

        if index % 10 == 0:
            print(f'processando classe = {classe}, index = {index}')

        if filename not in used:
            image_path = folder + '/Cube/' + filename
            #subdir = outdir + '/' + classe
            #os.makedirs(subdir, exist_ok=True)
            save_path = outdir + '/' + filename
            shutil.copy(image_path, save_path)
            count += 1
            used.append(filename)
        index += 1


used = np.array(used)
np.save('used.npy', used)


        







