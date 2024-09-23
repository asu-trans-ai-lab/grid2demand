# -*- coding:utf-8 -*-
##############################################################
# Created Date: Tuesday, September 12th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import pandas as pd
import os

from grid2demand.utils_lib.pkg_settings import pkg_settings
from pyufunc import path2linux


def gen_poi_trip_rate(poi_dict: dict,
                      trip_rate_file: str = "",
                      trip_purpose: int = 1,
                      verbose: bool = False) -> dict:
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
        POI(poi_id=0, poi_type='residential', x=0.0, y=0.0, area=0.0, trip_rate={'building': 'residential',
        'unit_of_measure': '1,000 Sq. Ft. GFA', 'trip_purpose': 1, 'production_rate1': 10.0,
        'attraction_rate1': 10.0, 'production_notes': 1, 'attraction_notes': 1})
    """
    poi_purpose_prod_dict = pkg_settings.get("poi_purpose_prod_dict")
    poi_purpose_attr_dict = pkg_settings.get("poi_purpose_attr_dict")

    default_flag = False

    # if no poi trip rate file provided, use default trip rate
    if not trip_rate_file:
        print("  No trip rate file provided, use default trip rate.")
        default_flag = True
    # if trip rate file provided is not valid, use default trip rate
    elif not os.path.isfile(path2linux(trip_rate_file)):
        print(f"  : {trip_rate_file} does not exist, use default trip rate.")
        default_flag = True

    if default_flag:
        for poi_id in poi_dict:
            building = poi_dict[poi_id]["building"]

            # if poi_type in default setting, use the default trip rate
            # else use 0.1 as the trip rate for production
            if building in poi_purpose_prod_dict:
                production_rate = poi_purpose_prod_dict[building][trip_purpose]
                production_notes = 1
            else:
                production_rate = 0.1
                production_notes = 0

            # if poi_type in default setting, use the default trip rate
            # else use 0.1 as the trip rate for attraction
            if building in poi_purpose_attr_dict:
                attraction_rate = poi_purpose_attr_dict[building][trip_purpose]
                attraction_notes = 1
            else:
                attraction_rate = 0.1
                attraction_notes = 0

            # update poi_trip_rate in the poi_dict
            poi_dict[poi_id]["trip_rate"] = {"building": building, "unit_of_measure": '1,000 Sq. Ft. GFA',
                                          "trip_purpose": trip_purpose,
                                          f"production_rate{trip_purpose}": production_rate,
                                          f"attraction_rate{trip_purpose}": attraction_rate,
                                          "production_notes": production_notes,
                                          "attraction_notes": attraction_notes}
        print("  : Successfully generated poi trip rate with default setting.")
        return poi_dict

    # if valid input file is provided, use the trip rate in the file
    df_trip_rate = pd.read_csv(trip_rate_file)
    df_trip_rate_dict = {
        df_trip_rate.loc[i, 'building']: df_trip_rate.loc[i, :]
        for i in range(len(df_trip_rate))
    }

    for poi_id in poi_dict:
        building = poi_dict[poi_id]["building"]
        if building in df_trip_rate_dict:
            poi_dict[poi_id].trip_rate = df_trip_rate_dict[building].to_dict()

    if verbose:
        print(f"  : Successfully generated poi trip rate from {trip_rate_file}.")

    return poi_dict


def gen_node_prod_attr(node_dict: dict,
                       poi_dict: dict,
                       residential_production: float = 10.0,
                       residential_attraction: float = 10.0,
                       boundary_production: float = 1000.0,
                       boundary_attraction: float = 1000.0,
                       verbose: bool = False) -> dict:
    # sourcery skip: merge-duplicate-blocks, remove-redundant-if
    """Generate production and attraction for each node.

    Args:
        node_dict (dict): Node dictionary
        poi_dict (dict): POI dictionary
        residential_production (float, optional): the production of residential area. Defaults to 10.0.
        residential_attraction (float, optional): the attraction of residential area. Defaults to 10.0.
        boundary_production (float, optional): boundary production, also outside production. Defaults to 1000.0.
        boundary_attraction (float, optional): boundary attraction, also the outside attraction. Defaults to 1000.0.

    Returns:
        dict: Node dictionary with generated production and attraction

    Examples:
        >>> node_dict = gd.read_node("./dataset/ASU/node.csv")
        >>> poi_dict = gd.read_poi("./dataset/ASU/poi.csv")
        >>> node_prod_attr = gd.gen_node_prod_attr(node_dict, poi_dict, residential_production=10.0,
        residential_attraction=10.0, boundary_production=1000.0, boundary_attraction=1000.0)
        >>> node_prod_attr[1]
        Node(node_id=1, poi_id=0, x=0.0, y=0.0, activity_type='residential', production=10.0, attraction=10.0)
    """

    for node in node_dict.values():
        if node["activity_type"] == "residential":
            node["production"] = residential_production
            node["attraction"] = residential_attraction
        elif node["activity_type"] == "boundary":
            node["production"] = boundary_production
            node["attraction"] = boundary_attraction
        elif node["activity_type"] == "poi":
            if node["poi_id"] in poi_dict:
                poi_trip_rate = poi_dict[node["poi_id"]]["trip_rate"]
                for key in poi_trip_rate:
                    if "production_rate" in key:
                        node["production"] = poi_trip_rate[key] * \
                            poi_dict[node["poi_id"]].area / 1000
                    if "attraction_rate" in key:
                        node["attraction"] = poi_trip_rate[key] * \
                            poi_dict[node["poi_id"]].area / 1000
        elif node["_zone_id"] != -1:
            node["production"] = boundary_production
            node["attraction"] = boundary_attraction
        else:
            node["production"] = 50
            node["attraction"] = 50
    if verbose:
        print("  : Successfully generated production and attraction for each node based on poi trip rate.")

    return node_dict
