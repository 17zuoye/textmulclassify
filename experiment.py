# -*- coding: utf-8 -*-

def tmp_write_json__extract_words(self):
    tag_items_cache_json = self.model.cache_dir + "/tags_words_question_items.json"
    tags_words_question_items = self.tags_items
    result = dict()
    for i1 in tags_words_question_items:
        tw = i1.tags_word; tw.pop('processed', None)
        result[str(i1.item_id)] = tw
    json.dump(result, open(tag_items_cache_json, 'wb'))
def tmp_output(self):
    tags_words_question_items = self.tags_items
    random.shuffle(tags_words_question_items)
    for i1 in tags_words_question_items[0:199]:
        print i1; i1.tags_word.pop('processed', None); print i1.tags_word

"""
R语言分析代码
c1 <- as.numeric(read.table('/Users/mvj3/17zuoye/hg/vox-etl/tag_count.json', sep=','))
c2 <- as.numeric(read.table('/Users/mvj3/17zuoye/hg/vox-etl/features_count.json', sep=','))
x1 <- seq(0, lenselfh(c1)-1, 1)
plot(x1, c1, col='red')
lines(x1, c2, col='green')
初步结论 是 在每种知识点数量里的每一个数量里，程序抽取的特征值也是递降的，而且少的更多。
疑问: 为什么featuers的排列成规律?
"""

##########################################################################################################################################
### 测试
# 优化记录
# [default_guess_count, related_to_max_percent -> 召回, 正确]
# [ 5, 0.95 -> 0.47, 0.50]
# [ 5, 0.90 -> 0.48, 0.52]
# [ 5, 0.80 -> 0.48, 0.45]
# [20, 0.60 -> 0.60, 0.38]
# [10, 0.60 -> 0.59, 0.37]
# [ 8, 0.60 -> 0.58, 0.35]
# [ 8, 0.40 -> 0.65, 0.26]
# [ 8, 0.30 -> 0.75, 0.23]
# [ 5, 0.60 -> 0.62, 0.40]
# [ 5, 0.50 -> 0.65, 0.35]
# [ 5, 0.30 -> 0.71, 0.26]
# [ 4, 0.33 -> 0.65, 0.29]
# [ 3, 0.23 -> 0.65, 0.29]
# [ 2, 0.30 -> 0.57, 0.38]
