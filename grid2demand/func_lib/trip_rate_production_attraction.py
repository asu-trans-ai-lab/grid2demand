# -*- coding:utf-8 -*-
##############################################################
# Created Date: Tuesday, September 12th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import pandas as pd
import os

from grid2demand.utils_lib.utils import path2linux
from grid2demand.utils_lib.pkg_settings import poi_purpose_prod_dict, poi_purpose_attr_dict


def gen_poi_trip_rate(poi_dict: dict,
                      trip_rate_file: str = "",
                      trip_purpose: int = 1) -> dict:
    """Generate trip rate for each poi.

    Args:
        poi_dict (dict): the dictionary of poi
        trip_rate_file (str, optional): poi trip rate file path. Defaults to "".
        trip_purpose (int, optional): the trip purpose. Defaults to 1. 1: HBW, 2: HBO, 3: NHB.

    Returns:
        dict: the dictionary of poi with trip rate

    Examples:
        >>> poi_dict = gd.read_poi("./dataset/ASU/poi.csv")
        >>> poi_trip_rate = gd.gen_poi_trip_rate(poi_dict, trip_rate_file="./dataset/ASU/trip_rate.csv", trip_purpose=1)
        >>> poi_trip_rate[0]
        POI(poi_id=0, poi_type='residential', x=0.0, y=0.0, area=(0.0, 0.0), trip_rate={'building': 'residential', 'unit_of_measure': '1,000 Sq. Ft. GFA', 'trip_purpose': 1, 'production_rate1': 10.0, 'attraction_rate1': 10.0, 'production_notes': 1, 'attraction_notes': 1})
    """

    default_flag = False

    # if no poi trip rate file provided, use default trip rate
    if not trip_rate_file:
        print("No trip rate file is provided, use default trip rate.")
        default_flag = True

    # validate trip rate file
    if not os.path.exists(path2linux(trip_rate_file)):
        print(f"File: {trip_rate_file} does not exist, use default trip rate.")
        default_flag = True

    if default_flag:
        for poi_id in poi_dict:
            poi_type = poi_dict[poi_id].poi_type

            # if poi_type in default setting, use the default trip rate
            # else use 0.1 as the trip rate for production
            if poi_type in poi_purpose_prod_dict:
                production_rate = poi_purpose_prod_dict[poi_type][trip_purpose]
                production_notes = 1
            else:
                production_rate = 0.1
                production_notes = 0

            # if poi_type in default setting, use the default trip rate
            # else use 0.1 as the trip rate for attraction
            if poi_type in poi_purpose_attr_dict:
                attraction_rate = poi_purpose_attr_dict[poi_type][trip_purpose]
                attraction_notes = 1
            else:
                attraction_rate = 0.1
                attraction_notes = 0

            # update poi_trip_rate in the poi_dict
            poi_dict[poi_id].trip_rate = {"building": poi_type, "unit_of_measure": '1,000 Sq. Ft. GFA',
                                          "trip_purpose": trip_purpose,
                                          f"production_rate{trip_purpose}": production_rate,
                                          f"attraction_rate{trip_purpose}": attraction_rate,
                                          "production_notes": production_notes,
                                          "attraction_notes": attraction_notes}
        return poi_dict

    # if valid input file is provided, use the trip rate in the file
    df_trip_rate = pd.read_csv(trip_rate_file)
    df_trip_rate_dict = {
        df_trip_rate.loc[i, 'building']: df_trip_rate.loc[i, :]
        for i in range(len(df_trip_rate))
    }

    for poi_id in poi_dict:
        poi_type = poi_dict[poi_id].poi_type
        if poi_type in df_trip_rate_dict:
            poi_dict[poi_id].trip_rate = df_trip_rate_dict[poi_type].to_dict()

    return poi_dict


def gen_node_prod_attr(node_dict: dict,
                       poi_dict: dict,
                       residential_production: float = 10.0,
                       residential_attraction: float = 10.0,
                       boundary_production: float = 1000.0,
                       boundary_attraction: float = 1000.0) -> dict:
    """Generate production and attraction for each node.

    Args:
        node_dict (dict): Node dictionary
        poi_dict (dict): POI dictionary
        residential_production (float, optional): the production of residential area. Defaults to 10.0.
        residential_attraction (float, optional): the attraction of residential area. Defaults to 10.0.
        boundary_production (float, optional): the boundary production, also known as the outside production. Defaults to 1000.0.
        boundary_attraction (float, optional): the boundary attraction, also known as the outside attraction. Defaults to 1000.0.

    Returns:
        dict: Node dictionary with generated production and attraction

    Examples:
        >>> node_dict = gd.read_node("./dataset/ASU/node.csv")
        >>> poi_dict = gd.read_poi("./dataset/ASU/poi.csv")
        >>> node_prod_attr = gd.gen_node_prod_attr(node_dict, poi_dict, residential_production=10.0, residential_attraction=10.0, boundary_production=1000.0, boundary_attraction=1000.0)
        >>> node_prod_attr[1]
        Node(node_id=1, poi_id=0, x=0.0, y=0.0, activity_location_tab='residential', production=10.0, attraction=10.0)
    """

    for node in node_dict.values():
        if node.activity_location_tab == "residential":
            node.production = residential_production
            node.attraction = residential_attraction
        elif node.activity_location_tab == "boundary":
            node.production = boundary_production
            node.attraction = boundary_attraction
        elif node.activity_location_tab == "poi":
            if node.poi_id in poi_dict:
                poi_trip_rate = poi_dict[node.poi_id].trip_rate
                for key in poi_trip_rate:
                    if "production_rate" in key:
                        node.production = poi_trip_rate[key] * \
                            poi_dict[node.poi_id].area[1] / 1000
                    if "attraction_rate" in key:
                        node.attraction = poi_trip_rate[key] * \
                            poi_dict[node.poi_id].area[1] / 1000
        else:
            node.production = 0
            node.attraction = 0
    return node_dict


def gen_zone_prod_attr(zone_dict: dict, node_dict: dict) -> dict:
    pass