# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 11th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

from __future__ import absolute_import
import grid2demand as gd
from grid2demand import GRID2DEMAND


if __name__ == "__main__":
    path_node = "./dataset/ASU/node.csv"
    path_poi = "./dataset/ASU/poi.csv"
    path_dir = "./dataset/ASU"

    # Step 1: Load node and poi files from input directory
    # There are two ways to load node and poi files: 1. Load from input directory; 2. Load from specified path
    gd = GRID2DEMAND(path_dir)

    # Step 1.1: Load from input directory
    # will return a dict containing node and poi dictionaries: {'node_dict': node_dict, 'poi_dict': poi_dict}
    network_dict = gd.read_network(path_dir)

    # Step 1.2: Load from specified path
    node_dict = gd.read_node("./dataset/ASU/node.csv")
    poi_dict = gd.read_poi("./dataset/ASU/poi.csv")

    # Step 2: Generate zone dictionary from node dictionary by specifying number of x blocks and y blocks
    # To be noticed: num_x_blocks and num_y_blocks have higher priority than cell_width and cell_height
    # if num_x_blocks and num_y_blocks are specified, cell_width and cell_height will be ignored
    zone_dict = gd.net2zone(node_dict, num_x_blocks=10, num_y_blocks=10, cell_width=0, cell_height=0)

    # Step 3: synchronize zone with node and poi
    # will add zone_id to node and poi dictionaries
    # Will also add node_list and poi_list to zone dictionary
    # Step 3.1: synchronize zone with node
    zone_node_dict = gd.sync_zone_and_node_geometry(zone_dict, node_dict)
    zone_dict_update = zone_node_dict.get('zone_dict')
    node_dict_update = zone_node_dict.get('node_dict')

    # Step 3.2: synchronize zone with poi
    zone_poi_dict = gd.sync_zone_and_poi_geometry(zone_dict_update, poi_dict)
    zone_dict_update = zone_poi_dict.get('zone_dict')
    poi_dict_update = zone_poi_dict.get('poi_dict')

    # Step 4: Generate zone-to-zone od distance matrix
    zone_od_matrix = gd.calc_zone_od_matrix(zone_dict_update)

    # Step 5: Generate poi trip rate for each poi
    poi_trip_rate = gd.gen_poi_trip_rate(poi_dict_update)

    # Step 6: Generate node production attraction for each node based on poi_trip_rate
    node_prod_attr = gd.gen_node_prod_attr(node_dict_update, poi_trip_rate)

    # Step 6.1: Calculate zone production and attraction based on node production and attraction
    zone_prod_attr = gd.calc_zone_production_attraction(node_prod_attr, zone_dict_update)

    # Step 7: Run gravity model to generate agent-based demand
    df_demand = gd.run_gravity_model(zone_prod_attr, zone_od_matrix)

    # Step 8: generate agent-based demand
    df_agent = gd.gen_agent_based_demand(node_prod_attr, zone_dict_update, df_demand=df_demand)

    # You can also view and edit the package setting by using gd.pkg_settings
    print(gd.pkg_settings)
