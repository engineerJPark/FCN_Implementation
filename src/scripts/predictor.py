from scripts.fcn import FCN18
import torch
import cv2
import torchvision.transforms as transforms
from torchvision.transforms.functional import InterpolationMode
from matplotlib import cm
import numpy as np
import cv2
import math
import open3d as o3d

class predictor():
  def __init__(self, path):
    self.path = path
    self.device= 'cuda'
    self.model = FCN18(4).to(self.device)

    checkpoint = torch.load(self.path)
    self.model.load_state_dict(checkpoint['model_state_dict'])

    self.model.eval()
    print('model evaluation start')

  def predict_seg(self, image, depth):
    '''
    image : PIL format, gonna be numpy array
    '''

    # image_np = np.array(image)
    image_np = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).transpose(2,0,1)
    image_torch = torch.from_numpy(image_np).to(torch.float)

    image_torch = torch.unsqueeze(image_torch, dim=0)

    test_transform = transforms.Compose([
        transforms.Normalize(mean=(0, 0, 0), std=(255., 255., 255.)),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
    ])

    test_seg = self.model(test_transform(image_torch).to(self.device))
    test_seg = test_seg.cpu()

    test_image_channel_idx = torch.argmax(torch.squeeze(test_seg, dim=0), dim=0) # final prediction
    test_image_mask = np.uint8(cm.gnuplot2(test_image_channel_idx.detach().numpy()*70)*255)

    # get RGBDImage
    test_image_channel_idx_stack = np.stack(np.array([test_image_channel_idx.detach().numpy(),\
                                              test_image_channel_idx.detach().numpy(), \
                                                test_image_channel_idx.detach().numpy()]), \
                                                  axis=0)
    
    # segmentation data to RGBDImage
    image_np_class1 = np.copy(image_np)
    image_np_class1[test_image_channel_idx_stack != 1] = 0
    image_np_class1 = image_np_class1.transpose(1,2,0) # HWC to CHW
    depth_np_class1 = np.copy(depth)
    depth_np_class1[test_image_channel_idx.detach().numpy() != 1] = 0
    image_np_class1 = np.asarray(image_np_class1, order='C')
    depth_np_class1 = np.asarray(depth_np_class1, order='C')
    image_o3d_class1 = o3d.geometry.Image(image_np_class1)
    depth_o3d_class1 = o3d.geometry.Image(depth_np_class1)
    
    image_np_class2 = np.copy(image_np)
    image_np_class2[test_image_channel_idx_stack != 2] = 0
    image_np_class2 = image_np_class2.transpose(1,2,0) # HWC to CHW
    depth_np_class2 = np.copy(depth)
    depth_np_class2[test_image_channel_idx.detach().numpy() != 2] = 0
    image_np_class2 = np.asarray(image_np_class2, order='C')
    depth_np_class2 = np.asarray(depth_np_class2, order='C')
    image_o3d_class2 = o3d.geometry.Image(image_np_class2)
    depth_o3d_class2 = o3d.geometry.Image(depth_np_class2)

    image_np_class3 = np.copy(image_np)
    image_np_class3[test_image_channel_idx_stack != 3] = 0
    image_np_class3 = image_np_class3.transpose(1,2,0) # HWC to CHW
    depth_np_class3 = np.copy(depth)
    depth_np_class3[test_image_channel_idx.detach().numpy() != 3] = 0
    image_np_class3 = np.asarray(image_np_class3, order='C')
    depth_np_class3 = np.asarray(depth_np_class3, order='C')
    image_o3d_class3 = o3d.geometry.Image(image_np_class3)
    depth_o3d_class3 = o3d.geometry.Image(depth_np_class3)

    rgbd_image_class0 = o3d.geometry.RGBDImage()
    rgbd_image_class1 = o3d.geometry.RGBDImage()
    rgbd_image_class2 = o3d.geometry.RGBDImage()
    rgbd_image_class3 = o3d.geometry.RGBDImage()
    
    # argument is for open3d.geometry.Image. devide by depth_scale = 1000.
    rgbd_out_class1 = rgbd_image_class1.create_from_color_and_depth(image_o3d_class1, depth_o3d_class1, convert_rgb_to_intensity=False)
    rgbd_out_class3 = rgbd_image_class3.create_from_color_and_depth(image_o3d_class3, depth_o3d_class3, convert_rgb_to_intensity=False)
    rgbd_out_class2 = rgbd_image_class2.create_from_color_and_depth(image_o3d_class2, depth_o3d_class2, convert_rgb_to_intensity=False)

    return test_image_mask, (rgbd_out_class1, rgbd_out_class2, rgbd_out_class3)

class predict_coord(predictor):
  def __init__(self, path):
    super(predict_coord, self).__init__(path)

    # by cv2.calibrateCamera
    self.intrinsic = o3d.camera.PinholeCameraIntrinsic()
    self.intrinsic.intrinsic_matrix = np.array(
      [
        [623.31476768, 0., 269.87277202],
        [0., 613.62125703 ,237.91605748],
        [0., 0., 1.]
      ]
    )

    self.distortion = np.array([-0.07379347, 0.66942174, -0.00238366, -0.02229801, -1.27933461])

    r_mat = np.array([[ 0.0141245 , -0.99960032, -0.02448881],
                      [-0.59908249,  0.01114869, -0.80060969],
                      [ 0.80056272,  0.02597903, -0.59868558]])
    c_mat = np.array([[-0.30],
                      [0],
                      [0.38]])
    t_mat = -np.matmul(r_mat, c_mat)

    # extrinsic matrix define
    self.extrinsic_mat = np.concatenate((r_mat, t_mat), axis=1)
    self.extrinsic_mat = np.concatenate((self.extrinsic_mat, np.array([[0., 0., 0., 1.]])), axis=0)

    self.init_pointcloud = o3d.geometry.PointCloud()

  def get_pointcloud(self, rgbd_image):

    pcd = self.init_pointcloud.create_from_rgbd_image(rgbd_image, intrinsic=self.intrinsic, extrinsic=self.extrinsic_mat, project_valid_depth_only=True)
    pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) # flip
    
    # post-processing
    pcd = pcd.remove_non_finite_points()
    pcd, _ = pcd.remove_radius_outlier(nb_points=100, radius=0.01)
    
    return pcd
