# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, September 28th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import os
import pandas as pd
from grid2demand.utils_lib.pkg_settings import required_files
from grid2demand.utils_lib.net_utils import Node, POI, Zone, Agent
from grid2demand.utils_lib.utils import (get_filenames_from_folder_by_type,
                                         check_required_files_exist,
                                         gen_unique_filename,
                                         path2linux)
from grid2demand.func_lib.read_node_poi import read_node, read_poi, read_network
from grid2demand.func_lib.gen_zone import (net2zone,
                                           sync_zone_and_node_geometry,
                                           sync_zone_and_poi_geometry,
                                           calc_zone_od_matrix)
from grid2demand.func_lib.trip_rate_production_attraction import (gen_poi_trip_rate,
                                                                  gen_node_prod_attr)
from grid2demand.func_lib.gravity_model import run_gravity_model
from grid2demand.func_lib.gen_agent_demand import gen_agent_based_demand


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

    def read_node(self, path_node: str = "") -> dict[int, Node]:
        if not path_node:
            path_node = self.path_node

        if not os.path.exists(path_node):
            raise Exception(f"Error: File {path_node} does not exist.")

        self.node_dict = read_node(path_node)
        return self.node_dict

    def read_poi(self, path_poi: str = "") -> dict[int, POI]:
        if not path_poi:
            path_poi = self.path_poi

        if not os.path.exists(path_poi):
            raise Exception(f"Error: File {path_poi} does not exist.")

        self.poi_dict = read_poi(path_poi)
        return self.poi_dict

    def read_network(self, input_dir: str = "") -> dict[str, dict]:
        if not input_dir:
            input_dir = self.input_dir

        if not os.path.isdir(input_dir):
            raise Exception(f"Error: Input directory {input_dir} does not exist.")
        network_dict = read_network(input_dir)
        self.node_dict = network_dict.get('node_dict')
        self.poi_dict = network_dict.get('poi_dict')
        return network_dict

    def net2zone(self, node_dict: dict[int, Node], num_x_blocks: int = 10, num_y_blocks: int = 10,
                 cell_width: float = 0, cell_height: float = 0) -> dict[int, Zone]:
        self.zone_dict = net2zone(node_dict, num_x_blocks, num_y_blocks, cell_width, cell_height)
        return self.zone_dict

    def sync_geometry_between_zone_and_node_poi(self, zone_dict: dict = "", node_dict: dict = "", poi_dict: dict = "") -> list[dict]:
        pass

    def calc_zone_od_distance_matrix(self, zone_dict: dict = "") -> dict:
        pass

    def gen_poi_trip_rate(self, poi_dict: dict = "", trip_rate_file: str = "", trip_purpose: int = 1) -> dict[int, POI]:
        pass

    def gen_node_prod_attr(self, node_dict: dict = "", poi_trip_rate: dict = "") -> dict[int, Node]:
        pass

    def run_gravity_model(self, node_prod_attr: dict = "", zone_dict: dict = "", zone_od_matrix: dict = "") -> pd.DataFrame:
        pass

    def gen_agent_based_demand(self, node_prod_attr: dict = "", zone_dict: dict = "", df_demand: pd.DataFrame = "") -> pd.DataFrame:
        pass

    def save_demand(self, df_demand: pd.DataFrame, output_dir: str = "") -> None:
        pass

    def save_agent(self, df_agent: pd.DataFrame, output_dir: str = "") -> None:
        pass