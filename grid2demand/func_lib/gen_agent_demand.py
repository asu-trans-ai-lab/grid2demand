# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, September 28th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import pandas as pd
from random import choice, uniform
import math
from pyufunc import gmns_geo


def gen_agent_based_demand(node_dict: dict, zone_dict: dict,
                           path_demand: str = "", df_demand: pd.DataFrame = "",
                           agent_type: str = "v") -> pd.DataFrame:
    # either path_demand or df_demand must be provided

    # if path_demand is provided, read demand data from path_demand
    if path_demand:
        df_demand = pd.read_csv(path_demand)

    # if df_demand is provided, validate df_demand
    if df_demand.empty:
        print("Error: No demand data provided.")
        return pd.DataFrame()

    agent_lst = []
    for i in range(len(df_demand)):
        o_zone_id = df_demand.loc[i, 'o_zone_id']
        d_zone_id = df_demand.loc[i, 'd_zone_id']
        o_zone_name = df_demand.loc[i, 'o_zone_name']
        d_zone_name = df_demand.loc[i, 'd_zone_name']
        o_node_id = choice(zone_dict[o_zone_name].node_id_list + [""])
        d_node_id = choice(zone_dict[d_zone_name].node_id_list + [""])

        if o_node_id and d_node_id:
            rand_time = math.ceil(uniform(1, 60))
            if rand_time == 60:
                departure_time = "0800"
            elif rand_time < 10:
                departure_time = f"070{rand_time}"
            else:
                departure_time = f"07{rand_time}"

            agent_lst.append(
                gmns_geo.Agent(
                    id=i + 1,
                    agent_type=agent_type,
                    o_zone_id=o_zone_id,
                    d_zone_id=d_zone_id,
                    o_zone_name=o_zone_name,
                    d_zone_name=d_zone_name,
                    o_node_id=o_node_id,
                    d_node_id=d_node_id,
                    geometry=f"LINESTRING({node_dict[o_node_id].x_coord} {node_dict[o_node_id].y_coord}, {node_dict[d_node_id].x_coord} {node_dict[d_node_id].y_coord})",
                    departure_time=departure_time
                )
            )
    print("  : Successfully generated agent-based demand data.")
    return pd.DataFrame(agent_lst)