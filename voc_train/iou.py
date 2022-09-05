'''
referenced from
https://stackoverflow.com/a/48383182
'''

# IoU function
def iou(pred, target, n_classes = 4):
  ious = []
  pred = pred.view(-1)
  target = target.view(-1)

  # Ignore IoU for background class ("0")
  for cls in range(1, n_classes):  # This goes from 1:n_classes-1 -> class "0" is ignored
    pred_inds = pred == cls
    target_inds = target == cls
    
    intersection = int((pred_inds * target_inds).sum().item())
    union = int((pred_inds + target_inds).sum().item())
    
    # print(intersection, union) # for test
    
    if int(target_inds.sum().item()) == 0 and int(pred_inds.sum().item()) == 0:
      continue
    
    if union == 0:
      ious.append(float('nan'))  # If there is no ground truth, do not include in evaluation
    else:
      ious.append(float(intersection) / float(union)) # float(max(union, 1)))
    
  return np.array(ious), np.array(ious).mean()


  # for test data
  with open(os.path.join(ROOT_DIR, "VOCdevkit/VOC2012/ImageSets/Segmentation/val.txt"), 'r') as f:
    lines = f.readlines()
  for i in range(len(lines)):
    lines[i] =  lines[i].strip('\n')

  iter = 0
  iou_stack = 0

  for idx in range(len(lines)):
    test_jpg_path = lines[idx] + '.jpg'
    test_png_path = lines[idx] + '.png'
    test_image = PIL.Image.open(os.path.join(ROOT_DIR, 'VOCdevkit/VOC2012', "JPEGImages", test_jpg_path))
    test_gt_image = PIL.Image.open(os.path.join(ROOT_DIR, 'VOCdevkit/VOC2012', "SegmentationObject", test_png_path))

    # test image transform & input to test model
    test_image = np.array(test_image)
    test_image = torch.from_numpy(test_image).to(torch.float).permute(2,0,1).to(device)
    ori_x, ori_y = test_image.shape[1], test_image.shape[2]
    test_image = torch.unsqueeze(test_image, dim=0)

    test_transform = transforms.Compose([
        transforms.Normalize(mean=(0, 0, 0), std=(255., 255., 255.)),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
    ])
    # return_transform = transforms.Compose([
    #     transforms.Resize((ori_x, ori_y), interpolation=InterpolationMode.BILINEAR),
    # ])

    test_seg = test_model(test_transform(test_image))
    # test_seg = return_transform(test_seg)
    # test_seg[test_seg <= 8] = 0 # Thresholdings
    test_seg = torch.squeeze(test_seg, dim=0)

    # model prediction
    test_image_channel_idx = torch.argmax(test_seg, dim=0).cpu()

    # ground truth image getting
    test_gt_image = np.array(test_gt_image)
    test_gt_image = torch.from_numpy(test_gt_image).to(torch.int)

    iter += 1
    _, metric = iou(test_image_channel_idx, test_gt_image, 21)
    print("iou of %d th " % (iter), " : ", metric)
    iou_stack += metric

  mean_iou = iou_stack / iter
  print("mean_iou : ", mean_iou)