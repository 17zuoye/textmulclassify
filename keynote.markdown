标题 100 pt
次标题 80 pt
脚注 36 pt
列表 50 pt
列表缩进 15 pt
列表大字 30, 18


# TextMulClassify

背景介绍

# Agenda
1. 预备概率知识
2. 项目架构组织

# 特征分布
从Feature无序的统计意义，知识点推荐 依赖于 文档 中特征(分词) 的分布。


# tfidf
term frequency–inverse document frequency

突出稀缺的 feature。越稀缺，值越大。但是损失了分布信息。

u'一个': 1.492268014669337
u'两个': 1.8366784327552066
u'三个': 3.3369801884738677

缩短词频距离
>>> math.log(10)
2.302585092994046
>>> math.log(10*10000)
11.512925464970229


# entropy
通过某 feature 在不同文档里的概率分布情况得知 该 feature 所携带的信息量。但是却损失了比例信息。

NOTE EntropyFunc 用的是全长度的分布数量，而不是比率，所以出现'一个'比'两个'值更大。
u'一个': 11.246466778408674
u'两个': 10.871699883788001
u'三个': 9.4049779717425626

>>> from scipy.stats import entropy as scipy_entropy
>>> scipy_entropy([1,2,3])
1.0114042647073518
>>> scipy_entropy([2,4,6])
1.0114042647073518


# 某一个feature = tfidf / entropy

通过 把重要信息凸显出来, 比如 "一个"。

# 余弦相似度

>>> from scipy.spatial.distance import cosine
>>> "%6.6f" % (1 - cosine([1,1,1], [1,1,1]))
'1.000000'
>>> "%6.6f" % (1 - cosine([1,1,1], [2,2,2]))
'1.000000'
>>> "%6.6f" % (1 - cosine([1,1,1], [3,6,9]))
'0.925820'
>>> "%6.6f" % (1 - cosine([1,1,1], [3,6,90]))
'0.633328'

# 文本相似度

从 detdup 获取的灵感

朴素贝叶斯

# 其他模型。
信息增益, 讲究的是一个特征在全部和子分类之间的权重区别。
推荐看文本挖掘。


# 分词
1. 基本分词
2. 去除 [一个字，not in [mk, mw], stop words, in ['x','m','eng'], , 长词切碎。

# 目前涉及到的概念
TfIdf, EntropyFunc, Similarity, TextMulClassify, FeaturesWeight(JIEBA),
TMCModel, TMCTree, TextSimilarityEngine, AssociationRuleLearningEngine

# 最终版架构

一张图 + ReadManualKps, Evaluate

DefaultEngine

# 缓存文件
1. ModelCache.db
2. documents_with_segments
3. idf_cache <= [1]
4. entropy_cache <= [1]
5. documents_with_features <= [2,3]
6. tags_tree <= [2,3,4]
7. text_engine

# 实际 API 执行

recommend_tags.func

1. TMCModel instance(包括分词特征)
2. association_rule_learning_engine
3. text_similarity_engine( 2. )
4. 线性加权


# 最后合并为一个进程

[`juniorschool_math`, `juniorschool_physics`, `highschool_math`, `highschool_physics`]
+ share JIEBA 400 MB

# 一些优化
slots_with_pickle Node
