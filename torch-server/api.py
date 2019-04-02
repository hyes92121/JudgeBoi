import io
import os 
import time 
import numpy as np 
from PIL import Image

import torch
import torchvision
import torchvision.transforms as tf
from torch.utils.data import Dataset, DataLoader


class TargetDataset(Dataset):
    def __init__(self, labels):
        self.imgs = []
        self.label = []

        for i in os.listdir('images'):
            self.imgs.append(np.array(Image.open(f'images/{i}')))
        with open(labels, 'r') as f:
            for l in f:
                self.label.append(float(l))

    def __len__(self):
        return len(self.label)

    def __getitem__(self, idx):
        return self.imgs[idx], self.label[idx]


class SourceDataset(Dataset):
    def __init__(self):
        self.data = []
        self.transform = tf.Compose([tf.ToTensor(), tf.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])])
    
    def load(self, manifest):
        for p in manifest:
            img = Image.open(p)
            self.data.append(np.array(img))
    
    def get_raw(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.transform(self.data[idx])

    def cleanup(self):
        self.data = []


def get_model_api():
    s1 = time.time()
    model = torchvision.models.resnet50(pretrained=True)
    e1 = time.time()
    print(f'Time loading model: {e1-s1:.4f}')

    s1 = time.time()
    model.eval()
    e1 = time.time()
    print(f'Time setting model to eval: {e1-s1:.4f}')
    
    s1 = time.time()
    model.cuda()
    e1 = time.time()
    print(f'Time moving model to cuda: {e1-s1:.4f}')

    dataset = SourceDataset()
    s1 = time.time()
    target_set = TargetDataset('label.csv')
    e1 = time.time()
    print(f'Building target dataset: {e1-s1:.4f}')

    s1 = time.time()
    dataloader = DataLoader(target_set, batch_size=200, shuffle=False, num_workers=0)
    e1 = time.time()
    print(f'Loading into dataloader: {e1-s1:.4f}')

    s1 = time.time()
    for batch in dataloader:
        imgs_gt, labels_gt = batch
        imgs_gt = np.array(imgs_gt)
        labels_gt = np.array(labels_gt)
    e1 = time.time()
    print(f'Time loading one batch: {e1-s1:.4f}')
    
    def model_api(d):
        #ss = time.time()
       
        #s1 = time.time()
        dataset.load(d)
        #e1 = time.time()
        #print(f'Time loading data: {e1-s1:.4}')
       
        #s1 = time.time()
        raw_source = dataset.get_raw()
        raw_source = np.array(raw_source)
        #e1 = time.time()
        #print(f'Time getting raw: {e1-s1:.4}')

        dataloader = DataLoader(dataset, batch_size=8, shuffle=False, num_workers=0)
        
        #s1 = time.time()
        label = np.array([])
        
        for batch in dataloader:
            imgs = batch
        
            #s1 = time.time()
            imgs = imgs.cuda()
            #e1 = time.time()
            #print(f'Time moving to cuda: {e1-s1:.4}')
        
            #s1 = time.time()
            output = model(imgs)
            #e1 = time.time()
            #print(f'Time infering: {e1-s1:.4}')

            output = np.array(torch.max(output, 1)[1].tolist())
            label = np.concatenate((label, output), axis=0)
        #e1 = time.time()
        #print(f'Time inferencing: {e1-s1:.4}')
        
        #s1 = time.time()
        error = np.mean( [ np.max(imgs_gt[i].astype(np.float32) - raw_source[i].astype(np.float32)) for i in range(200)] )
        #e1 = time.time()
        #print(f'Time calculating error: {e1-s1:.4}')

        #s1 = time.time()
        acc = np.mean(label!=labels_gt)
        #e1 = time.time()
        #print(f'Time calculating acc: {e1-s1:.4}')

        # cleanup code
        dataset.cleanup()

        return acc, error
    
    return model_api
