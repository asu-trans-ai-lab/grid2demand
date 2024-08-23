# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 4th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

from __future__ import absolute_import

import os
from multiprocessing import Pool
from dataclasses import make_dataclass, fields, asdict
from typing import Any

import pandas as pd
import shapely
from pyproj import Transformer
from tqdm.contrib.concurrent import process_map
from tqdm import tqdm

from grid2demand.utils_lib.net_utils import Node, POI, Zone
from grid2demand.utils_lib.pkg_settings import pkg_settings
from grid2demand.utils_lib.utils import (check_required_files_exist,
                                         extend_dataclass,
                                         create_dataclass_from_dict)
from pyufunc import (func_running_time, path2linux,
                     get_filenames_by_ext,)

# supporting functions for multiprocessing implementation


def _create_node_from_dataframe(df_node: pd.DataFrame) -> dict[int, Node]:
    """Create Node from df_node.

    Args:
        df_node (pd.DataFrame): the dataframe of node from node.csv

    Returns:
        dict[int, Node]: a dict of nodes.{node_id: Node}
    """
    # Reset index to avoid index error
    df_node = df_node.reset_index(drop=True)
    col_names = df_node.columns.tolist()

    if "node_id" in col_names:
        col_names.remove("node_id")

    # get node dataclass fields
    # Get the list of attribute names
    node_attr_names = [f.name for f in fields(Node)]

    # check difference between node_attr_names and col_names
    diff = list(set(col_names) - set(node_attr_names))

    # create attributes for node class if diff is not empty
    if diff:
        diff_attr = [(val, str, "") for val in diff]
        Node_ext = extend_dataclass(Node, diff_attr)
    else:
        Node_ext = Node

    node_dict = {}
    for i in range(len(df_node)):
        try:
            # check whether zone_id field in node.csv or not
            # if zone_id field exists and is not empty, assign it to _zone_id
            try:
                _zone_id = int(df_node.loc[i, 'zone_id'])

                # check if _zone is none or empty, assign -1
                if pd.isna(_zone_id) or not _zone_id:
                    _zone_id = -1

            except Exception:
                _zone_id = -1

            # get node id
            node_id = int(df_node.loc[i, 'node_id'])
            x_coord = float(df_node.loc[i, 'x_coord'])
            y_coord = float(df_node.loc[i, 'y_coord'])

            node = Node_ext()

            for col in col_names:
                setattr(node, col, df_node.loc[i, col])

            node.id = node_id
            node._zone_id = _zone_id
            node.geometry = shapely.Point(x_coord, y_coord)

            # node = Node(
            #     id=node_id,
            #     # activity_type=activity_type,
            #     # ctrl_type=df_node.loc[i, 'ctrl_type'],
            #     x_coord=x_coord,
            #     y_coord=y_coord,
            #     # poi_id=df_node.loc[i, 'poi_id'],
            #     # is_boundary=is_boundary,
            #     geometry=shapely.Point(x_coord, y_coord),
            #     _zone_id=_zone_id
            # )

            node_dict[node_id] = asdict(node)

        except Exception as e:
            print(f"  : Unable to create node: {node_id}, error: {e}")

    return node_dict


def _create_poi_from_dataframe(df_poi: pd.DataFrame) -> dict[int, POI]:
    """Create POI from df_poi.

    Args:
        df_poi (pd.DataFrame): the dataframe of poi from poi.csv

    Returns:
        dict[int, POI]: a dict of POIs.{poi_id: POI}
    """

    df_poi = df_poi.reset_index(drop=True)
    col_names = df_poi.columns.tolist()

    if "poi_id" in col_names:
        col_names.remove("poi_id")

    # get node dataclass fields
    # Get the list of attribute names
    poi_attr_names = [f.name for f in fields(POI)]

    # check difference between node_attr_names and col_names
    diff = list(set(col_names) - set(poi_attr_names))

    # create attributes for node class if diff is not empty
    if diff:
        diff_attr = [(val, Any, "") for val in diff]
        POI_ext = extend_dataclass(POI, diff_attr)
    else:
        POI_ext = POI

    poi_dict = {}

    for i in range(len(df_poi)):
        try:
            centroid = shapely.from_wkt(df_poi.loc[i, 'centroid'])

            # check if area is empty or not
            area = df_poi.loc[i, 'area']
            if pd.isna(area) or not area:
                geometry_shapely = shapely.from_wkt(df_poi.loc[i, 'geometry'])

                # Set up a Transformer to convert from WGS 84 to UTM zone 18N (EPSG:32618)
                transformer = Transformer.from_crs(
                    "EPSG:4326", "EPSG:32618", always_xy=True)

                # Transform the polygon's coordinates to UTM
                transformed_coords = [transformer.transform(x, y) for x, y in geometry_shapely.exterior.coords]
                transformed_polygon = shapely.Polygon(transformed_coords)

                # square meters
                area_sqm = transformed_polygon.area

                # square feet
                # area = area_sqm * 10.7639104

                area = area_sqm

            elif area > 90000:
                area = 0
            else:
                pass

            # get poi id
            poi_id = int(df_poi.loc[i, 'poi_id'])

            poi = POI_ext()

            for col in col_names:
                setattr(poi, col, df_poi.loc[i, col])

            poi.id = poi_id
            poi.x_coord = centroid.x
            poi.y_coord = centroid.y
            poi.area = area

            # poi = POI(
            #     id=df_poi.loc[i, 'poi_id'],
            #     x_coord=centroid.x,
            #     y_coord=centroid.y,
            #     area=area,  # square feet: area * 10.7639104
            #     building=df_poi.loc[i, 'building'] or "",
            #     amenity=df_poi.loc[i, 'amenity'] or "",
            #     centroid=df_poi.loc[i, 'centroid'],
            #     geometry=df_poi.loc[i, "geometry"]
            # )
            poi_dict[poi_id] = asdict(poi)
        except Exception as e:
            print(f"  : Unable to create poi: {poi_id}, error: {e}")
    return poi_dict


def _create_zone_from_dataframe_by_geometry(df_zone: pd.DataFrame) -> dict[int, Zone]:
    """Create Zone from df_zone.

    Args:
        df_zone (pd.DataFrame): the dataframe of zone from zone.csv, the required fields are: [zone_id, geometry]

    Returns:
        dict[int, Zone]: a dict of Zones.{zone_id: Zone}
    """
    df_zone = df_zone.reset_index(drop=True)
    col_names = df_zone.columns.tolist()

    if "zone_id" in col_names:
        col_names.remove("zone_id")

    # get node dataclass fields
    # Get the list of attribute names
    zone_attr_names = [f.name for f in fields(Zone)]

    # check difference between node_attr_names and col_names
    diff = list(set(col_names) - set(zone_attr_names))

    # create attributes for node class if diff is not empty
    if diff:
        diff_attr = [(val, Any, "") for val in diff]
        Zone_ext = extend_dataclass(Zone, diff_attr)
    else:
        Zone_ext = Zone

    zone_dict = {}

    for i in range(len(df_zone)):
        try:
            zone_id = df_zone.loc[i, 'zone_id']
            zone_geometry = df_zone.loc[i, 'geometry']

            zone_geometry_shapely = shapely.from_wkt(zone_geometry)
            centroid_wkt = zone_geometry_shapely.centroid.wkt
            x_coord = zone_geometry_shapely.centroid.x
            y_coord = zone_geometry_shapely.centroid.y

            zone = Zone_ext()

            for col in col_names:
                setattr(zone, col, df_zone.loc[i, col])

            zone.id = zone_id
            zone.name = zone_id
            zone.x_coord = x_coord
            zone.y_coord = y_coord
            zone.centroid = centroid_wkt
            zone.x_min = zone_geometry_shapely.bounds[0]
            zone.y_min = zone_geometry_shapely.bounds[1]
            zone.x_max = zone_geometry_shapely.bounds[2]
            zone.y_max = zone_geometry_shapely.bounds[3]

            # zone = Zone(
            #     id=zone_id,
            #     name=zone_id,
            #     x_coord=x_coord,
            #     y_coord=y_coord,
            #     centroid=centroid_wkt,
            #     x_max=zone_geometry_shapely.bounds[2],
            #     x_min=zone_geometry_shapely.bounds[0],
            #     y_max=zone_geometry_shapely.bounds[3],
            #     y_min=zone_geometry_shapely.bounds[1],
            #     node_id_list=[],
            #     poi_id_list=[],
            #     production=0,
            #     attraction=0,
            #     production_fixed=0,
            #     attraction_fixed=0,
            #     geometry=zone_geometry
            # )

            zone_dict[zone_id] = asdict(zone)
        except Exception as e:
            print(f"  : Unable to create zone: {zone_id}, error: {e}")
    return zone_dict


def _create_zone_from_dataframe_by_centroid(df_zone: pd.DataFrame) -> dict[int, Zone]:
    """Create Zone from df_zone.

    Args:
        df_zone (pd.DataFrame): the dataframe of zone from zone.csv, the required fields are: [zone_id, geometry]

    Returns:
        dict[int, Zone]: a dict of Zones.{zone_id: Zone}
    """
    df_zone = df_zone.reset_index(drop=True)
    col_names = df_zone.columns.tolist()

    if "zone_id" in col_names:
        col_names.remove("zone_id")

    # get node dataclass fields
    # Get the list of attribute names
    zone_attr_names = [f.name for f in fields(Zone)]

    # check difference between node_attr_names and col_names
    diff = list(set(col_names) - set(zone_attr_names))

    # create attributes for node class if diff is not empty
    if diff:
        diff_attr = [(val, Any, "") for val in diff]
        Zone_ext = extend_dataclass(Zone, diff_attr)
    else:
        Zone_ext = Zone

    zone_dict = {}

    for i in range(len(df_zone)):
        try:
            zone_id = df_zone.loc[i, 'zone_id']
            x_coord = df_zone.loc[i, 'x_coord']
            y_coord = df_zone.loc[i, 'y_coord']

            # load zone geometry
            try:
                zone_geometry = df_zone.loc[i, 'geometry']
            except Exception:
                zone_geometry = ""

            zone_centroid_shapely = shapely.Point(x_coord, y_coord)
            centroid_wkt = zone_centroid_shapely.wkt

            zone = Zone_ext()

            for col in col_names:
                setattr(zone, col, df_zone.loc[i, col])

            zone.id = zone_id
            zone.name = zone_id
            zone.centroid = centroid_wkt
            zone.geometry = zone_geometry

            # zone = Zone(
            #     id=zone_id,
            #     name=zone_id,
            #     x_coord=x_coord,
            #     y_coord=y_coord,
            #     centroid=centroid_wkt,
            #     node_id_list=[],
            #     poi_id_list=[],
            #     production=0,
            #     attraction=0,
            #     production_fixed=0,
            #     attraction_fixed=0,
            #     geometry=zone_geometry
            # )

            zone_dict[zone_id] = asdict(zone)
        except Exception as e:
            print(f"  : Unable to create zone: {zone_id}, error: {e}")
    return zone_dict


# main functions for reading node, poi, zone files and network


@func_running_time
def read_node(node_file: str = "", cpu_cores: int = 1, verbose: bool = False) -> dict[int: Node]:
    """Read node.csv file and return a dict of nodes.

    Args:
        node_file (str, optional): node file path. Defaults to "".
        cpu_cores (int, optional): number of cpu cores for parallel processing. Defaults to 1.
        verbose (bool, optional): print processing information. Defaults to False.

    Raises:
        FileNotFoundError: File: {node_file} does not exist.

    Returns:
        dict: a dict of nodes.

    Examples:
        >>> node_dict = read_node(node_file = r"../dataset/ASU/node.csv")
        >>> node_dict[1]
        Node(id=1, zone_id=0, x_coord=0.0, y_coord=0.0, is_boundary=0, geometry='POINT (0 0)',...)

        # if node_file does not exist, raise error
        >>> node_dict = read_node(node_file = r"../dataset/ASU/node.csv")
        FileNotFoundError: File: ../dataset/ASU/node.csv does not exist.
    """

    # convert path to linux path
    node_file = path2linux(node_file)

    # check if node_file exists
    if not os.path.exists(node_file):
        raise FileNotFoundError(f"File: {node_file} does not exist.")

    # read node.csv with specified columns and chunksize for iterations
    node_required_cols = pkg_settings["node_fields"]
    chunk_size = pkg_settings["data_chunk_size"]

    # read first two rows to check whether required fields are in node.csv
    df_node_2rows = pd.read_csv(node_file, nrows=2)
    col_names = df_node_2rows.columns.tolist()

    if "zone_id" in col_names and "zone_id" not in node_required_cols:
        node_required_cols.append("zone_id")

    if verbose:
        print(f"  : Reading node.csv with specified columns: {node_required_cols} \
                    \n    and chunksize {chunk_size} for iterations...")

    try:
        # Get total rows in poi.csv and calculate total chunks
        total_rows = sum(1 for _ in open(node_file)) - 1  # Exclude header row
        total_chunks = total_rows // chunk_size + 1
        df_node_chunk = pd.read_csv(node_file, usecols=node_required_cols, chunksize=chunk_size)
    except Exception as e:
        raise Exception(f"Error: Unable to read node.csv file for: {e}")

    if verbose:
        print(f"  : Parallel creating Nodes using Pool with {cpu_cores} CPUs. Please wait...")

    node_dict_final = {}

    # Parallel processing using Pool
    with Pool(cpu_cores) as pool:
        # results = pool.map(_create_node_from_dataframe, df_node_chunk)
        results = list(tqdm(pool.imap(_create_node_from_dataframe, df_node_chunk), total=total_chunks))
        pool.close()
        pool.join()

    # results = process_map(_create_node_from_dataframe, df_node_chunk, max_workers=cpu_cores)

    for node_dict in results:
        node_dict_final.update(node_dict)

    if verbose:
        print(f"  : Successfully loaded node.csv: {len(node_dict_final)} Nodes loaded.")

    node_dict_final = {k: create_dataclass_from_dict("Node", v) for k, v in node_dict_final.items()}

    return node_dict_final


@func_running_time
def read_poi(poi_file: str = "", cpu_cores: int = 1, verbose: bool = False) -> dict[int: POI]:
    """Read poi.csv file and return a dict of POIs.

    Args:
        poi_file (str): The poi.csv file path. default is "".
        cpu_cores (int, optional): number of cpu cores for parallel processing. Defaults to 1.
        verbose (bool, optional): print processing information. Defaults to False.

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
    poi_required_cols = pkg_settings["poi_fields"]
    chunk_size = pkg_settings["data_chunk_size"]

    if verbose:
        print(f"  : Reading poi.csv with specified columns: {poi_required_cols} \
                    \n    and chunksize {chunk_size} for iterations...")
    try:
        # Get total rows in poi.csv and calculate total chunks
        total_rows = sum(1 for _ in open(poi_file)) - 1  # Exclude header row
        total_chunks = total_rows // chunk_size + 1

        df_poi_chunk = pd.read_csv(poi_file, usecols=poi_required_cols, chunksize=chunk_size, encoding='utf-8')
    except Exception:
        df_poi_chunk = pd.read_csv(poi_file, usecols=poi_required_cols, chunksize=chunk_size, encoding='latin-1')

    # Parallel processing using Pool
    if verbose:
        print(f"  : Parallel creating POIs using Pool with {cpu_cores} CPUs. Please wait...")

    poi_dict_final = {}

    with Pool(cpu_cores) as pool:
        # results = pool.map(_create_poi_from_dataframe, df_poi_chunk)
        results = list(tqdm(pool.imap(_create_poi_from_dataframe, df_poi_chunk), total=total_chunks))
        pool.close()
        pool.join()

    # results = process_map(_create_poi_from_dataframe, df_poi_chunk, max_workers=cpu_cores)

    for poi_dict in results:
        poi_dict_final.update(poi_dict)

    if verbose:
        print(f"  : Successfully loaded poi.csv: {len(poi_dict_final)} POIs loaded.")

    poi_dict_final = {k: create_dataclass_from_dict(
        "POI", v) for k, v in poi_dict_final.items()}

    return poi_dict_final


@func_running_time
def read_zone_by_geometry(zone_file: str = "", cpu_cores: int = 1, verbose: bool = False) -> dict[int: Zone]:
    """Read zone.csv file and return a dict of Zones.

    Raises:
        FileNotFoundError: _description_
        FileNotFoundError: _description_

    Args:
        zone_file (str, optional): the input zone file path. Defaults to "".
        cpu_cores (int, optional): number of cpu cores for parallel processing. Defaults to 1.
        verbose (bool, optional): print processing information. Defaults to False.

    Returns:
        _type_: _description_
    """

    # convert path to linux path
    zone_file = path2linux(zone_file)

    # check if zone_file exists
    if not os.path.exists(zone_file):
        raise FileNotFoundError(f"File: {zone_file} does not exist.")

    # load default settings for zone required fields and chunk size
    zone_required_cols = pkg_settings["zone_geometry_fields"]
    chunk_size = pkg_settings["data_chunk_size"]

    if verbose:
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
    if verbose:
        print(f"  : Parallel creating Zones using Pool with {cpu_cores} CPUs. Please wait...")

    zone_dict_final = {}

    with Pool(cpu_cores) as pool:
        results = pool.map(_create_zone_from_dataframe_by_geometry, df_zone_chunk)
        pool.close()
        pool.join()

    for zone_dict in results:
        zone_dict_final.update(zone_dict)

    if verbose:
        print(f"  : Successfully loaded zone.csv: {len(zone_dict_final)} Zones loaded.")

    zone_dict_final = {k: create_dataclass_from_dict(
        "POI", v) for k, v in zone_dict_final.items()}

    return zone_dict_final


@func_running_time
def read_zone_by_centroid(zone_file: str = "", cpu_cores: int = 1, verbose: bool = False) -> dict[int: Zone]:
    """Read zone.csv file and return a dict of Zones.

    Args:
        zone_file (str, optional): the input zone file path. Defaults to "".
        cpu_cores (int, optional): number of cpu cores for parallel processing. Defaults to 1.
        verbose (bool, optional): print processing information. Defaults to False.

    Raises:
        FileNotFoundError: File: {zone_file} does not exist.
        FileNotFoundError: Required column: {col} is not in zone.csv. Please make sure zone_required_cols in zone.csv.

    Returns:
        dict: a dict of Zones.
    """

    # convert path to linux path
    zone_file = path2linux(zone_file)

    # check if zone_file exists
    if not os.path.exists(zone_file):
        raise FileNotFoundError(f"File: {zone_file} does not exist.")

    # load default settings for zone required fields and chunk size
    zone_required_cols = pkg_settings["zone_centroid_fields"]
    chunk_size = pkg_settings["data_chunk_size"]

    if verbose:
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
    if verbose:
        print(f"  : Parallel creating Zones using Pool with {cpu_cores} CPUs. Please wait...")

    zone_dict_final = {}

    with Pool(cpu_cores) as pool:
        results = pool.map(_create_zone_from_dataframe_by_centroid, df_zone_chunk)
        pool.close()
        pool.join()

    for zone_dict in results:
        zone_dict_final.update(zone_dict)

    if verbose:
        print(f"  : Successfully loaded zone.csv: {len(zone_dict_final)} Zones loaded.")

    zone_dict_final = {k: create_dataclass_from_dict(
        "POI", v) for k, v in zone_dict_final.items()}

    return zone_dict_final


def read_network(input_folder: str = "", cpu_cores: int = 1, verbose: bool = False) -> dict[str: dict]:
    """Read node.csv and poi.csv files and return a dict of nodes and a dict of POIs.

    Args:
        input_folder (str, optional): required files within this folder. Defaults to current folder.
        cpu_cores (int, optional): number of cpu cores for parallel processing. Defaults to 1.
        verbose (bool, optional): print processing information. Defaults to False.

    Raises:
        FileNotFoundError: if input_folder does not exist.

    Returns:
        dict: a dict of nodes and a dict of POIs.

    Examples:
        >>> node_dict, poi_dict = read_network(input_folder = r"../dataset/ASU")
        >>> node_dict[1]
        Node(id=1, zone_id=0, x_coord=0.0, y_coord=0.0, production=0.0, attraction=0.0, is_boundary=0,
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
        raise FileNotFoundError(
            f"Required files: {pkg_settings['required_files']} are not satisfied, please check your input folder.")

    node_dict = read_node(input_folder + "/node.csv", cpu_cores, verbose=verbose)
    poi_dict = read_poi(input_folder + "/poi.csv", cpu_cores, verbose=verbose)

    if verbose:
        print(f"  : Successfully loaded node.csv and poi.csv: {len(node_dict)} Nodes and {len(poi_dict)} POIs.")

    return {"node_dict": node_dict, "poi_dict": poi_dict}
