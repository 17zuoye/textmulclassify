# -*- coding: utf-8 -*-

from etl_utils import UnicodeUtils
import re
import json


class ReadManualKps():
    """
    示例数据结构是:

    ==========================================
    u'有理数无理数的概念与运算'
    [u'分数指数幂', u'有理数', u'无理数']

    u'二元一次方程组'
    [u'二元一次', u'二元一次方程', u'二元一次方程组', u'加减消元法', u'代入消元法', u'三元一次方程组']
    ==========================================

    输出为键值对。
    """

    def __init__(self, source):
        if "\n" not in source:
            source = UnicodeUtils.read(source)  # 有换行 表示已经读进来了

        self.result = dict()
        current_kp = current_features = None

        for num, line in enumerate(source.split("\n")):
            line = line.strip()
            line = re.sub("'", "\"", line)
            line = re.sub("u\"", "\"", line)

            try:
                current_kp, current_features = self.parse(line, current_kp, current_features)
            except:
                print "[num]", num + 1, "[line]", line
                raise Exception("parse error ...")

            if current_kp and current_features:
                self.result[current_kp] = current_features

    def parse(self, line, current_kp, current_features):
        line = line or " "
        target = None

        if (line[0] == "\"") and (line[-1] == "\""):
            target = 'kp'
        if (line[0] == "[") and (line[-1] == "]"):
            target = 'features'

        if target:
            parsed = json.loads(line)
            if target == 'kp':
                current_kp       = parsed
            if target == 'features':
                current_features = parsed
            return current_kp, current_features
        return None, None

    @classmethod
    def process(cls, source):
        return cls(source).result
