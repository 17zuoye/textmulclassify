# -*- coding: utf-8 -*-

import os
import sys
import unittest
import time
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

print "Delete pre caching"
time.sleep(1)
test_dir = os.path.join(root_dir, 'tests/output/')
os.system("rm -rf %s/*" % test_dir)

# File.read("high_school_math_tags/q_data/math.20140805.dat").split("\n").map {|line| _id, content, tags = line.split("\t"); {"_id"=>_id, "content"=>content, "tags"=>(tags || "").split("//")}}[0,100].each {|json| puts json };0
# %s/=>/ : u/g
# %s/]}/]},/g
# %s/ : u\[/ : \[/g
from tests.data_list import data_list
from tests.data_list_test import data_list_test


def process_data_list(record):
    record['tags'] = [unicode(t1, "UTF-8") for t1 in record['tags']]
    return record
data_list = [process_data_list(record) for record in data_list]
data_list_test = [process_data_list(record) for record in data_list_test]


class OriginalFoobarModel(list):
    pass
foobar_data = OriginalFoobarModel(data_list)

from textmulclassify import TextMulClassify
from model_cache import ModelCache
from etl_utils import jieba_parse, uprint


@ModelCache.connect(foobar_data, cache_dir=test_dir)
class FoobarModel(TextMulClassify.TMCModel):
    """ put in the root namespace, not in a function, so can pickle. """

    def init__load_data(self, record):
        self.item_id      = str(record['_id'])
        self.item_content = record['content']
        self.tags         = record['tags']

    @classmethod
    def tags_model__extract_features(cls, item, column=None):
        return jieba_parse(item.item_content)

    @classmethod
    def tags_model__extract_tags(cls, item):
        return item.tags


# init
tr = TextMulClassify(FoobarModel,
                     os.path.join(root_dir, "tests/tags_tree.dat"),

                     # 因为 test case 里数据量特别少，所以把阈值降低，大概能测试出效果就好。
                     default_guess_count=10,
                     # 以下三个参数设为0.1 以尽可能放到候选里。
                     related_to_max_percent=0.1,
                     mix_score_percent=0.1,
                     mix_unicode_coefficient=0.1,
                     # is_run_test=True # 会设置max_train_data_count为2000的
                     )

tr.recommend_tags  # eage load function, or will error.


def recommend_tags(item1):
    return [i1['name'] for i1 in tr.recommend_tags(item1)['recommend_tags']]

math_tree = TextMulClassify.TMCTree([
    {"current_id": 0, "parent_id": None, "name": u"数与代数"},
    {"current_id": 1, "parent_id": 0, "name": u"集合"},
    {"current_id": 2, "parent_id": 0, "name": u"函数"},
    {"current_id": 3, "parent_id": 1, "name": u"集合的概念"},
    {"current_id": 4, "parent_id": 2, "name": u"函数的零点与方程的根"},
    {"current_id": 5, "parent_id": 3, "name": u"集合的含义"},
    {"current_id": 6, "parent_id": 3, "name": u"元素与集合关系的判断"},
    {"current_id": 7, "parent_id": 6, "name": u"判断元素是否属于集合问题"},
    {"current_id": 8, "parent_id": 6, "name": u"集合中元素的性质及构成"},
    {"current_id": 9, "parent_id": 6, "name": u"计算集合元素个数问题"},
    {"current_id": 10, "parent_id": 6, "name": u"元素与集合关系的新定义问题"},
    {"current_id": 11, "parent_id": 4, "name": u"二分法求方程的近似解"},
    {"current_id": 12, "parent_id": 11, "name": u"二分法的定义"},
    {"current_id": 13, "parent_id": 11, "name": u"二分法的应用范围（看图判断）"},
    {"current_id": 14, "parent_id": 11, "name": u"二分法求方程的近似解"},
])


class TestTR(unittest.TestCase):

    def setUp(self):
        """ """

    def test_train_data(self):
        """ just test basic level """
        item1 = FoobarModel.values()[0]
        result_array = recommend_tags(item1)
        self.assertTrue(len(result_array) > 0)
        self.assertEqual(result_array[0], item1.tags[0])

    def test_test_data(self):
        match_count = 0
        for record1 in data_list_test:  # 总共 4 个测试items
            item1 = FoobarModel(record1)
            # 至少一个有交集
            common_tags1 = set(recommend_tags(item1)) & set(item1.tags)
            uprint('[common_tags]', common_tags1)
            if common_tags1:
                match_count += 1

        match_rate = match_count / float(len(data_list_test))
        print "[match_rate]", match_rate
        #self.assertTrue(match_rate >= 0.5)

    def test_tags_tree_import_from_file(self):
        tags_tree = tr.tags_tree
        node = TextMulClassify.TMCTree.node

        self.assertEqual(len(tags_tree), 1)
        self.assertEqual(len(tags_tree[tags_tree.root_node][node(u"数与代数")][node(u"集合")][node(u"集合的概念")]), 2)
        self.assertEqual(tags_tree[tags_tree.root_node][node(u"数与代数")][node(u"集合")][node(u"集合的概念")][node(u"集合的含义")], {})

        self.assertTrue(tags_tree.is_exact(u"集合", u"集合"))
        self.assertTrue(tags_tree.is_peer(u"集合", u"函数"))
        self.assertFalse(tags_tree.is_peer(u"集合", u"集合"))
        self.assertTrue(tags_tree.is_peer(u"计算集合元素个数问题", u"元素与集合关系的新定义问题"))

        self.assertTrue(tags_tree.is_child(u"元素与集合关系的新定义问题", u"元素与集合关系的判断"))
        self.assertFalse(tags_tree.is_child(u"元素与集合关系的新定义问题", u"集合", 1))
        self.assertTrue(tags_tree.is_child(u"元素与集合关系的新定义问题", u"集合", 6))
        self.assertFalse(tags_tree.is_parent(u"数与代数", u"元素与集合关系的新定义问题", 1))
        self.assertTrue(tags_tree.is_parent(u"数与代数", u"元素与集合关系的新定义问题", 3))

        self.assertTrue(tags_tree.is_parent(u"二分法求方程的近似解", u"二分法求方程的近似解"))
        self.assertTrue(tags_tree.is_child (u"二分法求方程的近似解", u"二分法求方程的近似解"))

    def test_tags_tree_import_from_dict(self):
        none  = math_tree.__class__.root_node
        i1    = math_tree[none].keys()[0]
        i2    = filter(lambda i1: i1.current_id == 1, math_tree[none][i1].keys())[0]
        i3     = math_tree[none][i1][i2].keys()[0]

        self.assertTrue(none in math_tree)
        self.assertEqual(len(math_tree[none][i1]), 2)
        self.assertTrue(i3 in math_tree[none][i1][i2])
        math_tree.distribution([])

    def test_tags_evaluate(self):
        items = [
            {"original_tags": [u"集合的含义"], "recommend_tags": [u"元素与集合关系的判断", u"二分法求方程的近似解"]},  # peer, umatch
            {"original_tags": [u"集合的含义"], "recommend_tags": [u"集合的含义"]},  # exact
            {"original_tags": [u"元素与集合关系的判断"], "recommend_tags": [u"计算集合元素个数问题", u"元素与集合关系的判断"]},  # child, exact
            {"original_tags": [u"计算集合元素个数问题"], "recommend_tags": [u"元素与集合关系的判断"]},  # parent
        ]
        evaluate = TextMulClassify.Evaluate(math_tree, items)
        # exact | child | parent | peer | unmatch | [total]
        self.assertEqual(evaluate.recall_rates, [50.0, 0.0, 25.0, 25.0, 0.0, 100.0])
        self.assertEqual(evaluate.precision_rates, [33.33, 16.67, 16.67, 16.67, 16.67, 83.34])


if __name__ == '__main__':
    unittest.main()
