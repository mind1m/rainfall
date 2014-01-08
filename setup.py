from setuptools import setup

setup(
    name='rainfall',
    version='0.8.3',
    author='Anton Kasyanov',
    author_email='antony.kasyanov@gmail.com',
    packages=['rainfall'],
    url='https://github.com/mind1master/rainfall',
    license="""
    Copyright 2014 Anton Kasyanov


    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations""",
    description='Micro web framework around asyncio (ex tulip)',
    long_description=open('README.txt').read(),
    install_requires=[
        "asyncio",
        "jinja2"
    ],
    test_suite="rainfall.tests",
    keywords = ['asyncio', 'tulip', 'web', 'tornado', 'cyclone', 'python3'],
    classifiers = [
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: Web Environment",
    ],
)