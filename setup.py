# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, December 28th 2020
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import setuptools

with open("README_pkg.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

try:
    # if have requirements.txt file inside the folder
    with open("requirements.txt", "r", encoding="utf-8") as f:
        modules_needed = [i.strip() for i in f.readlines()]
except Exception:
    modules_needed = []

setuptools.setup(
    name="grid2demand",  # Replace with your own username
    version="0.4.3",
    author="Xiangyong Luo, Dr.Xuesong(Simon) Zhou, Anjun Li, Entai Wang, Taehooie Kim",
    author_email="luoxiangyong01@gmail.com, xzhou74@asu.edu",
    description="A tool for generating zone-to-zone travel demand based on grid zones and gravity model",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xyluo25/grid2demand",

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    install_requires=modules_needed,

    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={'': ['*.txt', '*.xls', '*.xlsx', '*.csv'],
                  "test_data": ['*.xls']},
    project_urls={
        'Homepage': 'https://github.com/asu-trans-ai-lab/grid2demand',
        'Documentation': 'https://github.com/asu-trans-ai-lab/grid2demand',
        # 'Bug Tracker': '',
        # 'Source Code': '',
        # 'Download': '',
        # 'Publication': '',
        # 'Citation': '',
        # 'License': '',
        # 'Acknowledgement': '',
        # 'FAQs': '',
        # 'Contact': '',
    }
)