from glob import glob
#from inference_trt import get_class
import cv2
from time import time
from torch.utils.data import Dataset, DataLoader
from timm.data.transforms_factory import create_transform


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
        self.images = glob(root_dir + '/*.jpg')
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        image = cv2.imread(self.images[idx])

        if self.transform:
            sample = self.transform(sample)

        return sample

input_dir = 'windows_share/cuiaba_sorriso_norte/Panoramic'


images = glob(input_dir + '/*.jpg')[:100]


start = time()
for image in images:
    img = cv2.imread(image)

tempo = time() - start
print(f'ler as imagens demorou {tempo} segundos')