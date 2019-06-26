#!/bin/bash
set -e

max_epoch=19
checkpoint=16550


for ((i=5; i<$max_epoch; i+=1))
do
    echo "-------------------process $i epoch!-------------------------"
    CUDA_VISIBLE_DEVICES=7  python test_net.py test004 --dataset pascal_voc_0712 --net detnet59 --load_dir models  --checksession 1 --checkepoch $i --checkpoint $checkpoint --cuda
done
