# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 4th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import pandas as pd
from utils_lib import Node, POI


def read_node(node_file: str = "") -> dict:
    """Read node.csv file and return a dict of nodes.

    Args:
        node_file: The node.csv file path.

    Returns:
        A dict of nodes.

    """
    return None


def read_poi(poi_file: str = "") -> dict:
    """Read poi.csv file and return a dict of POIs.

    Args:
        poi_file: The poi.csv file path.

    Returns:
        A dict of POIs.

    """
    return None


def read_network(input_folder: str = "") -> dict:
    return None


if __name__ == "__main__":
    path_node = r"../dataset/ASU/node.csv"

    df_node = pd.read_csv(path_node)

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
        )




