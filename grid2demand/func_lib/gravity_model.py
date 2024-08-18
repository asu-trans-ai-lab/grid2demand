# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, September 7th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import numpy as np
from grid2demand.utils_lib.pkg_settings import pkg_settings


def calc_zone_production_attraction(node_dict: dict, poi_dict: dict, zone_dict: dict, verbose: bool = False) -> dict:
    # calculate zone production and attraction based on node production and attraction
    for zone_name in zone_dict:

        # calculate zone production and attraction based on node production and attraction
        if zone_dict[zone_name].node_id_list:
            for node_id in zone_dict[zone_name].node_id_list:
                try:
                    zone_dict[zone_name].production += node_dict[node_id].production
                    zone_dict[zone_name].attraction += node_dict[node_id].attraction
                except KeyError:
                    continue

    # calculate zone production and attraction based on poi
    for zone_name in zone_dict:
        if zone_dict[zone_name].poi_id_list:
            for poi_id in zone_dict[zone_name].poi_id_list:
                try:
                    poi_trip_rate = poi_dict[poi_id].trip_rate
                    print(f"poi_{poi_id}: ", poi_dict[poi_id].area)
                    for key in poi_trip_rate:
                        if "production_rate" in key:
                            zone_dict[zone_name].production += poi_trip_rate[key] * \
                                poi_dict[poi_id].area / 1000
                        if "attraction_rate" in key:
                            zone_dict[zone_name].attraction += poi_trip_rate[key] * \
                                poi_dict[poi_id].area / 1000

                    # zone_dict[zone_name].production += poi_dict[poi_id].production
                    # zone_dict[zone_name].attraction += poi_dict[poi_id].attraction
                except KeyError:
                    continue

    if verbose:
        print("  : Successfully calculated zone production and attraction based on node production and attraction.")

    return zone_dict


def calc_zone_od_friction_attraction(zone_od_friction_matrix_dict: dict,
                                     zone_dict: dict,
                                     verbose: bool = False) -> dict:
    zone_od_friction_attraction_dict = {}
    for zone_name, friction_val in zone_od_friction_matrix_dict.items():
        if zone_name[0] not in zone_od_friction_attraction_dict:
            zone_od_friction_attraction_dict[zone_name[0]] = friction_val * zone_dict[zone_name[1]].attraction
        else:
            zone_od_friction_attraction_dict[zone_name[0]] += friction_val * zone_dict[zone_name[1]].attraction

    if verbose:
        print("  : Successfully calculated zone od friction attraction.")

    return zone_od_friction_attraction_dict


def run_gravity_model(zone_dict: dict,
                      zone_od_dist_matrix: dict,
                      trip_purpose: int = 1,
                      alpha: float = 28507,
                      beta: float = -0.02,
                      gamma: float = -0.123,
                      verbose: bool = False) -> dict:
    # if trip purpose is specified in trip_purpose_dict, use the default value
    # otherwise, use the user-specified value
    trip_purpose_dict = pkg_settings.get("trip_purpose_dict")

    if trip_purpose in trip_purpose_dict:
        alpha = trip_purpose_dict[trip_purpose]["alpha"]
        beta = trip_purpose_dict[trip_purpose]["beta"]
        gamma = trip_purpose_dict[trip_purpose]["gamma"]

    # update zone attraction and production
    # zone_dict = calc_zone_production_attraction(node_dict, zone_dict)

    # perform zone od friction matrix
    zone_od_friction_matrix_dict = {
        zone_name_pair: alpha * (od_dist["dist_km"] ** beta) * (
            np.exp(od_dist["dist_km"] * gamma)) if od_dist["dist_km"] != 0 else 0
        for zone_name_pair, od_dist in zone_od_dist_matrix.items()
    }

    # perform attraction calculation
    zone_od_friction_attraction_dict = calc_zone_od_friction_attraction(zone_od_friction_matrix_dict,
                                                                        zone_dict,
                                                                        verbose=verbose)

    # perform od trip flow (volume) calculation
    for zone_name_pair in zone_od_friction_matrix_dict:
        try:
            zone_od_dist_matrix[zone_name_pair]["volume"] = float(zone_dict[zone_name_pair[0]].production *
                                                                  zone_dict[zone_name_pair[1]].attraction *
                                                                  zone_od_friction_matrix_dict[zone_name_pair] /
                                                                  zone_od_friction_attraction_dict[zone_name_pair[0]])
        except Exception:
            zone_od_dist_matrix[zone_name_pair]["volume"] = 0

    # Generate demand.csv
    if verbose:
        print("  : Successfully run gravity model to generate demand.csv.")

    # return pd.DataFrame(list(zone_od_matrix_dict.values()))
    return zone_od_dist_matrix
