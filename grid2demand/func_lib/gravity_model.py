# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, September 7th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import numpy as np
from grid2demand.utils_lib.pkg_settings import trip_purpose_dict


def run_gravity_model(node_dict: dict,
                      zone_od_matrix_dict: dict,
                      trip_purpose: int = 1,
                      alpha: float = 28507,
                      beta: float = -0.02,
                      gamma: float = -0.123):
    # sourcery skip: assign-if-exp, dict-comprehension, use-dict-items
    # if trip purpose is specified in trip_purpose_dict, use the default value
    # otherwise, use the user-specified value
    if trip_purpose in trip_purpose_dict:
        alpha = trip_purpose_dict[trip_purpose]["alpha"]
        beta = trip_purpose_dict[trip_purpose]["beta"]
        gamma = trip_purpose_dict[trip_purpose]["gamma"]

    # update zone attraction and production

    # perform zone od friction matrix
    zone_od_friction_matrix_dict = {}

    for zone_name_pair in zone_od_matrix_dict:

        od_dist = zone_od_matrix_dict[zone_name_pair]
        if od_dist != 0:
            zone_od_friction_matrix_dict[zone_name_pair] = alpha * (od_dist ** beta) * (np.exp(od_dist * gamma))
        else:
            zone_od_friction_matrix_dict[zone_name_pair] = 0

    # update od matrix distance by adding one key-value pair: volume: value
