#!/bin/bash
set -e
cd ..

CUDA_VISIBLE_DEVICES=6  python test_net.py test001 --dataset pascal_voc --net detnet59 --checksession 1 --checkepoch 11 --checkpoint 5010 --load_dir models --cuda
