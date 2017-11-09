#
#   Loading and saving darknet weight files
#   Copyright EAVISE
#

import numpy as np
import torch
import torch.nn as nn

import lightnet.layers as lnl
from .logger import *


class WeightLoader:
    """ Load darknet weight files into pytorch layers """
    def __init__(self, filename):
        with open(filename, 'rb') as fp:
            self.header = np.fromfile(fp, count=3, dtype=np.int32).tolist()
            ver_num = self.header[0]*100+self.header[1]*10+self.header[2]
            log(Loglvl.DEBUG, f'Loading weight file: version {self.header[0]}.{self.header[1]}.{self.header[2]}')

            if ver_num <= 19:
                log(Loglvl.WARN, 'Weight file uses sizeof to compute variable size, which might lead to undefined behaviour. (choosing int=int32, float=float32)')
                self.seen = int(np.fromfile(fp, count=1, dtype=np.int32)[0])
            elif ver_num <= 29:
                log(Loglvl.WARN, 'Weight file uses sizeof to compute variable size, which might lead to undefined behaviour. (choosing int=int32, float=float32, size_t=int64)')
                self.seen = int(np.fromfile(fp, count=1, dtype=np.int64)[0])
            else:
                log(Loglvl.ERROR, 'New weight file syntax! Loading of weights might not work properly. Please submit an issue with the weight file version number. [Run with Loglvl.DEBUG]')
                self.seen = int(np.fromfile(fp, count=1, dtype=np.int64)[0])
            
            self.buf = np.fromfile(fp, dtype = np.float32)

        self.start = 0
        self.size = self.buf.size

    def load_layer(self, layer):
        """ Load weights for a layer from the weights file """
        if type(layer) == nn.Conv2d:
            self._load_conv(layer)
        elif type(layer) == lnl.Conv2dBatchLeaky:
            self._load_convbatch(layer)
        elif type(layer) == nn.Linear:
            self._load_fc(layer)
        else:
            raise NotImplementedError(f'The layer you are trying to load is not supported [{type(layer)}]')

    def _load_conv(self, model):
        num_b = model.bias.numel()
        model.bias.data.copy_(torch.from_numpy(self.buf[self.start:self.start+num_b])
                                   .view_as(model.bias.data))
        self.start += num_b

        num_w = model.weight.numel()
        model.weight.data.copy_(torch.from_numpy(self.buf[self.start:self.start+num_w])
                                     .view_as(model.weight.data))
        self.start += num_w

    def _load_convbatch(self, model):
        num_b = model.layer[1].bias.numel()
        model.layer[1].bias.data.copy_(torch.from_numpy(self.buf[self.start:self.start+num_b])
                                            .view_as(model.layer[1].bias.data))
        self.start += num_b
        model.layer[1].weight.data.copy_(torch.from_numpy(self.buf[self.start:self.start+num_b])
                                              .view_as(model.layer[1].weight.data))
        self.start += num_b
        model.layer[1].running_mean.copy_(torch.from_numpy(self.buf[self.start:self.start+num_b])
                                               .view_as(model.layer[1].running_mean))
        self.start += num_b
        model.layer[1].running_var.copy_(torch.from_numpy(self.buf[self.start:self.start+num_b])
                                              .view_as(model.layer[1].running_var))
        self.start += num_b

        num_w = model.layer[0].weight.numel()
        model.layer[0].weight.data.copy_(torch.from_numpy(self.buf[self.start:self.start+num_w])
                                              .view_as(model.layer[0].weight.data))
        self.start += num_w 

    def _load_fc(self, model):
        num_b = model.bias.numel()
        model.bias.data.copy_(torch.from_numpy(self.buf[self.start:self.start+num_b])
                                   .view_as(model.bias.data))
        self.start += num_b

        num_w = model.weight.numel()
        model.weight.data.copy_(torch.from_numpy(self.buf[self.start:self.start+num_w])
                                     .view_as(model.weight.data))
        self.start += num_w 


class WeightSaver:
    """ Save darknet weight files from pytorch layers """
    def __init__(self, header, seen):
        self.weights = []
        self.header = np.array(header, dtype=np.int32)
        ver_num = self.header[0]*100+self.header[1]*10+self.header[2]
        if ver_num <= 19:
            self.seen = np.int32(seen)
        elif ver_num <= 29:
            self.seen = np.int64(seen)
        else:
            log(Loglvl.ERROR, 'New weight file syntax! Saving of weights might not work properly. Please submit an issue with the weight file version number. [Run with Loglvl.DEBUG]')
            self.seen = np.int64(seen)

    def write_file(self, filename):
        """ Save the accumulated weights to a darknet weightfile """
        log(Loglvl.DEBUG, f'Writing weight file: version {self.header[0]}.{self.header[1]}.{self.header[2]}')
        with open(filename, 'wb') as fp:
            self.header.tofile(fp)
            self.seen.tofile(fp)
            for np_arr in self.weights:
                np_arr.tofile(fp)
        log(Loglvl.DEBUG, f'Weight file saved as {filename}')

    def save_layer(self, layer):
        """ save weights for a layer """
        if type(layer) == nn.Conv2d:
            self._save_conv(layer)
        elif type(layer) == lnl.Conv2dBatchLeaky:
            self._save_convbatch(layer)
        elif type(layer) == nn.Linear:
            self._save_fc(layer)
        else:
            raise NotImplementedError(f'The layer you are trying to save is not supported [{type(layer)}]')

    def _save_conv(self, model):
        self.weights.append(model.bias.cpu().data.numpy())
        self.weights.append(model.weight.cpu().data.numpy())

    def _save_convbatch(self, model):
        self.weights.append(model.layer[1].bias.cpu().data.numpy())
        self.weights.append(model.layer[1].weight.cpu().data.numpy())
        self.weights.append(model.layer[1].running_mean.cpu().numpy())
        self.weights.append(model.layer[1].running_var.cpu().numpy())
        self.weights.append(model.layer[0].weight.cpu().data.numpy())

    def _save_fc(self, model):
        self.weights.append(model.bias.cpu().data.numpy())
        self.weights.append(model.weight.cpu().data.numpy())