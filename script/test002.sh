#!/bin/bash
set -e


CUDA_VISIBLE_DEVICES=6  python test_net.py test002 --dataset pascal_voc --net res101 --checksession 1 --checkepoch 7 --checkpoint 5010 --load_dir models --cuda
