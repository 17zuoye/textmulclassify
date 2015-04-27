# -*- coding: utf-8 -*-

import os, sys, unittest, time
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)


from textmulclassify.lib import ReadManualKps

class TestReadManualKps(unittest.TestCase):

    def test_main(self):
        source = ReadManualKps.__doc__.split("==========================================")[1]
        result = ReadManualKps.process(source)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[u"有理数无理数的概念与运算"], [u'分数指数幂', u'有理数', u'无理数'])

if __name__ == '__main__': unittest.main()
