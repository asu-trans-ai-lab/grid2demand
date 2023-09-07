# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 4th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

from __future__ import absolute_import
import pandas as pd
from grid2demand.utils_lib import Node, POI
import shapely


def read_node(node_file: str = "") -> dict:
    """Read node.csv file and return a dict of nodes.

    Args:
        node_file: The node.csv file path.

    Returns:
        A dict of nodes.

    Examples:
        >>> node_dict = read_node(node_file = r"../dataset/ASU/node.csv")
        >>> node_dict[1]
        Node(id=1, zone_id=0, x_coord=0.0, y_coord=0.0, production=0.0, attraction=0.0, boundary_flag=0,
        poi_id=-1, activity_type='residential', activity_location_tab='residential')
    """

    df_node = pd.read_csv(node_file)

    # check if poi_id is empty
    if len(df_node["poi_id"].unique().tolist()) == 1:
        print("poi_id is empty, It could lead to empty demand volume and zero agent. Please check your node.csv file.")

    node_dict = {}
    for i in range(len(df_node)):

        # check activity location tab
        activity_type = df_node.loc[i, 'activity_type']
        boundary_flag = df_node.loc[i, 'is_boundary']
        if activity_type in ["residential", "poi"]:
            activity_location_tab = activity_type
        elif boundary_flag == 1:
            activity_location_tab = "boundary"
        else:
            activity_location_tab = ''

        node_dict[df_node.loc[i, 'node_id']] = Node(
            id=df_node.loc[i, 'node_id'],
            activity_type=activity_type,
            activity_location_tab=activity_location_tab,
            x_coord=df_node.loc[i, 'x_coord'],
            y_coord=df_node.loc[i, 'y_coord'],
            poi_id=df_node.loc[i, 'poi_id'],
            boundary_flag=boundary_flag,
            geometry=shapely.Point(df_node.loc[i, 'x_coord'], df_node.loc[i, 'y_coord'])
        )

    return node_dict


def read_poi(poi_file: str = "") -> dict:
    """Read poi.csv file and return a dict of POIs.

    Args:
        poi_file: The poi.csv file path.

    Returns:
        A dict of POIs.

    """

    df_poi = pd.read_csv(poi_file)

    poi_dict = {}
    for i in range(len(df_poi)):
        # get centroid
        centroid = shapely.from_wkt(df_poi.loc[i, 'centroid'])

        # check area
        area = df_poi.loc[i, 'area']
        if area > 90000:
            area = 0

        poi_dict[df_poi.loc[i, 'poi_id']] = POI(
            id=df_poi.loc[i, 'poi_id'],
            x_coord=centroid.x,
            y_coord=centroid.y,
            area=[area,  area * 10.7639104], # square meter and square feet
            poi_type=df_poi.loc[i, 'building'] or "",
            geometry=df_poi.loc[i, "geometry"]
        )

    return poi_dict


def read_network(input_folder: str = "") -> dict:
    return None


if __name__ == "__main__":
    path_node = r"../dataset/ASU/node.csv"
    path_poi = r"../dataset/ASU/poi.csv"


