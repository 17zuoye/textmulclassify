TextMulClassify
===================================================
[![Build Status](https://img.shields.io/travis/17zuoye/textmulclassify/master.svg?style=flat)](https://travis-ci.org/17zuoye/textmulclassify)
[![Coverage Status](https://coveralls.io/repos/17zuoye/textmulclassify/badge.svg)](https://coveralls.io/r/17zuoye/textmulclassify)
[![Health](https://landscape.io/github/17zuoye/textmulclassify/master/landscape.svg?style=flat)](https://landscape.io/github/17zuoye/textmulclassify/master)
[![Download](https://img.shields.io/pypi/dm/textmulclassify.svg?style=flat)](https://pypi.python.org/pypi/textmulclassify)
[![License](https://img.shields.io/pypi/l/textmulclassify.svg?style=flat)](https://pypi.python.org/pypi/textmulclassify)
[![Python Versions](https://pypip.in/py_versions/textmulclassify/badge.svg?style=flat)](https://pypi.python.org/pypi/textmulclassify)


为给定的一段文本抽取一个或多个基于知识树的标签。

Project Structure
------------------------------------
```txt
textmulclassify/
  ▾ data_structures/
      __init__.py
      model.py
      tree.py
  ▾ engines/
      __base__.py
      __init__.py
      association_rule_learning.py
      text_similarity.py
  ▾ lib/
      __init__.py
      entropy.py
      evaluate.py
      features_weight.py
      read_manual_kps.py
      similarity.py
    __init__.py
    classify.py
```

项目细节
------------------------------------
目前还没有整理出项目架构和细节，部分零碎的项目讲解见 https://github.com/17zuoye/textmulclassify/blob/master/keynote_speech.markdown


运行测试
------------------------------------
```bash
pip install tox
tox
```

License
------------------------------------
MIT. David Chen @ 17zuoye
