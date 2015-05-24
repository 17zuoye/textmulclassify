# -*- coding: utf-8 -*-

from .__base__ import DefaultEngine
from collections import Counter


class AssociationRuleLearningEngine(DefaultEngine):
    """ 计算特征相似度 """

    def setup(self):
        pass

    def call(self, item1, candidates_with_weight=[]):
        fw1 = self.extract_features_weight(item1)

        candidate_nodes = set([node1 for feature1 in fw1
                               for node1 in self.classify.tags_tree.feature_to_nodes[feature1]])

        candidate_nodes__dict = {node1: self.similarity(node1.features_weight, fw1) for node1 in candidate_nodes}

        # use Counter#most_common to sort dict to list by desc order.
        sorted_candidate_nodes_weight__list = Counter({node1.name: weight1 for node1, weight1 in candidate_nodes__dict.iteritems()}).most_common()

        # 优化 裁剪候选知识点列表
        max_rate = sorted_candidate_nodes_weight__list[0][1] if sorted_candidate_nodes_weight__list else 0.0
        # 1. 采用和最匹配者百分比过滤
        candidate_tags = [i1 for i1 in sorted_candidate_nodes_weight__list if i1[1] >= max_rate * self.classify.related_to_max_percent]
        # 2. 采用比率过滤
        candidate_tags = candidate_tags[0:self.classify.default_guess_count]

        return {
            "data": candidate_tags,
            "detail": {},
        }

    def extract_features_weight(self, item1):
        result1 = None

        # 有item_id才可以缓存嘛，否则文本就不缓存，而直接返回结果了。
        if item1.item_id:
            result1 = self.classify.documents_with_features.get(item1.item_id, False)

        # cache result to *self.classify.documents_with_features*
        if not result1:
            result1 = Counter(self.classify.model.tags_model__extract_features(item1))
            if item1.item_id:
                self.classify.documents_with_features[item1.item_id] = result1

        return self.classify.calculate_features_weight(result1)
