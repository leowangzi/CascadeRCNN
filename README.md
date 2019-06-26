# DetNet
pytorch-1.1 torchvision-0.3

### References

- https://github.com/guoruoqian/DetNet_pytorch
- https://github.com/jwyang/fpn.pytorch
- https://github.com/jwyang/faster-rcnn.pytorch/tree/pytorch-1.0


### Prerequisites

- Python 2.7 or 3.6
- Pytorch 1.1 or higher
- CUDA 8.0 or higher
- tensorboardX

### Preparation

First of all, clone the code
```
git clone https://github.com/leowangzi/DetNet.git
cd DetNet
```
Then, create a folder:
```
mkdir data
```
or
```
ln -s [source_data] data
```


### What we are doing and going to do

- [x] Support pytorch-1.1 (master).
- [x] Support torchvision-0.3 (master).
- soft-nms

### Benchmarking

I benchmark this code thoroughly on pascal voc2007 and 07+12. Below are the results:

1). PASCAL VOC 2007 (Train/Test: 07trainval/07test, scale=600, ROI Align)

| model（FPN）                                                 | GPUs            | Batch Size | lr   | lr_decay | max_epoch | Speed/epoch | Memory/GPU | mAP  |
| ------------------------------------------------------------ | --------------- | ---------- | ---- | -------- | --------- | ----------- | ---------- | ---- |
| DetNet59 | 1 GTX 1080 (Ti) | 2          | 1e-3 | 10       | 12        | 1.07hr      | 5412MB     | 75.5 |

2). PASCAL VOC 07+12 (Train/Test: 07+12trainval/07test, scale=600, ROI Align)

| model（FPN）                                                 | GPUs            | Batch Size | lr   | lr_decay | max_epoch | Speed/epoch | Memory/GPU | mAP  |
| ------------------------------------------------------------ | --------------- | ---------- | ---- | -------- | --------- | ----------- | ---------- | ---- |
| DetNet59 | 1 GTX 1080 (Ti) | 1          | 1e-3 | 10       | 12        | 2.33hr      | 8015MB     | 81.5 |