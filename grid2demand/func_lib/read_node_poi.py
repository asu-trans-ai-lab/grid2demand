# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 4th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

from __future__ import absolute_import
import pandas as pd
import shapely
import os
from multiprocessing import Pool

from grid2demand.utils_lib.net_utils import Node, POI, Zone
from grid2demand.utils_lib.pkg_settings import pkg_settings
from grid2demand.utils_lib.utils import check_required_files_exist
from pyufunc import (func_running_time, path2linux,
                     get_filenames_by_ext,)


def create_node_from_dataframe(df_node: pd.DataFrame) -> dict[int, Node]:
    """Create Node from df_node.

    Args:
        df_node (pd.DataFrame): the dataframe of node from node.csv

    Returns:
        dict[int, Node]: a dict of nodes.{node_id: Node}
    """
    # Reset index to avoid index error
    df_node = df_node.reset_index(drop=True)

    node_dict = {}
    for i in range(len(df_node)):
        try:
            # check activity location tab
            activity_type = df_node.loc[i, 'activity_type']
            boundary_flag = df_node.loc[i, 'is_boundary']
            if activity_type in ["residential", "poi"]:
                activity_location_tab = activity_type
            elif boundary_flag == 1:
                activity_location_tab = "boundary"
            else:
                activity_location_tab = ''

            # check zone_id field in node.csv
            # if zone_id field exists and is not empty, assign it to __zone_id
            try:
                __zone_id = df_node.loc[i, 'zone_id']
            except Exception:
                __zone_id = -1

            node = Node(
                id=df_node.loc[i, 'node_id'],
                activity_type=activity_type,
                activity_location_tab=activity_location_tab,
                x_coord=df_node.loc[i, 'x_coord'],
                y_coord=df_node.loc[i, 'y_coord'],
                poi_id=df_node.loc[i, 'poi_id'],
                boundary_flag=boundary_flag,
                geometry=shapely.Point(df_node.loc[i, 'x_coord'], df_node.loc[i, 'y_coord']),
                __zone_id=__zone_id
            )
            node_dict[df_node.loc[i, 'node_id']] = node
        except Exception as e:
            print(f"  : Unable to create node: {df_node.loc[i, 'node_id']}, error: {e}")
    return node_dict


@func_running_time
def read_node(node_file: str = "", cpu_cores: int = 1) -> dict[int: Node]:
    """Read node.csv file and return a dict of nodes.

    Args:
        node_file (str, optional): node file path. Defaults to "".

    Raises:
        FileNotFoundError: File: {node_file} does not exist.

    Returns:
        dict: a dict of nodes.

    Examples:
        >>> node_dict = read_node(node_file = r"../dataset/ASU/node.csv")
        >>> node_dict[1]
        Node(id=1, zone_id=0, x_coord=0.0, y_coord=0.0, production=0.0, attraction=0.0, boundary_flag=0, geometry='POINT (0 0)')

        # if node_file does not exist, raise error
        >>> node_dict = read_node(node_file = r"../dataset/ASU/node.csv")
        FileNotFoundError: File: ../dataset/ASU/node.csv does not exist.
    """

    # convert path to linux path
    node_file = path2linux(node_file)

    # check if node_file exists
    if not os.path.exists(node_file):
        raise FileNotFoundError(f"File: {node_file} does not exist.")

    print(f"  : Parallel creating Nodes using Pool with {cpu_cores} CPUs. Please wait...")
    # read node.csv with specified columns and chunksize for iterations
    node_required_cols = pkg_settings["node_required_fields"]
    chunk_size = pkg_settings["data_chunk_size"]
    print(f"  : Reading node.csv with specified columns: {node_required_cols} \
                \n    and chunksize {chunk_size} for iterations...")
    df_node_chunk = pd.read_csv(node_file, usecols=node_required_cols, chunksize=chunk_size)

    # Parallel processing using Pool
    node_dict_final = {}
    with Pool(cpu_cores) as pool:
        results = pool.map(create_node_from_dataframe, df_node_chunk)

    for node_dict in results:
        node_dict_final.update(node_dict)
    print(f"  : Successfully loaded node.csv: {len(node_dict_final)} Nodes loaded.")
    return node_dict_final


def create_poi_from_dataframe(df_poi: pd.DataFrame) -> dict[int, POI]:
    """Create POI from df_poi.

    Args:
        df_poi (pd.DataFrame): the dataframe of poi from poi.csv

    Returns:
        dict[int, POI]: a dict of POIs.{poi_id: POI}
    """

    df_poi = df_poi.reset_index(drop=True)
    poi_dict = {}

    for i in range(len(df_poi)):
        try:
            centroid = shapely.from_wkt(df_poi.loc[i, 'centroid'])
            area = df_poi.loc[i, 'area']
            if area > 90000:
                area = 0
            poi = POI(
                id=df_poi.loc[i, 'poi_id'],
                x_coord=centroid.x,
                y_coord=centroid.y,
                area=[area, area * 10.7639104],  # square meter and square feet
                poi_type=df_poi.loc[i, 'building'] or "",
                geometry=df_poi.loc[i, "geometry"]
            )
            poi_dict[df_poi.loc[i, 'poi_id']] = poi
        except Exception as e:
            print(f"  : Unable to create poi: {df_poi.loc[i, 'poi_id']}, error: {e}")
    return poi_dict


@func_running_time
def read_poi(poi_file: str = "", cpu_cores: int = 1) -> dict[int: POI]:
    """Read poi.csv file and return a dict of POIs.

    Args:
        poi_file (str): The poi.csv file path. default is "".

    Raises:
        FileNotFoundError: if poi_file does not exist.

    Returns:
        dict: A dict of POIs.

    Examples:
        >>> poi_dict = read_poi(poi_file = r"../dataset/ASU/poi.csv")
        >>> poi_dict[1]
        POI(id=1, x_coord=0.0, y_coord=0.0, area=[0, 0.0], poi_type='residential', geometry='POINT (0 0)')

        # if poi_file does not exist, raise error
        >>> poi_dict = read_poi(poi_file = r"../dataset/ASU/poi.csv")
        FileNotFoundError: File: ../dataset/ASU/poi.csv does not exist.

    """

    # convert path to linux path
    poi_file = path2linux(poi_file)

    # check if poi_file exists
    if not os.path.exists(poi_file):
        raise FileNotFoundError(f"File: {poi_file} does not exist.")

    # Read poi.csv with specified columns and chunksize for iterations
    poi_required_cols = pkg_settings["poi_required_fields"]
    chunk_size = pkg_settings["data_chunk_size"]
    print(f"  : Reading poi.csv with specified columns: {poi_required_cols} \
                \n    and chunksize {chunk_size} for iterations...")
    df_poi_chunk = pd.read_csv(poi_file, usecols=poi_required_cols, chunksize=chunk_size)

    # Parallel processing using Pool
    print(f"  : Parallel creating POIs using Pool with {cpu_cores} CPUs. Please wait...")
    poi_dict_final = {}

    with Pool(cpu_cores) as pool:
        results = pool.map(create_poi_from_dataframe, df_poi_chunk)

    for poi_dict in results:
        poi_dict_final.update(poi_dict)

    print(f"  : Successfully loaded poi.csv: {len(poi_dict_final)} POIs loaded.")
    return poi_dict_final


def create_zone_from_dataframe(df_zone: pd.DataFrame) -> dict[int, Zone]:
    """Create Zone from df_zone.

    Args:
        df_zone (pd.DataFrame): the dataframe of zone from zone.csv, the required fields are: [zone_id, geometry]

    Returns:
        dict[int, Zone]: a dict of Zones.{zone_id: Zone}
    """
    df_zone = df_zone.reset_index(drop=True)
    zone_dict = {}

    for i in range(len(df_zone)):
        try:
            zone_id = df_zone.loc[i, 'zone_id']
            zone_geometry = df_zone.loc[i, 'geometry']

            zone_geometry_shapely = shapely.from_wkt(zone_geometry)
            centroid_wkt = zone_geometry_shapely.centroid.wkt
            centroid_x = zone_geometry_shapely.centroid.x
            centroid_y = zone_geometry_shapely.centroid.y
            zone = Zone(
                id=zone_id,
                name=zone_id,
                centroid_x=centroid_x,
                centroid_y=centroid_y,
                centroid=centroid_wkt,
                x_max=zone_geometry_shapely.bounds[2],
                x_min=zone_geometry_shapely.bounds[0],
                y_max=zone_geometry_shapely.bounds[3],
                y_min=zone_geometry_shapely.bounds[1],
                node_id_list=[],
                poi_id_list=[],
                production=0,
                attraction=0,
                production_fixed=0,
                attraction_fixed=0,
                geometry=zone_geometry
            )

            zone_dict[zone_id] = zone
        except Exception as e:
            print(f"  : Unable to create zone: {zone_id}, error: {e}")
    return zone_dict


@func_running_time
def read_zone(zone_file: str = "", cpu_cores: int = 1) -> dict[int: Zone]:
    """_summary_

    Raises:
        FileNotFoundError: _description_
        FileNotFoundError: _description_

    Returns:
        _type_: _description_
    """

    # convert path to linux path
    zone_file = path2linux(zone_file)

    # check if zone_file exists
    if not os.path.exists(zone_file):
        raise FileNotFoundError(f"File: {zone_file} does not exist.")

    # load default settings for zone required fields and chunk size
    zone_required_cols = pkg_settings["zone_required_fields"]
    chunk_size = pkg_settings["data_chunk_size"]
    print(f"  : Reading zone.csv with specified columns: {zone_required_cols} \
              \n   and chunksize {chunk_size} for iterations...")

    # check whether required fields are in zone.csv
    df_zone = pd.read_csv(zone_file, nrows=1)
    col_names = df_zone.columns.tolist()
    for col in zone_required_cols:
        if col not in col_names:
            raise FileNotFoundError(f"Required column: {col} is not in zone.csv. \
                Please make sure you have {zone_required_cols} in zone.csv.")

    # load zone.csv with specified columns and chunksize for iterations
    df_zone_chunk = pd.read_csv(zone_file, usecols=zone_required_cols, chunksize=chunk_size)

    # Parallel processing using Pool
    print(f"  : Parallel creating Zones using Pool with {cpu_cores} CPUs. Please wait...")
    zone_dict_final = {}

    with Pool(cpu_cores) as pool:
        results = pool.map(create_zone_from_dataframe, df_zone_chunk)

    for zone_dict in results:
        zone_dict_final.update(zone_dict)

    print(f"  : Successfully loaded zone.csv: {len(zone_dict_final)} Zones loaded.")
    return zone_dict_final


@func_running_time
def read_network(input_folder: str = "", cpu_cores: int = 1) -> dict[str: dict]:
    """Read node.csv and poi.csv files and return a dict of nodes and a dict of POIs.

    Args:
        input_folder (str, optional): required files within this folder. Defaults to current folder.

    Raises:
        FileNotFoundError: if input_folder does not exist.

    Returns:
        dict: a dict of nodes and a dict of POIs.

    Examples:
        >>> node_dict, poi_dict = read_network(input_folder = r"../dataset/ASU")
        >>> node_dict[1]
        Node(id=1, zone_id=0, x_coord=0.0, y_coord=0.0, production=0.0, attraction=0.0, boundary_flag=0,
        >>> poi_dict[1]
        POI(id=1, x_coord=0.0, y_coord=0.0, area=[0, 0.0], poi_type='residential', geometry='POINT (0 0)')

        # if input_folder is not specified, use current folder
        >>> node_dict, poi_dict = read_network()

        # if required files are not satisfied, raise error
        >>> node_dict, poi_dict = read_network(input_folder = r"../dataset/ASU")
        FileNotFoundError: Required files: ['node.csv', 'poi.csv'] are not satisfied, please check your input folder.
    """

    # set input folder to current folder if not specified
    if not input_folder:
        input_folder = os.getcwd()

    # convert path to linux path
    input_folder = path2linux(input_folder)

    # check if input_folder exists
    if not os.path.isdir(input_folder):
        raise FileNotFoundError(f"Input folder: {input_folder} does not exist.")

    # get all csv files in the folder
    dir_files = get_filenames_by_ext(input_folder, "csv")

    # check if required files exist
    is_required_files_exist = check_required_files_exist(pkg_settings["required_files"], dir_files)

    # if not all required files exist, raise error
    if not is_required_files_exist:
        raise FileNotFoundError(f"Required files: {pkg_settings['required_files']} are not satisfied, please check your input folder.")

    node_dict = read_node(input_folder + "/node.csv", cpu_cores)
    poi_dict = read_poi(input_folder + "/poi.csv", cpu_cores)

    print(f"  : Successfully loaded node.csv and poi.csv: {len(node_dict)} Nodes and {len(poi_dict)} POIs.")
    return {"node_dict": node_dict, "poi_dict": poi_dict}
