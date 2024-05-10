# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 11th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

from __future__ import absolute_import
import grid2demand as gd
import pandas as pd

if __name__ == "__main__":

    # Step 0: Specify input directory, if not, use current working directory as default input directory
    input_dir = "./datasets/DC_Downtown"

    # Initialize a GRID2DEMAND object
    gd_instance = gd.GRID2DEMAND(input_dir)

    # Step 1: Load node and poi data from input directory
    node_dict, poi_dict = gd_instance.load_network.values()

    # Step 2: Generate zone dictionary from zone.csv file
    #   please note, if you use this function,
    #   you need to make sure the zone.csv file is in the input directory
    #   this will generate zones based on your own TAZs
    #   and zone.csv requires at least two columns: zone_id and geometry
    zone_dict = gd_instance.taz2zone()

    # Step 3: synchronize geometry info between zone, node and poi
    #       add zone_id to node and poi dictionaries
    #       also add node_list and poi_list to zone dictionary
    updated_dict = gd_instance.sync_geometry_between_zone_and_node_poi(
        zone_dict, node_dict, poi_dict)
    zone_dict_update, node_dict_update, poi_dict_update = updated_dict.values()

    # Step 4: Calculate zone-to-zone od distance matrix
    zone_od_dist_matrix = gd_instance.calc_zone_od_distance_matrix(
        zone_dict_update)

    # Step 5: Generate poi trip rate for each poi
    poi_trip_rate = gd_instance.gen_poi_trip_rate(poi_dict_update)

    # Step 6: Generate node production attraction for each node based on poi_trip_rate
    node_prod_attr = gd_instance.gen_node_prod_attr(
        node_dict_update, poi_trip_rate)

    # Step 6.1: Calculate zone production and attraction based on node production and attraction
    zone_prod_attr = gd_instance.calc_zone_prod_attr(
        node_prod_attr, zone_dict_update)

    # Step 7: Run gravity model to generate agent-based demand
    df_demand = gd_instance.run_gravity_model(
        zone_prod_attr, zone_od_dist_matrix)

    # Step 8: generate agent-based demand
    df_agent = gd_instance.gen_agent_based_demand(
        node_prod_attr, zone_prod_attr, df_demand=df_demand)

    # You can also view and edit the package setting by using gd.pkg_settings
    print(gd.pkg_settings)

    # Step 9: Output demand, agent, zone, zone_od_dist_table, zone_od_dist_matrix files
    gd_instance.save_demand
    gd_instance.save_agent
    gd_instance.save_zone
    gd_instance.save_zone_od_dist_table
    gd_instance.save_zone_od_dist_matrix
