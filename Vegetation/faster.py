from glob import glob
from inference_trt import get_class, Model
import cv2
from time import time
from torch.utils.data import Dataset, DataLoader
from timm.data.transforms_factory import create_transform
import torch
from PIL import Image
from tqdm import tqdm


transform = create_transform(input_size=(3, 448, 448), interpolation='bicubic', mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225), crop_pct=None)


class ImagesDataset(Dataset):
    """Face Landmarks dataset."""

    def __init__(self, root_dir, transform=None):
        """
        Arguments:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        
        self.root_dir = root_dir
        self.images = glob(root_dir + '/*.jpg')[:1000]
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        image = cv2.imread(self.images[idx])

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        image = Image.fromarray(image)

        if self.transform:
            image = self.transform(image)

        return image


def get_class(image, model, version=0):

    results = model(image, version)

    return results

if __name__ == '__main__':

    batch_size = 20
    input_dir = 'windows_share/cuiaba_sorriso_norte/Panoramic'

    images_dataset = ImagesDataset(input_dir, transform)

    dataloader = DataLoader(images_dataset, batch_size=batch_size,
                            shuffle=True, num_workers=20)

    model = Model()

    start = time()

    for i, sample in (enumerate(dataloader)):
        #print(i, sample.shape)
        images_batch = sample

        predictions = [get_class(image, model) for image in images_batch]

    tempo = time() - start
    print(f'classificar as imagens demorou {tempo} segundos')
    tempo_por_imagem = tempo / (len(dataloader) * batch_size)
    print(f'fps = {1.0/tempo_por_imagem} s')
    print(f'quantidade de imagens = {len(dataloader)*batch_size}')
