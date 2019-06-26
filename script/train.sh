#!/bin/bash
set -e
cd ..

CUDA_VISIBLE_DEVICES=6 python trainval_net.py test001 --dataset pascal_voc --net detnet59 --bs 2 --nw 4 --lr 1e-3 --lr_decay_step 10 --epochs 12 --save_dir models --cuda
