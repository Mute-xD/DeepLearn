import torch
import torch.nn as nn
import torch.optim as optim
import tensorboardX
import torchvision.transforms as transforms
import torchvision.datasets as datasets
import torch.utils.data as u_data
import torch.backends.cudnn as cudnn


class MNIST:
    def __init__(self):
        self.writer = self.setWriter()
        self.batchSize = 64
        self.trainSetSize, self.testSetSize = None, None
        cudnn.benchmark = True
        print(cudnn.is_available())

    def build(self):
        trainPipe, testPipe = self.loadDataset()
        model = MNISTModel()
        model = model.cuda()
        ceLoss = nn.CrossEntropyLoss().cuda()  # 适合分类任务
        opt = optim.Adam(model.parameters(), lr=1e-3, weight_decay=0.0002)  # weightDecay l2正则化
        for epochs in range(1, 21):
            print('epochs: ', epochs)
            self.train(trainPipe, model, ceLoss, opt)
            self.test(testPipe, trainPipe, model)

    @staticmethod
    def train(trainPipe, model, ceLoss, opt):
        model.train()
        for i, data in enumerate(trainPipe):
            inputs, labels = data
            out = model(inputs.cuda(non_blocking=True))
            loss = ceLoss(out, labels.cuda(non_blocking=True))  # 两个参数shape一致

            opt.zero_grad()
            loss.backward()
            opt.step()

    def test(self, testPipe, trainPipe, model):
        model.eval()
        correct = 0

        for i, data in enumerate(trainPipe):
            inputs, labels = data
            out = model(inputs.cuda(non_blocking=True))
            _, predicted = torch.max(out, dim=1)  # maxVal, maxIndex
            predicted = predicted.cpu()
            for j in range(labels.shape[0]):
                if predicted[j].item() == labels[j].item():
                    correct += 1
        acc = correct / self.trainSetSize
        print('Train ACC: ', acc)
        correct = 0
        for i, data in enumerate(testPipe):
            inputs, labels = data
            out = model(inputs.cuda(non_blocking=True))
            _, predicted = torch.max(out, dim=1)  # maxVal, maxIndex
            predicted = predicted.cpu()
            for j in range(labels.shape[0]):
                if predicted[j].item() == labels[j].item():
                    correct += 1
        acc = correct / self.testSetSize
        print('Test ACC: ', acc)

    def loadDataset(self):
        trainSet = datasets.MNIST('./mnist', train=True, transform=transforms.ToTensor(), download=False)
        testSet = datasets.MNIST('./mnist', train=False, transform=transforms.ToTensor(), download=False)
        self.trainSetSize = len(trainSet)
        self.testSetSize = len(testSet)
        trainPipe = u_data.DataLoader(dataset=trainSet, batch_size=self.batchSize, shuffle=True,
                                      num_workers=4, pin_memory=True)
        testPipe = u_data.DataLoader(dataset=testSet, batch_size=self.batchSize, shuffle=True,
                                     num_workers=4, pin_memory=True)
        return trainPipe, testPipe

    @staticmethod
    def setWriter():
        return tensorboardX.SummaryWriter(comment='_mnist')


class MNISTModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Sequential(nn.Linear(784, 500), nn.Tanh())
        self.layer2 = nn.Sequential(nn.Linear(500, 300), nn.Tanh())
        self.layer3 = nn.Sequential(nn.Linear(300, 10), nn.Softmax(dim=1))  # 目标维度 此处为(64, 10)

    def forward(self, x):
        x.cuda(non_blocking=True)
        x = x.view(x.size()[0], -1)  # (64, 1, 28, 28) -> (64, 784)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        return x


if __name__ == '__main__':
    mnist = MNIST()
    mnist.build()
