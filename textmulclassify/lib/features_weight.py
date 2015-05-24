# -*- coding: utf-8 -*-

# original author is @junchen , @liheng
# refactored by @mvj3

import os
import json
from etl_utils import UnicodeUtils, cached_property, singleton
from collections import defaultdict, Counter
import jieba.posseg as posseg


@singleton()
class JIEBA_CLASS(object):

    def __init__(self):
        self.jieba = posseg.jieba

    def load_dictionaries(self, userdicts=[]):
        for file1 in userdicts:
            self.jieba.load_userdict(file1)

    def normal_cut(self, unicode1):
        return self.jieba.cut(unicode1)

    def posseg_cut(self, unicode1):
        return posseg.cut(unicode1)


class FeaturesWeight(object):

    def __init__(self, classify):
        self.classify = classify

        self.JIEBA = JIEBA_CLASS()
        self.JIEBA.load_dictionaries(classify.jieba_userdict_files)

        self.key_tag = set(['mk', 'mw'])
        self.obsolete_tag = set(['x', 'm', 'eng'])

        self.short_seg_threshold = 1
        self.long_key_seg_threshold = 2
        self.key_word_threshold = 0.005

    def load_data_from_input(self, input1):
        """ return data is a dict. """
        def wrap(data):
            avg = sum(data.values()) / float(len(data))
            return defaultdict(lambda: avg, data)

        if isinstance(input1, dict):
            return wrap(input1)

        if not os.path.exists(input1):
            return defaultdict(float)

        content = UnicodeUtils.read(input1).strip()
        try:
            data = json.loads(content)
        except:
            data = dict()
            for line in content.split("\n"):
                result = line.split(',')
                data[result[0]] = float(result[1].strip())

        return wrap(data)

    @cached_property
    def H_i_dict(self):
        d1 = self.load_data_from_input(self.classify.entropy_file)
        avg = sum(d1.values()) / float(len(d1))
        for k2 in d1.keys():
            if d1[k2] == 0.0:
                d1[k2] = avg  # tmp fix
        return d1

    @cached_property
    def idf_dict(self):
        return self.load_data_from_input(self.classify.idf_file)

    @cached_property
    def stop_words_set(self):
        return set([w1.strip() for file1 in self.classify.stop_words_files
                    for w1 in UnicodeUtils.read(file1).split("\n")])

    # @profile
    def extract_feature_words(self, in_text):
        """ 专业词汇抽取 + 对长词(3)再做分词 """
        assert isinstance(in_text, unicode), in_text

        seg_list = list(self.JIEBA.posseg_cut(in_text))  # NOTE 此处最慢
        lv_1_list = []
        lv_2_list = []

        def _continue(seg):
            if len(seg.word) == self.short_seg_threshold and (seg.flag not in self.key_tag):
                # 非关键词短串扔掉
                return True
            if seg.word in self.stop_words_set:
                # 扔掉次要词和标点及其他无关紧要的词
                return True
            if seg.flag in self.obsolete_tag:
                # 确定遗弃的词性
                return True
            return False

        def cut2(seg, lv_2_list):
            # 如果是关键词，字串长超过3个字
            if seg.flag in self.key_tag and len(seg.word) > self.long_key_seg_threshold:
                # 进一步切割以增加召回
                second_cut = list(self.JIEBA.normal_cut(seg.word))
                for sec_word in second_cut:
                    if (second_cut != seg.word) and (sec_word not in self.stop_words_set):
                        # 成功切割，增加入词库
                        lv_2_list.append(sec_word)
                # 第一个切词即和原词相同，未切割

        def process(seg, lv_1_list, lv_2_list):
            if _continue(seg):
                return False
            # 剩下的都是需要解析的词
            # 加入词列
            lv_1_list.append(seg)

            cut2(seg, lv_2_list)

        map(lambda seg: process(seg, lv_1_list, lv_2_list), seg_list)  # 此处运行时间仅为 1.6%

        # list 1 contains both flag and word
        # list 2 contains only word
        # directly return the list of words
        all_list = [item.word for item in lv_1_list]
        all_list.extend(lv_2_list)

        return all_list

    def calculate_features_weight(self, words_counter):
        """ 用占用个数 + idf + H 计算weight """
        words_len  = float(sum(words_counter.values()))
        assert words_len != 0

        weight_dict = dict()
        for word1, count1 in words_counter.iteritems():
            weight_dict[word1] = (count1 / words_len) * self.idf_dict[word1] / self.H_i_dict[word1]

        for word1 in weight_dict.keys():
            if weight_dict[word1] <= self.key_word_threshold:
                del weight_dict[word1]
        return weight_dict

    def compute_words_and_weights(self, text1):
        words = self.extract_feature_words(text1)
        keywords_weight = self.calculate_features_weight(Counter(words))
        return words, keywords_weight
