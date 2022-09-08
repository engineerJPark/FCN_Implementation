'''
TODO
check whether iou, pix acc is not wrong to control the voc data.
'''

from train import train
from fcn import FCN18
from utils import label_accuracy_score

import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

if __name__ == '__main__': 
  if torch.cuda.is_available():
    device = torch.device('cuda')
    torch.cuda.manual_seed_all(1)
  else:
    device = torch.device('cpu')
    torch.manual_seed(1)
  print(torch.__version__, device)

  model = FCN18(21, device).to(device)
  past_epoch = 0

  # resume training
  PATH = 'voc_train/fcn_model/model_97_347_10'
  checkpoint = torch.load(PATH)
  model.load_state_dict(checkpoint['model_state_dict'])
  past_epoch = checkpoint['epoch']
  print("past_epoch : ", past_epoch)
  
  lr = 1e-4
  weight_decay = 1e-4
  momentum = 0.9
  
  optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentum, weight_decay=weight_decay)
  criterion = nn.CrossEntropyLoss(ignore_index=-1).to(device)
  # scheduler = optim.lr_scheduler.MultiStepLR(optimizer, milestones=[50,250], gamma=0.1)
  # scheduler = optim.lr_scheduler.MultiStepLR(optimizer, milestones=[250 - past_epoch], gamma=0.1)
  # scheduler = None

  # # train
  # loss_history= train(model, optimizer, criterion, scheduler, epochs = 100, \
  #                 device=device, verbose=False)
  # plt.plot(loss_history)
  # plt.show()
  # plt.savefig('voc_train/loss_history.jpg')
  # print(loss_history)

  # seg_plot(model, 0, device=device)
  # mean_iou(model, device=device, verbose=False)
  # mean_foreground_pixel_acc(model, device=device, verbose=False)
  acc, acc_cls, mean_iu, fwavacc = label_accuracy_score(model, 21, device=device, verbose=True)