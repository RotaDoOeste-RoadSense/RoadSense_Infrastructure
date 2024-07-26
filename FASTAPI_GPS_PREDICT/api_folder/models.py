import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
list_to_tensor = lambda x: torch.tensor(x, dtype=torch.double)
class SmallNN(nn.Module):
    def __init__(self):
        super(SmallNN, self).__init__()
        self.fc1 = nn.Linear(4, 4)
        self.fc2 = nn.Linear(4, 3)
        self.fc3 = nn.Linear(3, 2)
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x
class ComplexNN(nn.Module):
    def __init__(self):
        super(ComplexNN, self).__init__()
        self.fc1 = nn.Linear(4, 32)
        self.fc2 = nn.Linear(32, 64)
        self.fc21 = nn.Linear(64, 128)
        self.fc22 = nn.Linear(128, 512)
        self.fc25 = nn.Linear(512,128)
        self.fc26 = nn.Linear(128,64)
        self.fc3 = nn.Linear(64, 32)
        self.fc4 = nn.Linear(32, 2)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc21(x))
        x = self.dropout(x)
        x = torch.relu(self.fc22(x))
        x = torch.relu(self.fc25(x))
        x = torch.relu(self.fc26(x))
        x = torch.relu(self.fc3(x))
        x = self.fc4(x)
        return x

class ModelManager:
    def __init__(self, model):
        self.model = model
        self.model.double()
        model.to(torch.device('cuda:0'))
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(model.parameters(), lr=0.0005)
        self.best_loss = float('inf')

    def train(self, train_loader, val_loader, epochs):
        for epoch in range(epochs):
            self.model.train()
            for inputs, targets in train_loader:
                self.optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)
                loss.backward()
                self.optimizer.step()
            print(f'Epoch {epoch+1}/{epochs}, Training Loss: {loss.item()}')
            val_loss = self.validate(val_loader)
            if val_loss < self.best_loss:
                self.best_loss = val_loss
                self.save_model("best.pt")
            self.save_model("last.pt")

    def validate(self, val_loader):
        self.model.eval()
        total_loss = 0
        with torch.no_grad():
            for inputs, targets in val_loader:
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)
                total_loss += loss.item()
        average_loss = total_loss / len(val_loader)
        print(f'Validation Loss: {average_loss}')
        return average_loss

    def predict(self, input_data):
        self.model.eval()
        input_tensor = torch.tensor([input_data], dtype=torch.double)
        input_tensor = input_tensor.to(torch.device('cuda:0'))
        with torch.no_grad():
            output = self.model(input_tensor)
        output = output.to('cpu')
        return output.numpy().tolist()
    
    def save_model(self, path):
        scripted_model = torch.jit.script(self.model)
        scripted_model.save(path)

    def load_model(self, path):
        self.model = torch.jit.load(path)
        self.model.eval()


if __name__=='__main__':
    model = ComplexNN()
    manager = ModelManager(model)
    manager.load_model('best.pt')
    # .predict(_input)
    