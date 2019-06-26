# --------------------------------------------------------
# Tensorflow Faster R-CNN
# Licensed under The MIT License [see LICENSE for details]
# Written by Jiasen Lu, Jianwei Yang, based on code from Ross Girshick
# --------------------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import _init_paths
import os
import sys
import numpy as np
import argparse
import pprint
import pdb
import time
import cv2
import torch
from torch.autograd import Variable
from PIL import Image
from model.utils.config import cfg, cfg_from_file, cfg_from_list, get_output_dir
from model.fpn.cascade.detnet_backbone import detnet as detnet_cascade
from model.fpn.non_cascade.detnet_backbone import detnet as detnet_noncascade
from model.rpn.bbox_transform import clip_boxes
from torchvision.ops import nms
from model.rpn.bbox_transform import bbox_transform_inv
from model.utils.net_utils import save_net, load_net, vis_detections
from model.utils.blob import im_list_to_blob
import pdb

try:
    xrange  # Python 2
except NameError:
    xrange = range  # Python 3


def parse_args():
    """
    Parse input arguments
    """
    parser = argparse.ArgumentParser(description='Train a Fast R-CNN network')
    parser.add_argument('exp_name', type=str, default=None, help='experiment name')
    parser.add_argument('--dataset', dest='dataset',
                        help='training dataset',
                        default='pascal_voc', type=str)
    parser.add_argument('--cfg', dest='cfg_file',
                        help='optional config file',
                        default='cfgs/vgg16.yml', type=str)
    parser.add_argument('--net', dest='net',
                        help='detnet59, etc',
                        default='detnet59', type=str)
    parser.add_argument('--set', dest='set_cfgs',
                        help='set config keys', default=None,
                        nargs=argparse.REMAINDER)
    parser.add_argument('--load_dir', dest='load_dir',
                        help='directory to load models', default="weights")
    parser.add_argument('--image_dir', dest='image_dir',
                        help='directory to load images', default="demo_images/",
                        type=str)
    parser.add_argument('--result_dir', dest='result_dir', help='directory to save visual result', default="vis_results/",
                        type=str)
    parser.add_argument('--cuda', dest='cuda',
                        help='whether use CUDA',
                        action='store_true')
    parser.add_argument('--checksession', dest='checksession',
                        help='checksession to load model',
                        default=4, type=int)
    parser.add_argument('--checkepoch', dest='checkepoch',
                        help='checkepoch to load network',
                        default=6, type=int)
    parser.add_argument('--checkpoint', dest='checkpoint',
                        help='checkpoint to load network',
                        default=10000, type=int)
    parser.add_argument('--soft_nms', help='whether use soft nms', action='store_true')
    parser.add_argument('--cascade', help='whether use cascade', action='store_true')
    parser.add_argument('--cag', dest='class_agnostic',
                        help='whether perform class_agnostic bbox regression',
                        action='store_true')

    args = parser.parse_args()
    return args


lr = cfg.TRAIN.LEARNING_RATE
momentum = cfg.TRAIN.MOMENTUM
weight_decay = cfg.TRAIN.WEIGHT_DECAY


def _get_image_blob(im):
    """Converts an image into a network input.
    Arguments:
      im (ndarray): a color image in BGR order
    Returns:
      blob (ndarray): a data blob holding an image pyramid
      im_scale_factors (list): list of image scales (relative to im) used
        in the image pyramid
    """
    im_orig = im.astype(np.float32, copy=True)  # RGB
    im_orig /= 255.0
    im_orig -= cfg.PIXEL_MEANS
    im_orig /= cfg.PIXEL_STDS

    im_shape = im_orig.shape
    im_size_min = np.min(im_shape[0:2])
    im_size_max = np.max(im_shape[0:2])

    processed_ims = []
    im_scale_factors = []

    for target_size in cfg.TEST.SCALES:
        im_scale = float(target_size) / float(im_size_min)
        # Prevent the biggest axis from being more than MAX_SIZE
        if np.round(im_scale * im_size_max) > cfg.TEST.MAX_SIZE:
            im_scale = float(cfg.TEST.MAX_SIZE) / float(im_size_max)
        im = cv2.resize(im_orig, None, None, fx=im_scale, fy=im_scale,
                        interpolation=cv2.INTER_LINEAR)
        im_scale_factors.append(im_scale)
        processed_ims.append(im)

    # Create a blob to hold the input images
    blob = im_list_to_blob(processed_ims)

    return blob, np.array(im_scale_factors)


if __name__ == '__main__':

    args = parse_args()

    print('Called with args:')
    print(args)

    args.cfg_file = "cfgs/{}.yml".format(args.net)
    if args.cfg_file is not None:
        cfg_from_file(args.cfg_file)
    if args.set_cfgs is not None:
        cfg_from_list(args.set_cfgs)
    if not os.path.exists(args.result_dir):
        os.mkdir(args.result_dir)

    print('Using config:')
    pprint.pprint(cfg)
    np.random.seed(cfg.RNG_SEED)

    # train set
    # -- Note: Use validation set and disable the flipped to enable faster loading.

    if args.exp_name is not None:
        input_dir = args.load_dir + "/" + args.net + "/" + args.dataset + '/' + args.exp_name
    else:
        input_dir = args.load_dir + "/" + args.net + "/" + args.dataset
    if not os.path.exists(input_dir):
        raise Exception('There is no input directory for loading network from ' + input_dir)
    load_name = os.path.join(input_dir,
                             'fpn_{}_{}_{}.pth'.format(args.checksession, args.checkepoch, args.checkpoint))

    classes = np.asarray(['__background__',
                          'aeroplane', 'bicycle', 'bird', 'boat',
                          'bottle', 'bus', 'car', 'cat', 'chair',
                          'cow', 'diningtable', 'dog', 'horse',
                          'motorbike', 'person', 'pottedplant',
                          'sheep', 'sofa', 'train', 'tvmonitor'])

    if args.cascade:
        if args.net == 'detnet59':
            fpn = detnet_cascade(classes, 59, pretrained=False, class_agnostic=args.class_agnostic)
        else:
            print("network is not defined")
            pdb.set_trace()
    else:
        if args.net == 'detnet59':
            fpn = detnet_noncascade(classes, 59, pretrained=False, class_agnostic=args.class_agnostic)
        else:
            print("network is not defined")
            pdb.set_trace()

    fpn.create_architecture()

    checkpoint = torch.load(load_name)
    fpn.load_state_dict(checkpoint['model'])
    print('load model successfully!')

    # pdb.set_trace()

    print("load checkpoint %s" % (load_name))

    # initilize the tensor holder here.
    im_data = torch.FloatTensor(1)
    im_info = torch.FloatTensor(1)
    num_boxes = torch.LongTensor(1)
    gt_boxes = torch.FloatTensor(1)

    # ship to cuda
    if args.cuda:
        im_data = im_data.cuda()
        im_info = im_info.cuda()
        num_boxes = num_boxes.cuda()
        gt_boxes = gt_boxes.cuda()

    # make variable
    with torch.no_grad():
        im_data = Variable(im_data)
        im_info = Variable(im_info)
        num_boxes = Variable(num_boxes)
        gt_boxes = Variable(gt_boxes)

    if args.cuda:
        cfg.CUDA = True

    if args.cuda:
        fpn.cuda()

    fpn.eval()

    start = time.time()
    max_per_image = 100
    thresh = 0.05
    vis = True

    imglist = os.listdir(args.image_dir)
    num_images = len(imglist)

    print('Loaded Photo: {} images.'.format(num_images))

    for i in range(num_images):

        # Load the demo image
        im_file = os.path.join(args.image_dir, imglist[i])
        # im = cv2.imread(im_file)
        im = np.array(Image.open(im_file))
        if len(im.shape) == 2:
            im = im[:, :, np.newaxis]
            im = np.concatenate((im, im, im), axis=2)

        blobs, im_scales = _get_image_blob(im)
        assert len(im_scales) == 1, "Only single-image batch implemented"
        im_blob = blobs
        im_info_np = np.array([[im_blob.shape[1], im_blob.shape[2], im_scales[0]]], dtype=np.float32)

        im_data_pt = torch.from_numpy(im_blob)
        im_data_pt = im_data_pt.permute(0, 3, 1, 2)
        im_info_pt = torch.from_numpy(im_info_np)

        with torch.no_grad():
            im_data.resize_(im_data_pt.size()).copy_(im_data_pt)
            im_info.resize_(im_info_pt.size()).copy_(im_info_pt)
            gt_boxes.resize_(1, 1, 5).zero_()
            num_boxes.resize_(1).zero_()

        # pdb.set_trace()

        det_tic = time.time()
        # rois, cls_prob, bbox_pred, rpn_loss, rcnn_loss = \
        #     fpn(im_data, im_info, gt_boxes, num_boxes)
        with torch.no_grad():
            ret = fpn(im_data, im_info, gt_boxes, num_boxes)
            rois, cls_prob, bbox_pred = ret[0:3]

        scores = cls_prob.data
        boxes = (rois[:, :, 1:5] / im_scales[0]).data

        if cfg.TEST.BBOX_REG:
            # Apply bounding-box regression deltas
            box_deltas = bbox_pred.data
            if cfg.TRAIN.BBOX_NORMALIZE_TARGETS_PRECOMPUTED:
                # Optionally normalize targets by a precomputed mean and stdev
                box_deltas = box_deltas.view(-1, 4) * torch.FloatTensor(cfg.TRAIN.BBOX_NORMALIZE_STDS).cuda() \
                             + torch.FloatTensor(cfg.TRAIN.BBOX_NORMALIZE_MEANS).cuda()
                box_deltas = box_deltas.view(1, -1, 4)
            pred_boxes = bbox_transform_inv(boxes, box_deltas, 1)
            pred_boxes = clip_boxes(pred_boxes, im_info.data, 1)
        else:
            # Simply repeat the boxes, once for each class
            pred_boxes = np.tile(boxes, (1, scores.size[1]))

        scores = scores.squeeze()
        pred_boxes = pred_boxes.squeeze()
        # _t['im_detect'].tic()
        det_toc = time.time()
        detect_time = det_toc - det_tic

        misc_tic = time.time()

        if vis:
            im2show = np.copy(im[:, :, ::-1])

        for j in xrange(1, len(classes)):
            inds = torch.nonzero(scores[:, j] > thresh).view(-1)
            if inds.numel() > 0:
                cls_scores = scores[:, j][inds]
                _, order = torch.sort(cls_scores, 0, True)
                if args.class_agnostic:
                    cls_boxes = pred_boxes[inds, :]
                else:
                    cls_boxes = pred_boxes[inds][:, j * 4:(j + 1) * 4]

                cls_dets = torch.cat((cls_boxes, cls_scores.unsqueeze(1)), 1)
                cls_dets = cls_dets[order]

                # if args.soft_nms:
                #     np_dets = cls_dets.cpu().numpy().astype(np.float32)
                #     keep = soft_nms(np_dets, method=cfg.TEST.SOFT_NMS_METHOD)  # np_dets will be changed
                #     keep = torch.from_numpy(keep).type_as(cls_dets).int()
                #     cls_dets = torch.from_numpy(np_dets).type_as(cls_dets)
                # else:
                keep = nms(cls_dets, cfg.TEST.NMS)
                cls_dets = cls_dets[keep.view(-1).long()]
                cls_dets = cls_dets.cpu().numpy()
            else:
                cls_dets = np.array([])

            if vis:
                im2show = vis_detections(im2show, classes[j], cls_dets, thresh=0.5)

        misc_toc = time.time()
        nms_time = misc_toc - misc_tic

        sys.stdout.write('im_detect: {:d}/{:d} {:.3f}s {:.3f}s   \r' \
                         .format(i + 1, num_images, detect_time, nms_time))
        sys.stdout.flush()

        if vis:
            # cv2.imshow('test', im2show)
            # cv2.waitKey(0)
            result_path = os.path.join(args.result_dir, imglist[i][:-4] + "_det.jpg")
            cv2.imwrite(result_path, im2show)
