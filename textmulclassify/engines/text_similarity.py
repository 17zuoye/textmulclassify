# -*- coding: utf-8 -*-

from .__base__ import DefaultEngine

from etl_utils import process_notifier, cpickle_cache, uprint, jieba_parse
from collections import Counter, defaultdict
import math


class TextSimilarityEngine(DefaultEngine):
    """ 计算文本相似度 """

    def setup(self):
        self.debug = False

        """ 主要数据结构为 total_tag_to_features__dict , 计算item与tags之间得相似度排序。 """
        self.total_tag_to_features__dict = cpickle_cache(self.classify.cpath('text_engine'),
                                                         self.cache__total_tag_to_features__dict)

        # remove features in stop_unicode_set
        for tag1, features_dict1 in self.total_tag_to_features__dict.iteritems():
            self.filter_by_stop_list(features_dict1)

        self.debug = True

    def call(self, item1, candidates_with_weight=[]):
        text_count1 = self.extract_features_weight(item1)

        tags_to_rank = {tag1: self.similarity(text_count1, self.total_tag_to_features__dict[tag1])
                        for tag1, weight1 in candidates_with_weight}

        return {
            "data": Counter(tags_to_rank).most_common(),
            "detail": {},
        }

    def extract_features_weight(self, item1):
        assert isinstance(item1.item_content, unicode)

        # 没效果
        #segment_features = self.classify.documents_with_segments.get(item1.item_id, None)
        #if not segment_features: segment_features = Counter(jieba_parse(item1.item_content))
        segment_features = Counter({})

        unicode_features = Counter(list(item1.item_content))

        mix_features = segment_features + unicode_features

        self.filter_by_stop_list(mix_features)
        if self.debug:
            uprint("[mix_features]", mix_features)
        return mix_features

    def filter_by_stop_list(self, d1):
        for feature1 in d1.keys():
            if feature1 in stop_unicode_set:
                del d1[feature1]

    def inspect_global_freq(self):
        d1 = defaultdict(int)
        for k1, v1 in self.total_tag_to_features__dict.iteritems():
            for k2, v2 in v1.iteritems():
                d1[k2] += v2
        uprint(Counter(d1).most_common())
        uprint(u''.join([v1[0] for v1 in Counter(d1).most_common()]))

    def cache__total_tag_to_features__dict(self):
        total_tag_to_features__dict = defaultdict(lambda: defaultdict(int))

        # calculate model_cache's freq distribution
        test_item_ids = self.model.test_item_ids()
        for item_id1, item1 in process_notifier(self.model):
            if item_id1 in test_item_ids:
                continue

            item1_features_dict = self.extract_features_weight(item1)

            for tag2 in self.model.tags_model__extract_tags(item1):
                dict3 = total_tag_to_features__dict[tag2]
                for feature4, count4 in item1_features_dict.iteritems():
                    dict3[feature4] += count4

        # remove defaultdict's func
        for k1 in total_tag_to_features__dict.keys():
            total_tag_to_features__dict[k1] = dict(total_tag_to_features__dict[k1])

        return dict(total_tag_to_features__dict)


# vv = uprint([i1 for i1 in Unicode.read((os.path.dirname(os.path.dirname(self.cache_dir)) + '/junior_school_physics/dict_folder/stop_words.dict')).split("\n") if (len(i1) == 1) and Unicode.is_chinese(i1)])
# vv = [uprint(k1, Counter(d1), "\n"*5) for k1, d1 in self.text_similarity.total_tag_to_features__dict.iteritems()]

# vv = uprint(u''.join([v1[0] for v1 in Counter(d1).most_common()]))
stop_unicode_set = set(list(u",的:D数点分是为题式得一可、出中析求个即在用考直于查对时有值"
                            u"则不了与以到故知所如由要此同小选后系确当再这过作成化能及把若"
                            u"已然人果而入称将其么就只也们做你按好还没些哪什着够才往吗很"))
for w1 in u"即可 考查 得到 题意 根据".split(" "):
    stop_unicode_set.add(w1)
