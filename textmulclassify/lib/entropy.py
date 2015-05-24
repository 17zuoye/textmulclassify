# -*- coding: utf-8 -*-

"""
计算 特征值的熵，看看特征值在知识点下的分布是否混乱。

每个特征都只有一个熵值。

           / tag1
Feature(i) - tag2
           \ tag3
           \ ...
           \ tagj

P(ij) = Feature(ij)/Feature(i)
H(i)  = - (连加 P(ij) * log( P(ij) ))
"""

from etl_utils import cpickle_cache, process_notifier  # , calculate_entropy
from collections import defaultdict

try:
    from scipy.stats import entropy as scipy_entropy
except ImportError, e:
    import math

    def scipy_entropy(values):
        feature_count_sum = float(sum(values))

        entropy = 0.0
        for c1 in values:
            p_ij = c1 / feature_count_sum
            entropy += p_ij * math.log(p_ij)
        return - entropy


class EntropyFunc(object):

    @classmethod
    def process(cls, d1, cache_dir):
        """ d1 is {"feature1":count1, "feature2":count2, ... } """

        def func():
            # 1. fetch all features
            uniq_keys = set([])
            for item_id1, item1 in process_notifier(d1):
                [uniq_keys.add(k1) for k1 in item1.iterkeys()]
            uniq_keys = list(uniq_keys)

            # 2. feature1 => {doc1: count1, doc2: count2, ...}
            value_cache = defaultdict(dict)
            for item_id1, item1 in process_notifier(d1):
                for k1, c1 in item1.iteritems():
                    value_cache[k1][item_id1] = c1

            # 3. calculate each feauture's entropy
            entropy_cache = dict()
            total_len = len(d1)
            for k1 in process_notifier(uniq_keys):
                exist_values = value_cache[k1].values()
                total_values = exist_values + [0] * (total_len - len(value_cache))

                entropy_cache[k1] = scipy_entropy(total_values)

            return entropy_cache

        return cpickle_cache(cache_dir + '/entropy.cPickle', func)
