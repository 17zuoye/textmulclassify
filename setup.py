# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='textmulclassify',
    version='0.1.0',
    url='http://github.com/17zuoye/textmulclassify/',
    license='MIT',
    authors=['David Chen', 'Lianhua Li', 'Junchen Feng', 'Heng Li', ],
    author_email=''.join(reversed("moc.liamg@emojvm")),
    description='textmulclassify',
    long_description='textmulclassify',
    packages=['textmulclassify'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'etl_utils >= 0.1.10',
        'tfidf >= 0.0.6',
        'termcolor',
        'model_cache >=0.1.0',
        'jieba',
        "urwid",
        "bunch",
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
