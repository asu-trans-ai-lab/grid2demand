# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, September 28th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import os
from itertools import combinations
import pandas as pd
import contextlib
import shapely
from grid2demand.utils_lib.pkg_settings import pkg_settings
from grid2demand.utils_lib.net_utils import (Node,
                                             POI,
                                             Zone,
                                             Agent)
from grid2demand.utils_lib.utils import check_required_files_exist

from grid2demand.func_lib.read_node_poi import (read_node,
                                                read_poi,
                                                read_network,
                                                read_zone_by_geometry,
                                                read_zone_by_centroid)
from grid2demand.func_lib.gen_zone import (net2zone,
                                           sync_zone_geometry_and_node,
                                           sync_zone_geometry_and_poi,
                                           sync_zone_centroid_and_node,
                                           sync_zone_centroid_and_poi,
                                           calc_zone_od_matrix)
from grid2demand.func_lib.trip_rate_production_attraction import (gen_poi_trip_rate,
                                                                  gen_node_prod_attr)
from grid2demand.func_lib.gravity_model import (run_gravity_model,
                                                calc_zone_production_attraction)
from grid2demand.func_lib.gen_agent_demand import gen_agent_based_demand

from pyufunc import (path2linux,
                     get_filenames_by_ext,
                     cvt_int_to_alpha,
                     generate_unique_filename)


class GRID2DEMAND:

    def __init__(self,
                 input_dir: str = "",
                 *,
                 node_file: str = "",
                 poi_file: str = "",
                 zone_file: str = "",
                 num_x_blocks: int = 10,
                 num_y_blocks: int = 10,
                 cell_width: float = 0,
                 cell_height: float = 0,
                 unit: str = "km",
                 trip_rate_file: str = "",
                 trip_purpose: int = 1,
                 alpha: float = 28507,
                 beta: float = -0.02,
                 gamma: float = -0.123,
                 output_dir: str = "",
                 use_zone_id: bool = False,
                 node_as_zone_centroid: bool = False,
                 verbose: bool = False) -> None:
        """initialize GRID2DEMAND object

        Args:
            input_dir (str, optional): input directory of your data. Defaults to "".
            output_dir (str, optional): output directory. Defaults to "".
            use_zone_id (bool, optional): whether to use zone_id from node.csv. Defaults to False.
            verbose (bool, optional): print processing message. Defaults to False.
        """

        # initialize input parameters
        self.input_dir = path2linux(input_dir) if input_dir else ""
        self.node_file = path2linux(node_file) if node_file else ""
        self.poi_file = path2linux(poi_file) if poi_file else ""
        self.zone_file = path2linux(zone_file) if zone_file else ""
        self.num_x_blocks = num_x_blocks
        self.num_y_blocks = num_y_blocks
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.unit = unit
        self.trip_rate_file = path2linux(trip_rate_file) if trip_rate_file else ""
        self.trip_purpose = trip_purpose
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        # # if not specified inputs, use current working directory as input directory
        # if not any([input_dir, node_file, poi_file]):
        #     self.input_dir = path2linux(os.getcwd())
        #     print(f"  : Input directory is not specified. Use current working directory {self.input_dir} as input directory. Please make sure node.csv and poi.csv are in {self.input_dir}.")

        # initialize output parameters
        # if specified output directory, use it as output directory
        # else, check whether input directory exists,
        # if input directory exists, use it as output directory
        # else, use current working directory as output directory

        if output_dir:
            self.output_dir = path2linux(output_dir)
        elif os.path.isdir(self.input_dir):
            self.output_dir = self.input_dir
        else:
            self.output_dir = path2linux(os.getcwd())

        self.verbose = verbose
        self.use_zone_id = use_zone_id

        # load default package settings,
        # user can modify the settings before running the model
        self.__load_pkg_settings()

        # if use_zone_id is True, this parameter will be implemented
        self.node_as_zone_centroid = node_as_zone_centroid

        # # check input directory if specified input directory
        if self.input_dir:
            self.__check_input_dir()

        # set default zone in geometry or centroid as False
        self.is_geometry = False
        self.is_centroid = False

        # set default poi_trip_rate, node_prod_attr, zone_prod_attr as False
        self.is_poi_trip_rate = False
        self.is_node_prod_attr = False
        self.is_zone_prod_attr = False
        self.is_zone_od_dist_matrix = False
        self.is_sync_geometry = False

    def __check_input_dir(self) -> None:
        """check input directory

        Raises:
            NotADirectoryError: Error: Input directory _input_dir_ does not exist.
            Exception: Error: Required files are not satisfied. Please check _required_files_ in _input_dir_.

        Returns:
            None: will generate self.path_node and self.path_poi for class instance.
        """

        if self.verbose:
            print("  : Checking input directory...")
        if not os.path.isdir(self.input_dir):
            raise NotADirectoryError(f"Error: Input directory {self.input_dir} does not exist.")

        # check required files in input directory
        dir_files = get_filenames_by_ext(self.input_dir, "csv")
        required_files = self.pkg_settings.get("required_files", [])

        is_required_files_exist = check_required_files_exist(required_files, dir_files, verbose=self.verbose)
        if not is_required_files_exist:
            raise Exception(f"Error: Required files are not satisfied. Please check {required_files} in {self.input_dir}.")

        self.node_file = path2linux(os.path.join(self.input_dir, "node.csv"))
        self.poi_file = path2linux(os.path.join(self.input_dir, "poi.csv"))

        # check optional files in input directory (zone.csv)
        optional_files = self.pkg_settings.get("optional_files", [])
        is_optional_files_exist = check_required_files_exist(optional_files, dir_files, verbose=False)

        if is_optional_files_exist:
            print(f"  : Optional file: {optional_files} found in {self.input_dir}.")
            print("  : Optional files could be used in the future steps.")
            self.zone_file = path2linux(os.path.join(self.input_dir, "zone.csv"))

        if self.verbose:
            print("  : Input directory is valid.\n")

    def __load_pkg_settings(self) -> None:
        if self.verbose:
            print("  : Loading default package settings...")
        self.pkg_settings = pkg_settings

        # add zone_id to node_dict if use_zone_id is True
        if self.use_zone_id and "zone_id" not in self.pkg_settings["node_fields"]:
            self.pkg_settings["node_fields"].append("zone_id")

        if self.verbose:
            print("  : Package settings loaded successfully.\n")

    def load_node(self, node_file: str = "") -> dict[int, Node]:
        """read node.csv file and return node_dict

        Raises:
            FileNotFoundError: Error: File {path_node} does not exist.

        Returns:
            dict[int, Node]: node_dict {node_id: Node}

        Examples:
            >>> from grid2demand import GRID2DEMAND
            >>> gd = GRID2DEMAND(input_dir)
            >>> node_dict = gd.load_node
            >>> node_dict[1]
            Node(id=1, x_coord=121.469, y_coord=31.238, production=0, attraction=0,
            is_boundary=0, zone_id=-1, poi_id=-1, activity_type= '', geometry='POINT (121.469 31.238)'
        """

        # update node_file if specified
        if node_file:
            self.node_file = path2linux(node_file)

        if not os.path.exists(self.node_file):
            raise FileNotFoundError(f"Error: File {self.node_file} does not exist.")

        self.node_dict = read_node(self.node_file, self.pkg_settings.get("set_cpu_cores"), verbose=self.verbose)

        # generate node_zone_pair {node_id: zone_id} for later use
        # the zone_id based on node.csv in field zone_id

        # create zone.csv if use_zone_id is True
        if self.use_zone_id:

            # zone columns in zone.csv
            _col = ["zone_id", "x_coord", "y_coord"]

            # get values from node_dict
            _val_list = []
            _node_and_zone_id = []  # store node_id that is zone
            self._node_is_zone = {}  # store node

            for node_id in self.node_dict:
                if self.node_dict[node_id]._zone_id != -1:
                    _val_list.append([self.node_dict[node_id]._zone_id,
                                      self.node_dict[node_id].x_coord,
                                      self.node_dict[node_id].y_coord])

                    _node_and_zone_id.append(node_id)

            # delete zone from node_dict
            for node_id in _node_and_zone_id:
                self._node_is_zone[node_id] = self.node_dict[node_id]
                del self.node_dict[node_id]

            _zone_df = pd.DataFrame(_val_list, columns=_col)
            self.zone_file = path2linux(os.path.join(self.input_dir, "zone.csv"))
            _zone_df.to_csv(self.zone_file, index=False)
            print(f"  : zone.csv is generated (use_zone_id = True) based on node.csv in {self.input_dir}.")

        self.__pair_node_zone_id = {
            node_id: self.node_dict[node_id]._zone_id
            for node_id in self.node_dict
            if self.node_dict[node_id]._zone_id != -1
        }

        return self.node_dict

    def load_poi(self, poi_file: str = "") -> dict[int, POI]:
        """read poi.csv file and return poi_dict

        Raises:
            FileExistsError: Error: File {path_poi} does not exist.

        Returns:
            dict[int, POI]: poi_dict {poi_id: POI}
        """

        # update poi_file if specified
        if poi_file:
            self.poi_file = path2linux(poi_file)

        if not os.path.exists(self.poi_file):
            raise FileExistsError(f"Error: File {self.poi_file} does not exist.")

        self.poi_dict = read_poi(self.poi_file, self.pkg_settings.get("set_cpu_cores"), verbose=self.verbose)
        return self.poi_dict

    def load_network(self,
                     *,
                     input_dir: str = "",
                     node_file: str = "",
                     poi_file: str = "",
                     return_value: bool = False) -> dict[str, dict]:
        """read node.csv and poi.csv and return network_dict

        Raises:
            FileExistsError: Error: Input directory {input_dir} does not exist.

        Returns:
            dict[str, dict]: network_dict {node_dict: dict[int, Node], poi_dict: dict[int, POI]}
        """

        # update input_dir, node_file, poi_file if specified
        if input_dir:
            self.input_dir = path2linux(input_dir)

        if node_file:
            self.node_file = path2linux(node_file)

        if poi_file:
            self.poi_file = path2linux(poi_file)

        # check input directory
        if self.input_dir and not os.path.isdir(self.input_dir):
            raise FileExistsError(f"Error: Input directory {self.input_dir} does not exist.")

        # read node.csv and poi.csv from input directory
        if not self.input_dir:
            raise Exception("Error: Input directory is not specified. Please specify input directory.")

        self.__check_input_dir()
        self.node_dict = self.load_node()
        self.poi_dict = self.load_poi()

        return {"node_dict": self.node_dict, "poi_dict": self.poi_dict} if return_value else None

    def net2zone(self,
                 node_dict: dict[int, Node] = {},
                 *,
                 num_x_blocks: int = 10,
                 num_y_blocks: int = 10,
                 cell_width: float = 0,
                 cell_height: float = 0,
                 unit: str = "km",
                 return_value: bool = False) -> dict[str, Zone]:
        """convert node_dict to zone_dict by grid.
        The grid can be defined by num_x_blocks and num_y_blocks, or cell_width and cell_height.
        if num_x_blocks and num_y_blocks are specified, the grid will be divided into num_x_blocks * num_y_blocks.
        if cell_width and cell_height are specified, the grid will be divided into cells with cell_width * cell_height.
        Note: num_x_blocks and num_y_blocks have higher priority to cell_width and cell_height.
              if num_x_blocks and num_y_blocks are specified, cell_width and cell_height will be ignored.

        Args:
            node_dict (dict[int, Node]): node_dict {node_id: Node}, default is self.node_dict.
            num_x_blocks (int, optional): total number of blocks/grids from x direction. Defaults to 10.
            num_y_blocks (int, optional): total number of blocks/grids from y direction. Defaults to 10.
            cell_width (float, optional): the width for each block/grid . Defaults to 0. unit: km.
            cell_height (float, optional): the height for each block/grid. Defaults to 0. unit: km.
            unit (str, optional): the unit of cell_width and cell_height. Defaults to "km".
                Options: ["km", "meter", "mile"]
            use_zone_id (bool, optional): whether to use zone_id from node_dict. Defaults to False.

        Returns:
            dict[str, Zone]: zone_dict {zone_name: Zone}
        """
        if self.verbose:
            print("  : Note: net2zone will generate grid-based zones from node_dict. \
                \n  : If you want to use your own zones(TAZs), \
                \n  : please skip this method and use taz2zone() instead. \n")

        # if not specified, use self.node_dict as input
        if node_dict:
            self.node_dict = node_dict
        else:
            node_dict = self.node_dict

        # update parameters if specified
        if num_x_blocks:
            self.num_x_blocks = num_x_blocks
        if num_y_blocks:
            self.num_y_blocks = num_y_blocks
        if cell_width:
            self.cell_width = cell_width
        if cell_height:
            self.cell_height = cell_height
        if unit:
            self.unit = unit

        print("  : Generating zone dictionary...")

        # generate zone based on zone_id in node.csv
        if self.use_zone_id:
            node_with_zone_id = {}

            for node_id in node_dict:
                with contextlib.suppress(AttributeError):
                    if node_dict[node_id]._zone_id != -1:
                        node_with_zone_id[node_id] = node_dict[node_id]

            if not node_with_zone_id:
                print("  : No zone_id found in node_dict, will generate zone based on original node_dict")
            else:
                node_dict = node_with_zone_id

        self.zone_dict = net2zone(node_dict,
                                  self.num_x_blocks,
                                  self.num_y_blocks,
                                  self.cell_width,
                                  self.cell_height,
                                  self.unit,
                                  verbose=self.verbose)
        self.__pair_zone_id_name = {Zone.id: Zone.name for Zone in self.zone_dict.values()}
        self.is_geometry = True

        # save zone to zone.csv
        zone_df = pd.DataFrame(self.zone_dict.values())
        path_output = path2linux(os.path.join(self.output_dir, "zone.csv"))
        zone_df.to_csv(path_output, index=False)

        if self.verbose:
            print(f"  : net2zone saved zone.csv to {self.output_dir}")

        return self.zone_dict if return_value else None

    def taz2zone(self, zone_file: str = "", return_value: bool = False) -> dict[str, Zone]:

        if self.verbose:
            print("  : Note: taz2zone will generate zones from zone.csv (TAZs). \
                    \n  : If you want to use grid-based zones (generate zones from node_dict) , \
                    \n  : please skip this method and use net2zone() instead. \n")

        # update zone_file if specified
        if zone_file:
            self.zone_file = path2linux(zone_file)

        # check zone_file, geometry or centroid?
        if not os.path.exists(self.zone_file):
            raise FileNotFoundError(f"Error: File {self.zone_file} does not exist.")

        # load zone file column names
        zone_columns = []
        try:
            zone_df = pd.read_csv(self.zone_file, nrows=1)  # 1 row, reduce memory and time
            zone_columns = zone_df.columns
        except Exception as e:
            raise Exception(f"Error: Failed to read {self.zone_file}.") from e

        # update geometry or centroid
        # sourcery skip: merge-nested-ifs
        if set(self.pkg_settings.get("zone_geometry_fields")).issubset(set(zone_columns)):
            # check geometry fields is valid from zone_df
            if not any(zone_df["geometry"].isnull()):
                self.is_geometry = True

        if set(self.pkg_settings.get("zone_centroid_fields")).issubset(set(zone_columns)):
            self.is_centroid = True

        if not self.is_geometry and not self.is_centroid:
            raise Exception(f"Error: {self.zone_file} does not contain valid zone fields.")

        if self.verbose:
            print("  : Generating zone dictionary...")

        # generate zone by geometry: zone_id, geometry
        if self.is_geometry:
            self.zone_dict = read_zone_by_geometry(self.zone_file, self.pkg_settings.get("set_cpu_cores"))
            self.__pair_zone_id_name = {
                Zone.id: Zone.name for Zone in self.zone_dict.values()}

        # generate zone by centroid: zone_id, x_coord, y_coord
        elif self.is_centroid:
            self.zone_dict = read_zone_by_centroid(
                self.zone_file, self.pkg_settings.get("set_cpu_cores"))
            self.__pair_zone_id_name = {
                Zone.id: Zone.name for Zone in self.zone_dict.values()}

        else:
            print(f"Error: {self.zone_file} does not contain valid zone fields.")
            return {}

        return self.zone_dict if return_value else {}

    def sync_geometry_between_zone_and_node_poi(self,
                                                zone_dict: dict = "",
                                                node_dict: dict = "",
                                                poi_dict: dict = "",
                                                return_value: bool = False) -> dict[str, dict]:
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
        if self.verbose:
            print("  : Synchronizing geometry between zone and node/poi...")

        # update zone_dict, node_dict, poi_dict if specified
        if zone_dict:
            self.zone_dict = zone_dict
        if node_dict:
            self.node_dict = node_dict
        if poi_dict:
            self.poi_dict = poi_dict

        # check zone_dict exists
        if not hasattr(self, "zone_dict"):
            raise Exception("Not valid zone_dict. Please generate zone_dict first.")

        # synchronize zone with node
        if hasattr(self, "node_dict"):
            print("  : Synchronizing zone with node...\n")
            if self.is_geometry:
                try:
                    zone_node_dict = sync_zone_geometry_and_node(self.zone_dict,
                                                                 self.node_dict,
                                                                 self.pkg_settings.get("set_cpu_cores"),
                                                                 verbose=self.verbose)
                    self.zone_dict = zone_node_dict.get('zone_dict')
                    self.node_dict = zone_node_dict.get('node_dict')
                except Exception as e:
                    print("Could not synchronize zone with node.\n")
                    print(f"The error occurred: {e}")
            elif self.is_centroid:
                try:
                    zone_node_dict = sync_zone_centroid_and_node(self.zone_dict,
                                                                 self.node_dict,
                                                                 verbose=self.verbose)
                    self.zone_dict = zone_node_dict.get('zone_dict')
                    self.node_dict = zone_node_dict.get('node_dict')
                except Exception as e:
                    print("Could not synchronize zone with node.\n")
                    print(f"The error occurred: {e}")

        # synchronize zone with poi
        if hasattr(self, "poi_dict"):
            print("  : Synchronizing zone with poi...\n")
            if self.is_geometry:
                try:
                    zone_poi_dict = sync_zone_geometry_and_poi(self.zone_dict,
                                                               self.poi_dict,
                                                               self.pkg_settings.get("set_cpu_cores"))
                    self.zone_dict = zone_poi_dict.get('zone_dict')
                    self.poi_dict = zone_poi_dict.get('poi_dict')
                except Exception as e:
                    print("Could not synchronize zone with poi.\n")
                    print(f"The error occurred: {e}")
            elif self.is_centroid:
                try:
                    zone_poi_dict = sync_zone_centroid_and_poi(self.zone_dict,
                                                               self.poi_dict,
                                                               verbose=self.verbose)
                    self.zone_dict = zone_poi_dict.get('zone_dict')
                    self.poi_dict = zone_poi_dict.get('poi_dict')
                except Exception as e:
                    print("Could not synchronize zone with poi.\n")
                    print(f"The error occurred: {e}")

        # # if not specified, use self.zone_dict, self.node_dict, self.poi_dict as input
        # if not all([zone_dict, node_dict, poi_dict]):
        #     zone_dict = self.zone_dict
        #     node_dict = self.node_dict
        #     poi_dict = self.poi_dict

        # # synchronize zone with node
        # try:
        #     zone_node_dict = sync_zone_geometry_and_node(zone_dict, node_dict, self.pkg_settings.get("set_cpu_cores"), verbose=self.verbose)
        #     zone_dict_add_node = zone_node_dict.get('zone_dict')
        #     self.node_dict = zone_node_dict.get('node_dict')
        # except Exception as e:
        #     raise Exception(
        #         f"Error in running {self.sync_geometry_between_zone_and_node_poi.__name__}: \
        #           not valid zone_dict or node_dict"
        #     ) from e

        # # synchronize zone with poi
        # try:
        #     zone_poi_dict = sync_zone_geometry_and_poi(zone_dict_add_node,
        #                                                poi_dict,
        #                                                self.pkg_settings.get("set_cpu_cores"))
        #     self.zone_dict = zone_poi_dict.get('zone_dict')
        #     self.poi_dict = zone_poi_dict.get('poi_dict')
        # except Exception as e:
        #     raise Exception(
        #         f"Error in running {self.sync_geometry_between_zone_and_node_poi.__name__}: \
        #           not valid zone_dict or poi_dict"
        #     ) from e

        self.is_sync_geometry = True
        return {"zone_dict": self.zone_dict,
                "node_dict": self.node_dict,
                "poi_dict": self.poi_dict} if return_value else None

    def calc_zone_od_distance_matrix(self, zone_dict: dict = "", return_value: bool = False) -> dict[tuple, float]:
        """calculate zone-to-zone od distance matrix

        Args:
            zone_dict (dict, optional): the zone dictionary. Defaults to "".
                if not specified, use self.zone_dict.

        Returns:
            dict[tuple, float]: zone_od_matrix {(zone_id1, zone_id2): distance}
        """

        # if not specified, use self.zone_dict as input
        if zone_dict:
            self.zone_dict = zone_dict

        self.zone_od_dist_matrix = calc_zone_od_matrix(self.zone_dict,
                                                       self.pkg_settings.get("set_cpu_cores"),
                                                       verbose=self.verbose)
        self.is_zone_od_dist_matrix = True
        return self.zone_od_dist_matrix if return_value else None

    def gen_poi_trip_rate(self,
                          poi_dict: dict = "",
                          trip_rate_file: str = "",
                          trip_purpose: int = 1,
                          return_value: bool = False) -> dict[int, POI]:
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

        # update input parameters if specified
        if poi_dict:
            self.poi_dict = poi_dict

        # if usr provides trip_rate_file (csv file), save to self.pkg_settings["trip_rate_file"]
        if trip_rate_file:
            self.trip_rate_file = trip_rate_file
            if ".csv" not in self.trip_rate_file:
                raise Exception(f"  : Error: trip_rate_file {self.trip_rate_file} must be a csv file.")
            self.pkg_settings["trip_rate_file"] = pd.read_csv(self.trip_rate_file)

        # update trip_purpose if specified
        if trip_purpose:
            self.trip_purpose = trip_purpose

        self.poi_dict = gen_poi_trip_rate(self.poi_dict, self.trip_rate_file, self.trip_purpose, verbose=self.verbose)
        self.is_poi_trip_rate = True
        return self.poi_dict if return_value else None

    def gen_node_prod_attr(self,
                           node_dict: dict = "",
                           poi_dict: dict = "",
                           return_value: bool = False) -> dict[int, Node]:
        """generate production and attraction for each node based on poi trip rate

        Args:
            node_dict (dict, optional): Defaults to "". if not specified, use self.node_dict.
            poi_dict (dict, optional): Defaults to "". if not specified, use self.poi_dict.

        Returns:
            dict[int, Node]: the updated node_dict {node_id: Node}
        """

        # if not all([node_dict, poi_dict]):
        #     node_dict = self.node_dict
        #     poi_dict = self.poi_dict

        # update input parameters if specified
        if node_dict:
            self.node_dict = node_dict
        if poi_dict:
            self.poi_dict = poi_dict

        self.node_dict = gen_node_prod_attr(self.node_dict, self.poi_dict, verbose=self.verbose)
        self.is_node_prod_attr = True
        return self.node_dict if return_value else None

    def calc_zone_prod_attr(self,
                            zone_dict: dict = "",
                            node_dict: dict = "",
                            poi_dict: dict = "",
                            trip_rate_file: str = "",
                            trip_purpose: int = 1,
                            return_value: bool = False) -> dict[str, Zone]:
        """calculate zone production and attraction based on node production and attraction

        Args:
            node_dict (dict, optional): Defaults to "". if not specified, use self.node_dict.
            zone_dict (dict, optional): Defaults to "". if not specified, use self.zone_dict.

        Returns:
            dict[str, Zone]: the updated zone_dict {zone_name: Zone}
        """

        # update input parameters if specified
        if zone_dict:
            self.zone_dict = zone_dict

        if node_dict:
            self.node_dict = node_dict

        if poi_dict:
            self.poi_dict = poi_dict

        if trip_rate_file:
            self.trip_rate_file = trip_rate_file

        if trip_purpose:
            self.trip_purpose = trip_purpose

        # calculate od distance matrix if not exists
        if not self.is_zone_od_dist_matrix:
            self.calc_zone_od_distance_matrix(zone_dict=self.zone_dict)

        # generate poi trip rate for each poi if not generated
        if not self.is_poi_trip_rate:
            self.gen_poi_trip_rate(poi_dict=self.poi_dict,
                                   trip_rate_file=self.trip_rate_file,
                                   trip_purpose=self.trip_purpose)

        # generate node production and attraction for each node based on poi_trip_rate if not generated
        if not self.is_node_prod_attr:
            self.gen_node_prod_attr(node_dict=self.node_dict,
                                    poi_dict=self.poi_dict)

        # if not all([node_dict, zone_dict]):
        #     node_dict = self.node_dict
        #     zone_dict = self.zone_dict

        # calculate zone production and attraction based on node production and attraction
        self.zone_dict = calc_zone_production_attraction(self.node_dict, self.zone_dict, verbose=self.verbose)
        self.is_zone_prod_attr = True

        return self.zone_dict if return_value else None

    def run_gravity_model(self,
                          zone_dict: dict = "",
                          node_dict: dict = "",
                          poi_dict: dict = "",
                          zone_od_dist_matrix: dict = "",
                          trip_rate_file: str = "",
                          trip_purpose: int = 1,
                          alpha: float = 28507,
                          beta: float = -0.02,
                          gamma: float = -0.123,
                          return_value: bool = False) -> pd.DataFrame:
        """run gravity model to generate demand

        Args:
            zone_dict (dict, optional): dict store zones info. Defaults to "".
            zone_od_dist_matrix (dict, optional): OD distance matrix. Defaults to "".
            trip_purpose (int, optional): purpose of trip. Defaults to 1.
            alpha (float, optional): parameter alpha. Defaults to 28507.
            beta (float, optional): parameter beta. Defaults to -0.02.
            gamma (float, optional): parameter gamma. Defaults to -0.123.

        Returns:
            pd.DataFrame: the final demand dataframe
        """
        # if not specified, use self.zone_dict, self.zone_od_dist_matrix as input
        # if not all([zone_dict, zone_od_dist_matrix]):
        #     zone_dict = self.zone_dict
        #     zone_od_dist_matrix = self.zone_od_dist_matrix

        # update parameters if specified
        if zone_dict:
            self.zone_dict = zone_dict
        if node_dict:
            self.node_dict = node_dict
        if poi_dict:
            self.poi_dict = poi_dict
        if zone_od_dist_matrix:
            self.zone_od_dist_matrix = zone_od_dist_matrix
        if trip_rate_file:
            self.trip_rate_file = trip_rate_file
        if trip_purpose:
            self.trip_purpose = trip_purpose
        if alpha:
            self.alpha = alpha
        if beta:
            self.beta = beta
        if gamma:
            self.gamma = gamma

        # synchronize geometry between zone and node/poi
        if not self.is_sync_geometry:
            self.sync_geometry_between_zone_and_node_poi()

        # calculate zone production and attraction based on node production and attraction
        if not self.is_zone_prod_attr:
            self.calc_zone_prod_attr(zone_dict=self.zone_dict,
                                     node_dict=self.node_dict,
                                     poi_dict=self.poi_dict,
                                     trip_rate_file=self.trip_rate_file,
                                     trip_purpose=self.trip_purpose)

        # run gravity model to generate demand
        self.zone_od_demand_matrix = run_gravity_model(self.zone_dict,
                                                       self.zone_od_dist_matrix,
                                                       self.trip_purpose,
                                                       self.alpha,
                                                       self.beta,
                                                       self.gamma,
                                                       verbose=self.verbose)
        self.df_demand = pd.DataFrame(list(self.zone_od_demand_matrix.values()))

#         # if use_zone_id is True, generate demand dataframe based on zone_id from node.csv
#         if self.use_zone_id:
#
#             # generate comb {(o_node_id, d_node_id)}
#             # pair_node_zone_id: node_id and zone_id from node.csv, they are unique pairs
#             # comb: all possible combinations of node_id pairs
#             # comb: can be seen as all possible zone_id pairs from node.csv
#             node_zone_lst = list(self.__pair_node_zone_id.keys())
#
#             # create all possible combinations of node_id pairs
#             comb = [(i, j) for i in node_zone_lst for j in node_zone_lst]
#
#             # generate demand_lst to store demand dataframe
#             demand_lst = []
#
#             # create demand dictionary
#             for pair in comb:
#                 o_node_id, d_node_id = pair
#                 o_zone_id = self.node_dict[o_node_id].zone_id  # zone_id from generated zone
#                 d_zone_id = self.node_dict[d_node_id].zone_id  # zone_id from generated zone
#
#                 o_zone_name = self.__pair_zone_id_name.get(o_zone_id, "")  # zone_name from generated zone
#                 d_zone_name = self.__pair_zone_id_name.get(d_zone_id, "")  # zone_name from generated zone
#
#                 if o_zone_name and d_zone_name and o_zone_name != d_zone_name:
#                     try:
#                         dist_km = self.zone_od_dist_matrix[(o_zone_name, d_zone_name)].get('dist_km')
#                         volume = self.zone_od_demand_matrix[(o_zone_name, d_zone_name)].get('volume')
#
#                         demand_lst.append(
#                             {
#                                 # "o_node_id": o_node_id,
#                                 "o_zone_id": self.__pair_node_zone_id[o_node_id],
#                                 "o_zone_name": self.__pair_node_zone_id[o_node_id],
#
#                                 # "d_node_id": d_node_id,
#                                 "d_zone_id": self.__pair_node_zone_id[d_node_id],
#                                 "d_zone_name": self.__pair_node_zone_id[d_node_id],
#                                 "dist_km": dist_km,
#                                 "volume": volume,
#                                 "geometry": shapely.LineString([self.node_dict[o_node_id].geometry,
#                                                                 self.node_dict[d_node_id].geometry])
#
#                             }
#                         )
#
#                     except KeyError:
#                         dist_km = 0
#                         volume = 0
#
#                         if self.verbose:
#                             print(f"  : Error: zone_od_dist_matrix does not contain {o_zone_name, d_zone_name}.")
#             if demand_lst:
#                 self.df_demand_based_zone_id = pd.DataFrame(demand_lst)
#             else:
#                 self.df_demand_based_zone_id = pd.DataFrame(columns=["o_zone_id", "o_zone_name",
#                                                                      "d_zone_id", "d_zone_name",
#                                                                      "dist_km", "volume", "geometry"])
#             return self.df_demand_based_zone_id if return_value else None

        print("  : Successfully generated OD demands.")
        return self.df_demand if return_value else None

    def gen_agent_based_demand(self,
                               node_dict: dict = "",
                               zone_dict: dict = "",
                               df_demand: pd.DataFrame = "") -> pd.DataFrame:
        """generate agent-based demand

        Args:
            node_dict (dict, optional): _description_. Defaults to "".
            zone_dict (dict, optional): _description_. Defaults to "".
            df_demand (pd.DataFrame, optional): _description_. Defaults to "".

        Returns:
            pd.DataFrame: the final agent-based demand dataframe
        """

        if not isinstance(df_demand, pd.DataFrame):
            df_demand = self.df_demand

        if not all([node_dict, zone_dict]):
            node_dict = self.node_dict
            zone_dict = self.zone_dict

        self.df_agent = gen_agent_based_demand(node_dict, zone_dict, df_demand=df_demand, verbose=self.verbose)
        return self.df_agent

    def save_results_to_csv(self, output_dir: str = "",
                            demand: bool = True,
                            *,  # enforce keyword-only arguments
                            zone: bool = True,
                            node: bool = True,  # save updated node
                            poi: bool = True,  # save updated poi
                            zone_od_dist_table: bool = False,
                            zone_od_dist_matrix: bool = False,
                            is_demand_with_geometry: bool = False,
                            overwrite_file: bool = True) -> None:

        # update output_dir if specified
        if output_dir:
            self.output_dir = path2linux(output_dir)

        if demand:
            self.save_demand(overwrite_file=overwrite_file, is_demand_with_geometry=is_demand_with_geometry)

        if zone:
            self.save_zone(overwrite_file=overwrite_file)

        if node:
            self.save_node(overwrite_file=overwrite_file)

        if poi:
            self.save_poi(overwrite_file=overwrite_file)

        if zone_od_dist_table:
            self.save_zone_od_dist_table(overwrite_file=overwrite_file)

        if zone_od_dist_matrix:
            self.save_zone_od_dist_matrix(overwrite_file=overwrite_file)

        return None

    # @property
    def save_demand(self, overwrite_file: bool = True,
                    is_demand_with_geometry: bool = False) -> None:

        if overwrite_file:
            path_output = path2linux(os.path.join(self.output_dir, "demand.csv"))
        else:
            path_output = generate_unique_filename(path2linux(os.path.join(self.output_dir, "demand.csv")))

        # check if df_demand exists
        if not hasattr(self, "df_demand"):
            print("  : Could not save demand file: df_demand does not exist. Please run run_gravity_model() first.")
        else:

            df_demand_non_zero = self.df_demand[self.df_demand["volume"] > 0]

            if is_demand_with_geometry:
                col_name = ["o_zone_id", "d_zone_id", "dist_km", "volume", "geometry"]
            else:
                col_name = ["o_zone_id", "d_zone_id", "dist_km", "volume"]

            df_demand_non_zero = df_demand_non_zero[col_name]

            df_demand_non_zero.to_csv(path_output, index=False)
            print(f"  : Successfully saved demand.csv to {self.output_dir}")
        return None

    # @property
    def save_agent(self, overwrite_file: bool = True) -> None:

        if not hasattr(self, "df_agent"):
            print("  : df_agent does not exist. Please run gen_agent_based_demand() first.")
            return

        if overwrite_file:
            path_output = path2linux(os.path.join(self.output_dir, "agent.csv"))
        else:
            path_output = generate_unique_filename(path2linux(os.path.join(self.output_dir, "agent.csv")))
        self.df_agent.to_csv(path_output, index=False)
        print(f"  : Successfully saved agent.csv to {self.output_dir}")

    # @property
    def save_zone(self, overwrite_file: bool = True) -> None:

        if overwrite_file:
            path_output = path2linux(os.path.join(self.output_dir, "zone.csv"))
        else:
            path_output = generate_unique_filename(path2linux(os.path.join(self.output_dir, "zone.csv")))

        # check if zone_dict exists
        if not hasattr(self, "zone_dict"):
            print("  : Could not save zone file: zone_dict does not exist. \
                Please run sync_geometry_between_zone_and_node_poi() first.")
        else:
            zone_df = pd.DataFrame(self.zone_dict.values())

            # change column name from id to node_id
            zone_df.rename(columns={"id": "zone_id"}, inplace=True)

            zone_df.to_csv(path_output, index=False)
            print(f"  : Successfully saved zone.csv to {self.output_dir}")
        return None

    # @property
    def save_node(self, overwrite_file: bool = True) -> None:

        if not hasattr(self, "node_dict"):
            print("  : node_dict does not exist. Please run sync_geometry_between_zone_and_node_poi() first.")
            return

        if overwrite_file:
            path_output = path2linux(os.path.join(self.output_dir, "node.csv"))
        else:
            path_output = generate_unique_filename(path2linux(os.path.join(self.output_dir, "node.csv")))

        node_df = pd.DataFrame(self.node_dict.values())

        # update node data if centroid is used, ignore zone_id if original zone_id is empty
        if self.is_centroid:
            for i in range(len(node_df)):
                original_zone_id = node_df.loc[i, "_zone_id"]
                if original_zone_id == -1:
                    node_df.loc[i, "zone_id"] = None

        if self.use_zone_id:
            node_df["zone_id"] = ""
            node_is_zone_df = pd.DataFrame(self._node_is_zone.values())
            node_is_zone_df["zone_id"] = node_is_zone_df["_zone_id"]

            node_df = pd.concat([node_df, node_is_zone_df], ignore_index=True)

        node_df.rename(columns={"id": "node_id"}, inplace=True)
        node_df.to_csv(path_output, index=False)
        print(f"  : Successfully saved updated node to node.csv to {self.output_dir}")
        return None

    # @property
    def save_poi(self, overwrite_file: bool = True) -> None:

        if overwrite_file:
            path_output = path2linux(os.path.join(self.output_dir, "poi.csv"))
        else:
            path_output = generate_unique_filename(path2linux(os.path.join(self.output_dir, "poi.csv")))

        # check if poi_dict exists
        if not hasattr(self, "poi_dict"):
            print("  : Could not save updated poi file: poi_dict does not exist. Please run load_poi() first.")
        else:
            poi_df = pd.DataFrame(self.poi_dict.values())

            # rename column name from id to poi_id
            poi_df.rename(columns={"id": "poi_id"}, inplace=True)
            poi_df.to_csv(path_output, index=False)
            print(f"  : Successfully saved updated poi to poi.csv to {self.output_dir}")
        return None

    # @property
    def save_zone_od_dist_table(self, overwrite_file: bool = True) -> None:

        if overwrite_file:
            path_output = path2linux(os.path.join(self.output_dir, "zone_od_dist_table.csv"))
        else:
            path_output = generate_unique_filename(path2linux(os.path.join(self.output_dir, "zone_od_dist_table.csv")))

        # check if zone_od_dist_matrix exists
        if not hasattr(self, "zone_od_dist_matrix"):
            print("  : zone_od_dist_matrix does not exist. Please run calc_zone_od_distance_matrix() first.")
        else:
            zone_od_dist_table_df = pd.DataFrame(self.zone_od_dist_matrix.values())
            zone_od_dist_table_df = zone_od_dist_table_df[["o_zone_id", "d_zone_id",
                                                            "dist_km", "geometry"]]
            zone_od_dist_table_df.to_csv(path_output, index=False)
            print(f"  : Successfully saved zone_od_dist_table.csv to {self.output_dir}")
        return None

    # @property
    def save_zone_od_dist_matrix(self, overwrite_file: bool = True) -> None:

        if overwrite_file:
            path_output = path2linux(os.path.join(self.output_dir, "zone_od_dist_matrix.csv"))
        else:
            path_output = generate_unique_filename(path2linux(os.path.join(self.output_dir, "zone_od_dist_matrix.csv")))

        # check if zone_od_dist_matrix exists
        if not hasattr(self, "zone_od_dist_matrix"):
            print(
                "  : zone_od_dist_matrix does not exist. Please run calc_zone_od_distance_matrix() first.")
        else:
            zone_od_dist_table_df = pd.DataFrame(self.zone_od_dist_matrix.values())
            zone_od_dist_table_df = zone_od_dist_table_df[["o_zone_id", "o_zone_name", "d_zone_id",
                                                            "d_zone_name", "dist_km", "geometry"]]

            zone_od_dist_matrix_df = zone_od_dist_table_df.pivot(index='o_zone_name',
                                                                    columns='d_zone_name',
                                                                    values='dist_km')

            zone_od_dist_matrix_df.to_csv(path_output)
            print(f"  : Successfully saved zone_od_dist_matrix.csv to {self.output_dir}")
        return None
