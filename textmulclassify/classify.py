# -*- coding: utf-8 -*-

__all__ = ["TextMulClassify"]

import math
import os
import random
from collections import defaultdict, Counter
from etl_utils import process_notifier, cpickle_cache, cached_property, \
    uprint, UnicodeUtils, jieba_parse, DictUtils
from termcolor import cprint
from tfidf import TfIdf
from model_cache.tools.parallel import ParallelData
from forwardable import Forwardable, def_delegators


def pn(msg):
    cprint(msg, 'cyan')

from .data_structures import TMCModel, TMCTree
from .lib import ReadManualKps, FeaturesWeight, Similarity, Evaluate
from .engines import AssociationRuleLearningEngine, TextSimilarityEngine


class TextMulClassify(object):

    __metaclass__ = Forwardable
    _ = def_delegators("features_weight_machine", ["extract_feature_words",
                                                   "calculate_features_weight", "compute_words_and_weights", ])

    @cached_property
    def classify(self):
        return self  # alias

    def __init__(self, model1, tags_file1, **opts):
        """ 以下属性都可以通过model, tags_file, opts进行设置 """
        print "Init TagClassify at", id(self)
        # 1. 基本配置
        self.model = model1
        self.cache_dir = self.model.cache_dir
        self.opts = opts
        self.model.tags_tree = TMCTree(tags_file1)

        # linked together!
        self.model.tags_tree.classify = self
        self.model.classify = self
        # tags_tree is a cached_property, see `def tags_tree(self):`

        self.is_run_test   = opts.get('is_run_test', False)

        # 2. 自定义训练数据
        self.max_train_data_count = 2000 if self.is_run_test else 0
        self.stop_words_files = []
        self.jieba_userdict_files = []
        self.idf_file = None
        self.entropy_file = None

        # 3. 一系列模型参数
        self.default_guess_count = opts.get('default_guess_count', 10)

        # 0.6 -> 0.7 -> 0.8 效果会提升一两个百分点。
        # 两个会好点，但是一个反而都差了。
        # 0.5也是变差了。
        self.related_to_max_percent = opts.get('related_to_max_percent', 0.60)

        self.mix_score_percent = opts.get('mix_score_percent', 0.8)
        self.mix_unicode_coefficient = opts.get('mix_unicode_coefficient', 1.8)

        # overwrite all defaults
        for opt1, v1 in self.opts.iteritems():
            setattr(self, opt1, v1)
        assert isinstance(self.stop_words_files, list)
        assert isinstance(self.jieba_userdict_files, list)

        # 4. 相关模块
        self.features_weight_machine = FeaturesWeight(self)
        self.evaluate = lambda items: Evaluate(self.model.tags_tree, items)

    def cpath(self, name):
        return self.model.pickle_path(name)

    @cached_property
    def documents_with_features(self):
        """ 基本耗时都在posseg.cut """
        print "\ntfidf需要的文档列表"
        return ParallelData.process(self.model, 'dict',
                                    self.model.pickle_path('documents_with_features'),
                                    item_func=lambda item1: Counter(self.model.tags_model__extract_features(item1)),
                                    )

    @cached_property
    def documents_with_segments(self):
        """ 纯分词 """
        return ParallelData.process(self.model, 'dict',
                                    self.model.pickle_path('documents_with_segments'),
                                    item_func=lambda item1: Counter(jieba_parse(item1.item_content)),
                                    )

    @cached_property
    def idf_cache(self):
        """ 训练+测试 预料全在里面了 """
        result = TfIdf(self.documents_with_segments, self.cache_dir).idf_cache
        self.idf_file = result  # 采用自己的IDF，给FeaturesWeight用
        return result

    @cached_property
    def entropy_cache(self):
        """ 训练+测试 预料全在里面了 """
        from .lib.entropy import EntropyFunc
        result = EntropyFunc.process(self.documents_with_segments, self.cache_dir)
        self.entropy_file = result  # 采用自己的熵，给FeaturesWeight用
        result = DictUtils.add_default_value(result)

        """
        from etl_utils import is_regular_word, Unicode
        for k1 in result.keys():
            if not (is_regular_word(k1) or Unicode.is_chinese(k1)):
                del result[k1]
        """

        self.entropy_file = result
        return result

    @property
    def association_rule_learning_engine(self):
        return AssociationRuleLearningEngine(classify=self.classify)

    @property
    def text_similarity_engine(self):
        return TextSimilarityEngine(classify=self.classify)

    # 暴露接口
    @cached_property
    def recommend_tags(self):
        self.load_train_data()

        def recommend_tags(item1):
            """ 参数: 输入的item1一般来说必须是持久化的。 """
            # TODO 可能把 node1.features_weight 直接优化成数组来做

            # A. 计算特征相似度
            result_rule = self.association_rule_learning_engine(item1)

            # B. 计算文本相似度
            result_text = self.text_similarity_engine(item1, result_rule['data'])

            count_feature, count_text = result_rule['counter'], result_text['counter']
            result_mix = sorted([[t1[0],
                                  count_feature[t1[0]] + count_text[t1[0]] * self.mix_unicode_coefficient]
                                 for t1 in result_rule['data']],
                                key=lambda i1: -i1[1])

            print "=" * 60
            uprint(u"题目ID", item1.item_id)
            uprint(u"题目content", item1.item_content)
            print
            uprint(u"original 知识点", self.model.tags_model__extract_tags(item1))
            uprint(u"features 相似度", result_rule['data'])
            uprint(u"unicode  相似度", result_text['data'])
            uprint(u"mix      相似度", result_mix)

            if result_mix:
                candidate_tags  = result_mix[0:self.default_guess_count]

                # 用于提升超过两个推荐的"正确度"。
                max_score = max([i1[1] for i1 in result_mix])
                candidate_tags  = filter(lambda i1: i1[1] >= (max_score * self.mix_score_percent), candidate_tags)
            else:
                candidate_tags  = []
            uprint(u"[final]", candidate_tags)
            print "\n" * 3

            #import pdb; pdb.set_trace()
            candidate_tags = [{"name": name1, "ids": self.tags_tree.fetch_name_ids(name1),
                               "weight": weight1} for name1, weight1 in candidate_tags]

            return {
                "item_id": item1.item_id,
                "item_content": item1.item_content,
                "recommend_tags": candidate_tags,
                "original_tags": self.model.tags_model__extract_tags(item1),
            }
        return recommend_tags

    @cached_property
    def tags_tree(self):
        """ load_features_with_weight """
        # modify tags_tree
        def func():
            if 'manual_kps' in self.opts:
                # 人工标记，如吕文星标记的初高中知识点短规则组合。
                data = {kp1: Counter(features) for kp1, features in ReadManualKps.process(self.opts['manual_kps']).iteritems()}
            else:
                # 机器训练
                data = self.model.tags_tree.load__tag_to_words_count__dict(self.model, self.documents_with_features)

            print "load_words_with_weight ..."
            self.model.tags_tree.load_features_with_weight(data)
            self.model.tags_tree.classify = None
            return self.model.tags_tree

        o1 = cpickle_cache(self.model.pickle_path('tags_tree'), func)
        o1.classify = self  # Fix cPickle.UnpickleableError
        return o1

###############################################################################################################
    def evaluate_effect(self, default_guess_count=10):
        if not self.is_run_test:
            print "没有设置is_run_test=True!"
            exit(0)

        test_items = self.model.test_items()
        print "要评估", len(test_items), "个条目"

        self.tags_tree.inspect('features_weight')

        result = [[self.model.tags_model__extract_tags(item1), self.recommend_tags(item1)]
                  for item1 in process_notifier(test_items)]

        def inspect_result(result, filter_item_ids=set([])):
            for idx1, two_parts in enumerate(result):
                print "第", idx1 + 1, "个"
                original_tags, recommend_data = two_parts
                if recommend_data['item_id'] not in filter_item_ids:
                    continue

                print "试题ID", recommend_data['item_id']
                print "试题内容", recommend_data['item_content']
                uprint(u"关键词列表 => 熵", recommend_data['features_weight'])
                uprint(u"原始标签:", original_tags)
                uprint(u"推荐标签:", recommend_data['recommend_tags'])
                uprint(u"推荐细节:", recommend_data['recommend_tags_detail'])
                print "\n" * 3
        inspect_result(result)

        evaluate_items = [{"object_id": recommend_data['item_id'],
                           "original_tags": original_tags, "recommend_tags": [i1['name'] for i1 in recommend_data['recommend_tags']]}
                          for original_tags, recommend_data in result]

        # 手工评估
        def ee(num=1):
            self.evaluate([{"object_id": recommend_data['item_id'],
                            "original_tags": original_tags,
                            "recommend_tags": [i1['name'] for i1 in recommend_data['recommend_tags'][0:num]]}
                           for original_tags, recommend_data in result])
        # --------------------------------------------

        # 初中物理 查看知识点树在每条路径上被引用的分布情况  [(0, 357), (1, 217), (2, 24), (3, 1)]
        self.tags_tree.distribution([i1['recommend_tags'] for i1 in evaluate_items])
        self.evaluate(evaluate_items)

        if ('eval_result' in evaluate_items[0]) and False:
            eval_items2 = filter(lambda i1: i1['eval_result'], evaluate_items)
            inspect_result(result, [i1['object_id'] for i1 in eval_items2])
            self.tags_tree.distribution([i1['original_tags'] for i1 in eval_items2])
        import pdb
        pdb.set_trace()

    def load_train_data(self):
        jieba_parse(u"你好")  # load jieba first

        cpath = self.cpath

        data_list = [
            {
                "path": [cpath('documents_with_segments'), ],
                "var": "documents_with_segments", "lazy": True,
            },
            {
                "path": [cpath("idf"), ],
                "var": "idf_cache", "lazy": False,
            },
            {
                "path": [cpath("entropy"), ],
                "var": "entropy_cache", "lazy": False,
            },
            {
                "path": [self.model.dbpath, cpath('documents_with_features'), ],
                "var": "documents_with_features", "lazy": True,
            },
            {
                "path": cpath('tags_tree'),
                "var": "tags_tree", "lazy": False,
            },
            {
                "path": cpath('text_engine'),
                "var": "text_similarity_engine", "lazy": False,
            },
        ]

        if not os.path.exists(cpath('idf')):
            self.model.pull_data()

        for idx1, data1 in enumerate(data_list):
            print "\n" * 5
            print "_" * 150
            print "[" * 3 + "#" * 144 + "]" * 3
            print "[第%i步] 检查预生成 %s" % (idx1 + 1, data1['path'])

            if not isinstance(data1['path'], list):
                data1['path'] = [data1['path']]

            should_read_attr = False
            for path1 in data1['path']:
                if not os.path.exists(path1):
                    should_read_attr = True

            if (not data1['lazy']) or should_read_attr:
                getattr(self, data1['var'])


###############################################################################################################
TextMulClassify.TMCModel = TMCModel  # bind to namespace
TextMulClassify.TMCTree = TMCTree
TextMulClassify.Evaluate = Evaluate

"""
1. 筛选出大部分badcases [想出文本相似度方案]
2. 合并两种方案，强强联合。[已整合, 有效果]
3. "勾股定理的证明"等隐含特征只能从a2+b2=c2公式中推理出来吗。 [目前在一定程度上用于文本相似度]
4. 添加老师手工特征。[没效果]
5. 在候选基础上，应用基于字符的文本相似度。和detdup类似。[7-9%提升]

1. 前端也可以按颜色区分推荐度。
"""
