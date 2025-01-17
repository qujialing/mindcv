from typing import Optional

import mindspore.nn as nn
from mindspore import Tensor

from ..utils import make_divisible
from .pooling import GlobalAvgPooling


class SqueezeExcite(nn.Cell):

    def __init__(self,
                 in_channels: int,
                 rd_ratio: float = 1. / 16,
                 rd_channels: Optional[int] = None,
                 rd_divisor: int = 8,
                 norm: Optional[nn.Cell] = None,
                 act_layer: nn.Cell = nn.ReLU,
                 gate_layer: nn.Cell = nn.Sigmoid
                 ) -> None:
        super(SqueezeExcite, self).__init__()
        self.norm = norm
        self.act = act_layer()
        self.gate = gate_layer()
        if not rd_channels:
            rd_channels = make_divisible(in_channels * rd_ratio, rd_divisor)

        self.conv_reduce = nn.Conv2d(in_channels=in_channels,
                                     out_channels=rd_channels,
                                     kernel_size=1,
                                     has_bias=True
                                     )
        if self.norm:
            self.bn = nn.BatchNorm2d(rd_channels)
        self.conv_expand = nn.Conv2d(in_channels=rd_channels,
                                     out_channels=in_channels,
                                     kernel_size=1,
                                     has_bias=True
                                     )
        self.pool = GlobalAvgPooling(keep_dims=True)

    def construct(self, x: Tensor) -> Tensor:
        x_se = self.pool(x)
        x_se = self.conv_reduce(x_se)
        if self.norm:
            x_se = self.bn(x_se)
        x_se = self.act(x_se)
        x_se = self.conv_expand(x_se)
        x_se = self.gate(x_se)
        x = x * x_se
        return x
