# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, September 28th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import os
import pandas as pd
from grid2demand.utils_lib.pkg_settings import pkg_settings
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
from grid2demand.func_lib.gravity_model import run_gravity_model, calc_zone_production_attraction
from grid2demand.func_lib.gen_agent_demand import gen_agent_based_demand


class GRID2DEMAND:

    def __init__(self, path_dir: str) -> None:
        self.path_dir = path2linux(path_dir)

        # check input directory
        self.__check_input_dir()
        self.__load_pkg_settings()

    def __check_input_dir(self) -> None:
        """check input directory

        Raises:
            NotADirectoryError: Error: Input directory _path_dir_ does not exist.
            Exception: Error: Required files are not satisfied. Please check _required_files_ in _path_dir_.

        Returns:
            None: will generate self.path_node and self.path_poi for class instance.
        """
        if not os.path.exists(self.path_dir):
            raise NotADirectoryError(f"Error: Input directory {self.path_dir} does not exist.")

        # check required files in input directory
        dir_files = get_filenames_from_folder_by_type(self.path_dir, "csv")
        required_files = pkg_settings.get("required_files")
        is_required_files_exist = check_required_files_exist(required_files, dir_files)
        if not is_required_files_exist:
            raise Exception(f"Error: Required files are not satisfied. Please check {required_files} in {self.path_dir}.")

        self.path_node = os.path.join(self.path_dir, "node.csv")
        self.path_poi = os.path.join(self.path_dir, "poi.csv")

    def __load_pkg_settings(self) -> None:
        self.pkg_setting = pkg_settings

    def read_node(self, path_node: str = "") -> dict[int, Node]:
        """read node.csv file and return node_dict

        Args:
            path_node (str, optional): the path to node.csv. Defaults to "". if not specified, use self.path_node.

        Raises:
            FileNotFoundError: Error: File {path_node} does not exist.

        Returns:
            dict[int, Node]: node_dict {node_id: Node}

        Examples:
            >>> from grid2demand import GRID2DEMAND
            >>> gd = GRID2DEMAND(path_dir)
            >>> node_dict = gd.read_node()
            >>> node_dict[1]
            Node(id=1, x_coord=121.469, y_coord=31.238, production=0, attraction=0,
            boundary_flag=0, zone_id=-1, poi_id=-1, activity_type= '',
            activity_location_tab='', geometry='POINT (121.469 31.238)'
        """

        if not path_node:
            path_node = self.path_node

        if not os.path.exists(path_node):
            raise FileNotFoundError(f"Error: File {path_node} does not exist.")

        self.node_dict = read_node(path_node)
        return self.node_dict

    def read_poi(self, path_poi: str = "") -> dict[int, POI]:
        """read poi.csv file and return poi_dict

        Args:
            path_poi (str, optional): the path to poi.csv. Defaults to "". if not specified, use self.path_poi.

        Raises:
            FileExistsError: Error: File {path_poi} does not exist.

        Returns:
            dict[int, POI]: poi_dict {poi_id: POI}
        """

        if not path_poi:
            path_poi = self.path_poi

        if not os.path.exists(path_poi):
            raise FileExistsError(f"Error: File {path_poi} does not exist.")

        self.poi_dict = read_poi(path_poi)
        return self.poi_dict

    def read_network(self, input_dir: str = "") -> dict[str, dict]:
        """read node.csv and poi.csv and return network_dict

        Args:
            input_dir (str, optional): the input directory that include required files. Defaults to "".
                                       if not specified, use self.input_dir.

        Raises:
            FileExistsError: Error: Input directory {input_dir} does not exist.

        Returns:
            dict[str, dict]: network_dict {node_dict: dict[int, Node], poi_dict: dict[int, POI]}
        """

        if not input_dir:
            input_dir = self.input_dir

        if not os.path.isdir(input_dir):
            raise FileExistsError(f"Error: Input directory {input_dir} does not exist.")
        network_dict = read_network(input_dir)
        self.node_dict = network_dict.get('node_dict')
        self.poi_dict = network_dict.get('poi_dict')
        return network_dict

    def net2zone(self, node_dict: dict[int, Node], num_x_blocks: int = 10, num_y_blocks: int = 10,
                 cell_width: float = 0, cell_height: float = 0, unit: str = "km") -> dict[str, Zone]:
        """convert node_dict to zone_dict by grid.
        The grid can be defined by num_x_blocks and num_y_blocks, or cell_width and cell_height.
        if num_x_blocks and num_y_blocks are specified, the grid will be divided into num_x_blocks * num_y_blocks.
        if cell_width and cell_height are specified, the grid will be divided into cells with cell_width * cell_height.
        Note: num_x_blocks and num_y_blocks have higher priority to cell_width and cell_height.
              if num_x_blocks and num_y_blocks are specified, cell_width and cell_height will be ignored.

        Args:
            node_dict (dict[int, Node]): node_dict {node_id: Node}
            num_x_blocks (int, optional): total number of blocks/grids from x direction. Defaults to 10.
            num_y_blocks (int, optional): total number of blocks/grids from y direction. Defaults to 10.
            cell_width (float, optional): the width for each block/grid . Defaults to 0. unit: km.
            cell_height (float, optional): the height for each block/grid. Defaults to 0. unit: km.
            unit (str, optional): the unit of cell_width and cell_height. Defaults to "km".

        Returns:
            dict[str, Zone]: zone_dict {zone_name: Zone}
        """

        self.zone_dict = net2zone(node_dict, num_x_blocks, num_y_blocks, cell_width, cell_height, unit)
        return self.zone_dict

    def sync_geometry_between_zone_and_node_poi(self, zone_dict: dict = "",
                                                node_dict: dict = "", poi_dict: dict = "") -> dict[str, dict]:
        """synchronize geometry between zone and node/poi.

        Args:
            zone_dict (dict, optional): zone dict generated from net2zone. Defaults to "".
                if not specified, use self.zone_dict.
            node_dict (dict, optional): the node_dict generated from read_node/read_network. Defaults to "".
                if not specified, use self.node_dict.
            poi_dict (dict, optional): the poi_dict generated from read_poi/read_network. Defaults to "".
                if not specified, use self.poi_dict.

        Raises:
            Exception: Error in running _function_name_: not valid zone_dict or node_dict
            Exception: Error in running _function_name_: not valid zone_dict or poi_dict

        Returns:
            dict[str, dict]: {"zone_dict": self.zone_dict, "node_dict": self.node_dict, "poi_dict": self.poi_dict}
        """

        # if not specified, use self.zone_dict, self.node_dict, self.poi_dict as input
        if not all([zone_dict, node_dict, poi_dict]):
            zone_dict = self.zone_dict
            node_dict = self.node_dict
            poi_dict = self.poi_dict

        # synchronize zone with node
        try:
            zone_node_dict = sync_zone_and_node_geometry(zone_dict, node_dict)
            zone_dict_add_node = zone_node_dict.get('zone_dict')
            self.node_dict = zone_node_dict.get('node_dict')
        except Exception as e:
            raise Exception(
                f"Error in running {self.sync_geometry_between_zone_and_node_poi.__name__}: \
                  not valid zone_dict or node_dict"
            ) from e

        # synchronize zone with poi
        try:
            zone_poi_dict = sync_zone_and_poi_geometry(zone_dict_add_node, poi_dict)
            self.zone_dict = zone_poi_dict.get('zone_dict')
            self.poi_dict = zone_poi_dict.get('poi_dict')
        except Exception as e:
            raise Exception(
                f"Error in running {self.sync_geometry_between_zone_and_node_poi.__name__}: \
                  not valid zone_dict or poi_dict"
            ) from e
        return {"zone_dict": self.zone_dict, "node_dict": self.node_dict, "poi_dict": self.poi_dict}

    def calc_zone_od_distance_matrix(self, zone_dict: dict = "") -> dict[tuple, float]:
        """calculate zone-to-zone od distance matrix

        Args:
            zone_dict (dict, optional): the zone dictionary. Defaults to "".
                if not specified, use self.zone_dict.

        Returns:
            dict[tuple, float]: zone_od_matrix {(zone_id1, zone_id2): distance}
        """

        # if not specified, use self.zone_dict as input
        if not zone_dict:
            zone_dict = self.zone_dict

        self.zone_od_dist_matrix = calc_zone_od_matrix(zone_dict)
        return self.zone_od_dist_matrix

    def gen_poi_trip_rate(self, poi_dict: dict = "", trip_rate_file: str = "", trip_purpose: int = 1) -> dict[int, POI]:
        """generate poi trip rate for each poi

        Args:
            poi_dict (dict, optional): the poi dictionary. Defaults to "".
                if not specified, use self.poi_dict.
            trip_rate_file (str, optional): the path to trip rate file. Defaults to "".
                if not specified, use self.trip_rate_file.
            trip_purpose (int, optional): the trip purpose. Defaults to 1.

        Returns:
            dict[int, POI]: poi_dict {poi_id: POI}
        """

        # if not specified, use self.poi_dict as input
        if not poi_dict:
            poi_dict = self.poi_dict

        self.poi_dict = gen_poi_trip_rate(poi_dict, trip_rate_file, trip_purpose)
        return self.poi_dict

    def gen_node_prod_attr(self, node_dict: dict = "", poi_dict: dict = "") -> dict[int, Node]:
        """generate production and attraction for each node based on poi trip rate

        Args:
            node_dict (dict, optional): Defaults to "". if not specified, use self.node_dict.
            poi_dict (dict, optional): Defaults to "". if not specified, use self.poi_dict.

        Returns:
            dict[int, Node]: the updated node_dict {node_id: Node}
        """

        if not all([node_dict, poi_dict]):
            node_dict = self.node_dict
            poi_dict = self.poi_dict

        self.node_dict = gen_node_prod_attr(node_dict, poi_dict)
        return self.node_dict

    def calc_zone_production_attraction(self, node_dict: dict = "", zone_dict: dict = "") -> dict[str, Zone]:
        """calculate zone production and attraction based on node production and attraction

        Args:
            node_dict (dict, optional): Defaults to "". if not specified, use self.node_dict.
            zone_dict (dict, optional): Defaults to "". if not specified, use self.zone_dict.

        Returns:
            dict[str, Zone]: the updated zone_dict {zone_name: Zone}
        """
        if not all([node_dict, zone_dict]):
            node_dict = self.node_dict
            zone_dict = self.zone_dict
        self.zone = calc_zone_production_attraction(node_dict, zone_dict)
        return self.zone

    def run_gravity_model(self, zone_dict: dict = "",
                          zone_od_dist_matrix: dict = "",
                          trip_purpose: int = 1,
                          alpha: float = 28507,
                          beta: float = -0.02,
                          gamma: float = -0.123) -> pd.DataFrame:
        """run gravity model to generate demand

        Args:
            zone_dict (dict, optional): _description_. Defaults to "".
            zone_od_dist_matrix (dict, optional): _description_. Defaults to "".
            trip_purpose (int, optional): _description_. Defaults to 1.
            alpha (float, optional): _description_. Defaults to 28507.
            beta (float, optional): _description_. Defaults to -0.02.
            gamma (float, optional): _description_. Defaults to -0.123.

        Returns:
            pd.DataFrame: the final demand dataframe
        """
        if not all([zone_dict, zone_od_dist_matrix]):
            zone_dict = self.zone_dict
            zone_od_dist_matrix = self.zone_od_dist_matrix

        self.df_demand = run_gravity_model(zone_dict, zone_od_dist_matrix)
        return self.df_demand

    def gen_agent_based_demand(self, node_dict: dict = "", zone_dict: dict = "",
                               df_demand: pd.DataFrame = "") -> pd.DataFrame:
        """generate agent-based demand

        Args:
            node_dict (dict, optional): _description_. Defaults to "".
            zone_dict (dict, optional): _description_. Defaults to "".
            df_demand (pd.DataFrame, optional): _description_. Defaults to "".

        Returns:
            pd.DataFrame: the final agent-based demand dataframe
        """
        if not all([node_dict, zone_dict, df_demand]):
            node_dict = self.node_dict
            zone_dict = self.zone_dict
            df_demand = self.df_demand

        self.df_agent = gen_agent_based_demand(node_dict, zone_dict, df_demand)
        return self.df_agent

    def save_demand(self, output_dir: str = "") -> None:
        if not output_dir:
            output_dir = self.path_dir

        if not hasattr(self, "df_demand"):
            print("Error: df_demand does not exist. Please run run_gravity_model() first.")

        path_output = gen_unique_filename(path2linux(os.path.join(output_dir, "demand.csv")))
        self.df_demand.to_csv(path_output, index=False)

    def save_agent(self, output_dir: str = "") -> None:
        if not output_dir:
            output_dir = self.path_dir

        if not hasattr(self, "df_agent"):
            print("Error: df_agent does not exist. Please run gen_agent_based_demand() first.")

        path_output = gen_unique_filename(path2linux(os.path.join(output_dir, "agent.csv")))
        self.df_agent.to_csv(path_output, index=False)
