# -*- coding:utf-8 -*-
##############################################################
# Created Date: Friday, March 1st 2024
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import pytest
from grid2demand.func_lib.read_node_poi import read_node


def test_read_node_non_existing_file():
    # Test case for a non-existing node file
    with pytest.raises(FileNotFoundError):
        read_node(node_file="path/to/non_existing_node_file.csv")
