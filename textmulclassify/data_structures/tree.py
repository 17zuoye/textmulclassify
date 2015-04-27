# -*- coding: utf-8 -*-

from etl_utils import UnicodeUtils, process_notifier, uprint, cached_property, slots_with_pickle
from collections import defaultdict, Counter


from bunch import Bunch

# 使用 __slots__ 属性 降低内存使用
# 优化例子: 初高中物理数学内存从 5.6G 降低到 5.0G.
@slots_with_pickle('current_id', 'name', 'parent_id', 'depth', 'features_weight', '_hash')
class Node(object):

    def __init__(self, attrs={}):
        default_attrs = {"current_id": None, "name": u"", "parent_id": None, "depth": 0}
        attrs = dict(default_attrs.items() + attrs.items())
        self.features_weight = dict()

        [setattr(self, k1, v1) for k1, v1 in attrs.iteritems()]
        assert isinstance(self.name, unicode)
        self._hash = hash(u"_".join([unicode(self.current_id or u""), (self.name or u"")]))

    """ 用来保证 每一个node都是唯一的，即使重名的。 """
    def __hash__(self): return self._hash

    def __eq__(self, another):
        assert isinstance(another, Node)
        return hash(self) == hash(another)


class TMCTree(dict):
    """ 多层Tags树，节点为Tag，叶子为空字典 """

    root_node = Node()

    def __init__(self, datasource, line_split="\n", item_split="\t"):
        """ 层级Tag文件必须以 \n 换行，以 \t 标示Tag间层次关系 """
        super(TMCTree, self).__init__()

        # 链接到核心引擎
        self.classify = None # to set it lately

        # 支持Tag递归引用, node.name => [node.parent_id, ...]
        self.child_name_to_parent_relation_dict = defaultdict(set)

        # 支持外部直接用Node的字符串形式查找
        self.name_to_nodes = defaultdict(set)

        self.feature_to_nodes = defaultdict(set)

        def import_from_list(list1):
            # 确保数据结构正确
            assert 'current_id' in list1[0]
            assert 'parent_id'  in list1[0]
            assert 'name'       in list1[0]

            id_to_node__dict   = dict()
            for li in list1:
                node1 = Node(li)
                id_to_node__dict[node1.current_id] = node1
            id_to_node__dict[None] = TMCTree.root_node

            parent_to_children = defaultdict(set)
            for id1, node1 in id_to_node__dict.iteritems():
                if (node1.current_id is None) and (node1.parent_id is None): continue
                parent_to_children[id_to_node__dict[node1.parent_id]].add(node1)

                # 用 node1.name 是兼容跨级同名
                self.child_name_to_parent_relation_dict[node1.name].add(id_to_node__dict[node1.parent_id])
                self.name_to_nodes[node1.name].add(node1)

            assert TMCTree.root_node in parent_to_children

            def add_to_current_tree(current_tree, parent):
                for child in parent_to_children[parent]:
                    child.depth = parent.depth + 1
                    # assert child != parent
                    if child not in current_tree:
                        current_tree[child] = dict()
                    add_to_current_tree(current_tree[child], child)

            self[TMCTree.root_node] = {}
            add_to_current_tree(self[TMCTree.root_node], TMCTree.root_node)

        def import_from_file(file1):
# import_from_file 暂不支持depth
            for line in UnicodeUtils.read(file1).strip().split(line_split):
                line = line.strip()
                if TMCTree.root_node not in self: self[TMCTree.root_node] = dict()
                current_dict = self[TMCTree.root_node]
                parent_node  = TMCTree.root_node
                for current_node in line.split(item_split):
                    current_node = Node({"name":current_node})
                    self.name_to_nodes[current_node.name].add(current_node)
                    if current_node not in current_dict:
                        current_dict[current_node] = dict()

                    self.child_name_to_parent_relation_dict[current_node.name].add(parent_node)
                    current_dict = current_dict[current_node]
                    parent_node  = current_node

        if isinstance(datasource, list):
            import_from_list(datasource)
        elif isinstance(datasource, (str, unicode)):
            import_from_file(datasource)
        else:
            raise Exception(u"datasource 必须是 list 或者 文件名")


    def is_exact(self, recommend_node, target_node):
        """ is recommend_node exact node of target_node. """
        return recommend_node == target_node

    def is_peer(self, recommend_node, target_node):
        """ is recommend_node peer node of target_node. """
        if self.is_exact(recommend_node, target_node): return False
        return bool(self.child_name_to_parent_relation_dict[recommend_node] & \
                    self.child_name_to_parent_relation_dict[target_node])

    def is_child(self, recommend_node, target_node, max_depth=1):
        """ is recommend_node child node of target_node. """
        # NOTE Node.__hash__是基于current_id和name的。但是这边比较是用name比较的。
        assert isinstance(recommend_node, unicode)
        recommend_node = node(recommend_node)
        target_node    = node(target_node)

        # 兼容以下递归
        # "函数的零点与方程的根	二分法求方程的近似解	二分法求方程的近似解"
        # 目前验证实际数据没有跨级递归。
        traversed_nodes = set([])

        _depth    = 0

        def _is_child(child_node1, parent_node1, _depth, yes=False):
            if child_node1.name == TMCTree.root_node.name: return False

            parent_nodes2 = self.child_name_to_parent_relation_dict[child_node1.name]
            # 因为推荐时用的文本，其没有current_id, 故需要对parent_nodes2进行转化
            yes = yes or (parent_node1.name in [p1.name for p1 in parent_nodes2])
            if yes: return True

            traversed_nodes.add(child_node1)

            # 去除递归引用的 任意跨级关系。
            for child_node2 in (parent_nodes2 - traversed_nodes):
                if child_node2 is TMCTree.root_node:
                    continue
                yes = yes or _is_child(child_node2, parent_node1, _depth+1, yes)

            if _depth >= max_depth: return False

            return yes

        return _is_child(recommend_node, target_node, _depth)

    def is_parent(self, recommend_node, target_node, max_depth=1):
        """ is recommend_node parent node of target_node. """
        return self.is_child(target_node, recommend_node, max_depth)

    def has_node(self, node1):
        return node1 in self.child_name_to_parent_relation_dict

    @classmethod
    def node(cls, uname): return Node({"name":uname})

    def lines(self):
        # 1. 生成一行行的从根节点到叶节点
        def extract_root_leaf_line(current_dict, parent_node, lines=[], pre_line=[]):
            pre_line = pre_line or [parent_node]
            for node1 in current_dict:
                sub_pre_line = pre_line + [node1] # make a dup
                if current_dict[node1]:
                    extract_root_leaf_line(current_dict[node1], node1, lines, sub_pre_line)
                else:
                    lines.append(sub_pre_line)
            return lines
        return extract_root_leaf_line(self[self.root_node], self.root_node)

    def distribution(self, tags_list):
        """ 查看知识点树在每条(从根节点到最深叶节点)路径上被引用的分布情况 """
        assert self.name_to_nodes

        lines = self.lines()

        # 2. 计算每个Node被引用次数
        def iter_nodes(lambda1):
            for line1 in lines:
                for node1 in line1: lambda1(node1)
            lambda1(self.root_node)

        def assign_ref_count(node1): node1.ref_count = 0
        iter_nodes(assign_ref_count)

        for tags1 in tags_list:
            for t1 in tags1:
                for node1 in self.name_to_nodes[t1]:
                    node1.ref_count += 1

        marked_nodes_counts_in_lines = []
        for idx1, line1 in enumerate(lines):
            c1 = len(filter(lambda node1: node1.ref_count, line1))
            marked_nodes_counts_in_lines.append(c1)
            print c1, "\t"*2, ', '.join(["\"%s\": %i" % (node1.name, node1.ref_count) \
                                                for node1 in line1[1:]])
        common = Counter(marked_nodes_counts_in_lines).most_common()
        print self.distribution.__doc__, common

        def del_ref_count(node1):
            if 'ref_count' in node1.__dict__:
                del node1.ref_count
        iter_nodes(del_ref_count)

        return common

    def load_features_with_weight(self, tag_to_features_count__dict):
        for tag1, features_counter1 in process_notifier(tag_to_features_count__dict):
            for node1 in self.name_to_nodes[tag1]:
                node1.features_weight = self.classify.calculate_features_weight(features_counter1)

                for f1 in node1.features_weight.keys(): # temp Fix
                    if f1 in self.classify.features_weight_machine.stop_words_set: del node1.features_weight[f1]

                for feature1 in features_counter1: self.feature_to_nodes[feature1].add(node1)
        return self

    def inspect(self, name=None):
        if name == 'name_to_nodes':
            pass

        if name == 'feature_to_nodes':
            pass

        if name == 'features_weight':
            for name1, nodes_set1 in self.name_to_nodes.iteritems():
                for node1 in nodes_set1:
                    uprint(node1.name, Counter(node1.features_weight).most_common(), "\n")

        if name is None: uprint(self)

    def filter_valid_tags(self, tags):
        return list(filter(lambda t1: t1 in self.name_to_nodes, tags))

    @cached_property
    def total_nodes(self):
        return set([node1 for f1, nodes in feature_to_nodes.iteritems() for node1 in nodes])

    def rich_train_data_by_editor(self, files=[]):
        """ 通过人工编辑规则增强Train Data """
        # 20140910_1427 没效果，反而有一两个百分点下降。
        for file1 in files:
            parsed = ReadManualKps.process(dict_dir + file1)
            for node_name1, node_features in parsed.iteritems():
                features2 = [node_name1] + node_features
                # 1. Add features to jieba
                for name2 in features2:
                    jieba.add_word(name2, 1000000) # 1000000 copied from lianhua
                # 2. Add features to tags_tree.name_to_nodes
                nodes_set2 = self.name_to_nodes.get(node_name1, set([]))
                for node3 in nodes_set2:
                    node3_feature_max_value = max(node3.features_weight.values() or [0.25])
                    for feature4 in features2:
                        node3.features_weight[feature4] = node3_feature_max_value
                        self.feature_to_nodes[feature4].add(node3)

    def load__tag_to_words_count__dict(self, model_cache, documents_with_features):
        print "load item_id_to_tags__dict ..."
        item_id_to_tags__dict = { item_id1 : self.filter_valid_tags(model_cache.tags_model__extract_tags(item1)) \
                for item_id1, item1 in process_notifier(model_cache) }

        print "load tag_to_words_count__dict ..."
        tag_to_words_count__dict = defaultdict(lambda : defaultdict(lambda : 0))
        test_item_ids = model_cache.test_item_ids()
        for item_id1, words_count1 in process_notifier(documents_with_features):
            if item_id1 in test_item_ids: continue
            for tag1 in item_id_to_tags__dict[item_id1]:
                for word1, count1 in words_count1.iteritems():
                    tag_to_words_count__dict[tag1][word1] += count1
        return tag_to_words_count__dict

    def fetch_name_ids(self, name1):
        return [node1.current_id for node1 in self.name_to_nodes.get(name1, [])]


node = TMCTree.node
