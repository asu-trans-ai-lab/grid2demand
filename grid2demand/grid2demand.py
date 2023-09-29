# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, September 28th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import os
import pandas as pd
from grid2demand.utils_lib.pkg_settings import required_files
from grid2demand.utils_lib.utils import (get_filenames_from_folder_by_type,
                                         check_required_files_exist,
                                         gen_unique_filename,
                                         path2linux)
from grid2demand.func_lib.read_node_poi import read_node, read_poi


class GRID2DEMAND:

    def __init__(self, input_dir: str) -> None:
        self.input_dir = path2linux(input_dir)


        # check input directory
        self.check_input_dir()

    def check_input_dir(self) -> None:
        if not os.path.exists(self.input_dir):
            raise Exception("Error: Input directory does not exist.")

        # check required files in input directory
        dir_files = get_filenames_from_folder_by_type(self.input_dir, "csv")
        is_required_files_exist = check_required_files_exist(required_files, dir_files)
        if not is_required_files_exist:
            raise Exception(f"Error: Required files are not satisfied. Please check {required_files} in {self.input_dir}.")

        self.path_node = os.path.join(self.input_dir, "node.csv")
        self.path_poi = os.path.join(self.input_dir, "poi.csv")

    def read_node(self, path_node: str = "") -> pd.DataFrame:
        if not path_node:
            path_node = self.path_node
        return
