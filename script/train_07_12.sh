#!/bin/bash
set -e


CUDA_VISIBLE_DEVICES=4  python trainval_net.py test004 --dataset pascal_voc_0712 --net detnet59 --bs 2 --nw 4 --lr 1e-3 --lr_decay_step 5 --epochs 20 --save_dir models --cuda
