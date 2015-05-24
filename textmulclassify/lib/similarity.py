# -*- coding: utf-8 -*-

# original author is @junchen and @LiHeng
# refactored by @mvj3

# from scipy.spatial.distance import cosine as scipy_cosine
# from collections import OrderedDict
from math import sqrt


class Similarity(object):
    def __init__(self, mode='cosine'):
        self.mode = mode  # 默认 余弦相似度
        assert self.mode in [
            'cosine',  # 余弦相似度
            'set',    # 集合相似度
        ]

    def __call__(self, kw1, kw2):
        """ kw = keywords_weight """
        return getattr(self, self.mode)(kw1, kw2)

    def _denominator(self, d1):
        return sqrt(float(sum([v1 ** 2 for v1 in d1.itervalues()])))

    def cosine(self, kw1, kw2):
        """
        # 太慢了，生成对象太多
        two_arrays = OrderedDict()
        for k1, w1 in kw1.iteritems():
            two_arrays[k1] = [w1, 0.0]
        for k2, w2 in kw2.iteritems():
            v2 = two_arrays.get(k2, None)
            if v2 is None:
                two_arrays[k2] = [0.0, w2]
            else:
                v2[1] = w2
        values = two_arrays.values()
        a = [i1[0] for i1 in values]
        b = [i1[1] for i1 in values]
        """
        denominator = self._denominator(kw1) * self._denominator(kw2)
        if denominator == 0.0:
            return 0.0

        # TODO 既然 for2.get(k1, 0.0) 没有的就没有，所以谁先谁后就补关键了？
        # 不管是分子还是分母，因为乘以零还是零，所以不用在乎两者各自缺失的 keys, _denominator 和 这里都是对的。
        for1, for2 = [kw1, kw2] if len(kw1) < len(kw2) else [kw2, kw1]
        total = 0.0
        for k1, v1 in for1.iteritems():
            total += v1 * for2.get(k1, 0.0)
        return total / denominator

        """
        if isinstance(kw1, dict):
            keys = set(kw1.keys() + kw2.keys())
            a, b = [], []
            for k1 in keys:
                a.append(kw1.get(k1, 0.0))
                b.append(kw2.get(k1, 0.0))
        else:
            a, b = kw1, kw2

        # 有点慢，主要是生成额外对象
        return 1 - scipy_cosine(a, b) # scipy里是得相减的。
        """


# 余弦相似度

# 对text_count2的v1取log，不管底数如何。召回率不变，正确率降低了快一半。
# text_count2 = {k1 : math.log(v1, 2) for k1, v1 in text_count2.iteritems()}
# 对text_count2的v1取指数，两率都下降两个百分点。
# text_count2 = {k1 : v1**2 for k1, v1 in text_count2.iteritems()}

# 自定义相似度(还不知道学名)
"""
denominator     = float(sum(text_count1.values()) * sum(text_count2.values()))
common_features =       set(text_count1.keys())   & set(text_count2.keys())

result = 0.0
for feature1 in common_features:
    result += text_count1[feature1] * text_count2[feature1] / denominator

return result
"""
