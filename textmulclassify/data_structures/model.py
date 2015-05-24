# -*- coding: utf-8 -*-

from etl_utils import UnicodeUtils, process_notifier, cpickle_cache
from collections import Counter
from urwid import is_wide_char
import random


class Distribution(list):
    """ 查看列表的数据分布情况 """

    def __init__(self, data1):
        if isinstance(data1, list):
            list1 = Counter(data1).most_common()
        if isinstance(data1, dict):
            list1 = sorted(data1.iteritems(), key=lambda i1: -i1[1])

        def get_width(str1):
            c = 0
            for s1 in str1:
                c += (2 if is_wide_char(s1, 0) else 1)
            return c
        list1_width = [get_width(i1[0]) for i1 in list1]
        self.max_strlen = max(list1_width) + 2

        super(Distribution, self).__init__(list1)

    def inspect(self):
        for k1, c1 in self:
            print UnicodeUtils.rjust(k1, self.max_strlen), ":", c1, "\n"


class TMCModel(object):
    """ TMCClassify接受的输入Model """

    tags_tree = None
    tags_column_name = None

    @classmethod
    def tags_model__extract_features(cls, item, column=None):
        raise NotImplemented

    @classmethod
    def tags_model__extract_tags(cls, item):
        return [t1 for t1 in getattr(item, cls.tags_column_name)
                if cls.tags_tree.has_node(t1)]

    @classmethod
    def tags_model__append_more_features_when_recommend(cls, item, sorted_features):
        return sorted_features

    @classmethod
    def is_valid_tag(cls, tag1):
        return cls.tags_tree.has_node(tag1)

    def __repr__(self):
        print "item_id", self.item_id, "\n"
        print "item_content", self.item_content, "\n"
        return ''

    @classmethod
    def test_items(cls):
        """ default test items """
        return [cls[item_id1] for item_id1 in cls.test_item_ids()]

    @classmethod
    def test_item_ids(cls):
        """ 在ModelCache数据准备好之后，在训练和评估之前，应该先选出test_item_ids. """
        def func():
            print "[select test item ids]\n"
            all_item_ids = cls.all_item_ids()
            random.shuffle(all_item_ids)
            if cls.classify.max_train_data_count == 0:
                return []  # compact
            return all_item_ids[-cls.classify.max_train_data_count:]
        ids = cpickle_cache(cls.pickle_path('test_item_ids'), func)
        return set(ids)

    @classmethod
    def all_item_ids(cls):
        def filtered_item_ids_by_has_tags():
            print "[load from original data]\n"
            cls.pull_data()
            # 过滤掉 没有Tag的items
            return [item_id1 for item_id1, item1 in process_notifier(cls)
                    if cls.tags_model__extract_tags(item1)]

        print "[load tags_items_ids]\n"
        return cpickle_cache(cls.pickle_path('tags_items_ids'), filtered_item_ids_by_has_tags)
