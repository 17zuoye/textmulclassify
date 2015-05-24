# -*- coding: utf-8 -*-

from ..data_structures.tree import TMCTree
from etl_utils import uprint


class Evaluate(object):
    """ 计算多级知识点下的 exact|peer|child|parent 召回率+正确率 """

    def __init__(self, tags_tree, items):
        self.items = items
        for i1 in self.items:
            i1['eval_result'] = []

        # 验证数据结构
        assert isinstance(tags_tree, TMCTree)  # name TODO
        assert isinstance(self.items, list)
        assert 'original_tags' in self.items[0]
        assert 'recommend_tags' in self.items[0]

        self.process(tags_tree, self.items)

    def process(self, tags_tree, items, verbose=False):
        from bunch import Bunch
        total_counts     = Bunch({'original': 0, 'recommend': 0})
        # 对recall来说, recommend_tags对original_tags里的每个tag都可以超过一个匹配，
        # 但是还是按original_tags里排重过的匹配算。
        recall_counts    = Bunch({'exact': 0, 'peer': 0, 'child': 0, 'parent': 0, 'unmatch': 0})
        # 对precision来说，是可以超过多个的，然后 比率 就是直接除以自身全部个数。
        precision_counts = Bunch({'exact': 0, 'peer': 0, 'child': 0, 'parent': 0, 'unmatch': 0})

        def update(obj, method, num):
            setattr(obj, method, (getattr(obj, method) + num))

        for idx1, item1 in enumerate(items):
            if verbose:
                print "\n", "#" * 50, "[process] #", idx1 + 1
            if item1['original_tags']:
                assert isinstance(list(item1['original_tags'])[0],  unicode)
            if item1['recommend_tags']:
                assert isinstance(list(item1['recommend_tags'])[0], unicode)

            original_tags  = set(filter(lambda i1: i1 in tags_tree.name_to_nodes,
                                    item1['original_tags']))  # check valid data
            recommend_tags = set(item1['recommend_tags'])

            total_counts.original  += len(original_tags)
            total_counts.recommend += len(recommend_tags)

            # processed_* 只是为了处理 epcp 依赖的顺序，即前面处理了，后面就没机会了
            processed_original_tags   = set([])
            processed_recommend_tags  = set([])

            def func(counts, is_precision=False):
                if not is_precision:
                    for1, for2 = original_tags, recommend_tags
                else:
                    for2, for1 = original_tags, recommend_tags

                processed = set([])

                for method in ["exact", "peer", "child", "parent"]:
                    match_count = 0

                    for t1 in (for1 - processed):  # 其实核心就是对这一层进行遍历
                        matched_t1 = None
                        for t2 in for2:  # 不需要相减，因为其他recommend_tags还要判定关系
                            n_t1, n_t2 = t2, t1
                            if verbose:
                                print method, "[n_t1]", n_t1, "[n_t2]", n_t2
                            if getattr(tags_tree, "is_" + method)(n_t1, n_t2):
                                if verbose:
                                    print "√"
                                matched_t1 = n_t2
                                break
                        if matched_t1:
                            # 这样在这个循环外部的for循环rt1就没有机会重复计算了
                            processed.add(n_t2)
                            match_count += 1
                    update(counts, method, match_count)
                if verbose:
                    uprint("[processed]", processed)
                counts.unmatch += len(for1 - processed)

                # 计算是否完全没有 召回｜正确
                if len(processed) == 0:
                    text = "no_precision" if is_precision else "no_recall"
                    item1['eval_result'].append(text)

            if verbose:
                print " " * 10, "[recall]    ..."
            func(recall_counts)

            if verbose:
                print " " * 10, "[precision] ..."
            func(precision_counts, is_precision=True)

        print "#" * 100
        print "#" * 100
        print "#" * 100

        def calculate_detail_rates(denominator, molecules):
            def calculate_percent(molecule, denominator):
                return round(((molecule / float(denominator))) * 100, 2)
            rates = [calculate_percent(m1, denominator) for m1 in molecules]
            rates.append(sum(rates[0:-1]))
            return rates

        print "total_counts", repr(total_counts)
        print "recall_counts", repr(recall_counts)
        print "precision_counts", repr(precision_counts)

        self.recall_rates = calculate_detail_rates(total_counts.original,
                [recall_counts.exact, recall_counts.child, recall_counts.parent, recall_counts.peer, recall_counts.unmatch])

        self.precision_rates = calculate_detail_rates(total_counts.recommend,
                [precision_counts.exact, precision_counts.child, precision_counts.parent, precision_counts.peer, precision_counts.unmatch])

        print "exact | child | parent | peer | unmatch | [total]"
        print "召回率", self.recall_rates
        print "正确率", self.precision_rates
