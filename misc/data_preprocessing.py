import os
import re
import warnings

import kaggle
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms


class CustomImageDataset(Dataset):
    def __init__(self, directory_path, transform=None):
        self.directory_path = directory_path
        self.transform = transform

        images, labels = [], []
        counter = 0
        for root, dirs, files in os.walk(directory_path):
            temp_list = [os.path.join(root, file) for file in files if file.endswith((".jpg", ".png"))]
            if len(temp_list) > 0:
                images.extend(temp_list)
                labels.extend([counter] * len(temp_list))
                counter += 1

        self.images = images

        num_classes = len(set(labels))
        one_hot = F.one_hot(torch.tensor(labels), num_classes=num_classes)
        self.labels = one_hot.float()

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        label = self.labels[idx]

        return image, label


def get_statistics(path):

    total_count = 0
    animals = os.listdir(path)
    for index, animal in enumerate(animals):
        base_path = f"./data/training_set/training_set/{animal}/"

        if not os.path.exists(base_path):
            print(f"Directory not found for {animal}: {base_path}")
            continue

        file_paths = os.listdir(base_path)
        image_paths = [file_path for file_path in file_paths if re.search(r"\.jpe?g$", file_path, re.IGNORECASE)]
        updated_image_paths = [base_path + image_path for image_path in image_paths]

        print(f"Number of {animal}:", len(updated_image_paths))
        total_count += len(updated_image_paths)
        storage = dict()

        for image_path in updated_image_paths:

            with Image.open(image_path) as image:

                width, height = image.size
                storage[(width, height)] = storage.get((width, height), 0) + 1

        sorted_by_values = sorted(storage.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"Most common {animal} image shapes:")

        for value in sorted_by_values:
            width, height, count = value[0][0], value[0][1], value[1]
            print(f"width: {width}, height: {height}, count: {count}")

        print("")
        if index == len(animals) - 1:
            print("Total Count:", total_count)


def download_data(path):
    if os.path.isdir(path):
        warnings.warn(
            "Directory already exists. Download skipped, but the code continues!",
            UserWarning,
        )
    else:
        kaggle.api.dataset_download_files("tongpython/cat-and-dog", path=path, unzip=True)
        print("Data downloaded and unzipped to:", path)


def create_dataloaders():
    transform = transforms.Compose(
        [
            transforms.Resize((512, 512), interpolation=Image.LANCZOS),
            transforms.ToTensor(),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=45),
        ]
    )

    train_directory_path = "./data/training_set/training_set/"
    test_directory_path = "./data/test_set/test_set/"

    full_dataset = CustomImageDataset(directory_path=train_directory_path, transform=transform)
    test_dataset = CustomImageDataset(directory_path=test_directory_path, transform=None)

    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size

    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(dataset=train_dataset, batch_size=2, shuffle=True, num_workers=1)
    val_loader = DataLoader(dataset=val_dataset, batch_size=2, shuffle=True, num_workers=1)

    return train_loader, val_loader


def get_dataloader_example(data_loader):
    for images, labels in data_loader:
        print("Images Shape:", images.shape)
        print("Labels Shape:", labels.shape)

        image = images[0].permute(1, 2, 0).numpy()
        label = labels[0]

        print("Example Image:")
        plt.imshow(image)
        plt.axis("off")
        plt.show()
        print("Image Class:", label)
        break
