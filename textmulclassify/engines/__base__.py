# -*- coding: utf-8 -*-

from etl_utils import cached_property
from ..lib import Similarity
from collections import defaultdict

class DefaultEngine(object):
    """ 给候选Tags重新排序和过滤的Engine. """

    # core
    def __init__(self, **opts):
        self.opts = opts
        for k1, v1 in self.opts.iteritems():
            setattr(self, k1, v1)

        self.similarity = Similarity()
        self.setup()

    def __call__(self, item1, candidates_with_weight=[]):
        data = self.call(item1, candidates_with_weight)
        data.update({"counter" : self.counter(data['data'])})
        return data


    # API
    def setup(self):
        pass

    def call(self, item1, candidates_with_weight=[]):
        return {
                "data"   : candidates_with_weight,
                "detail" : { },
               }

    # utils
    def extract_features_weight(self, item1):
        """ 抽取 { feature1 => weight1, ... } """
        raise NotImplemented

    @cached_property
    def model(self): return self.classify.model

    def counter(self, candidate_tags1):
        return defaultdict(lambda : 0.0, {c1[0] : c1[1] for c1 in candidate_tags1})
