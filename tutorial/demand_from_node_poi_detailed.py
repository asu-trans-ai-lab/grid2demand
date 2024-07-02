# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 11th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

from __future__ import absolute_import
from pathlib import Path
import os

try:
    import grid2demand as gd
except ImportError:
    root_path = Path(os.path.abspath(__file__)).parent.parent
    os.chdir(root_path)
    import grid2demand as gd


if __name__ == "__main__":

    # Step 0: Specify input directory
    input_dir = r"datasets\demand_from_grid\dubai"

    # Initialize a GRID2DEMAND object
    net = gd.GRID2DEMAND(input_dir=input_dir)

    # NOTE: You can also view and edit the package setting by using gd.pkg_settings
    print(net.pkg_settings)

    # Step 1: Load node and poi data from input directory
    net.load_network()

    # NOTE: you can view loaded node and poi data by using the following attributes
    # net.node_dict
    # net.poi_dict

    # Step 2: Generate zone
    #   by specifying number of x blocks and y blocks
    net.net2zone(num_x_blocks=10, num_y_blocks=10)
    # net.net2zone(net.node_dict, num_x_blocks=10, num_y_blocks=10)

    # or generate zone based on grid size with 10 km width and 10 km height for each zone
    # net.net2zone(cell_width=10, cell_height=10, unit='km')

    # NOTE: you can view generated zone data by using the following attributes
    # net.zone_dict

    # Step 3: synchronize geometry info between zone, node and poi
    #       add zone_id to node and poi dictionaries
    #       also add node_list and poi_list to zone dictionary

    net.sync_geometry_between_zone_and_node_poi()

    # Step 4: Calculate zone-to-zone od distance matrix
    net.calc_zone_od_distance_matrix()

    # NOTE: you can view zone-to-zone od distance matrix by using the following attributes
    # net.zone_od_dist_matrix

    # Step 5: Generate poi trip rate for each poi
    net.gen_poi_trip_rate(trip_rate_file="", trip_purpose=1)

    # Step 6: Generate node production attraction for each node based on poi_trip_rate
    net.gen_node_prod_attr(node_dict=net.node_dict, poi_dict=net.poi_dict)

    # Step 6.1: Calculate zone production and attraction based on node production and attraction
    net.calc_zone_prod_attr()

    # Step 7: Run gravity model to generate agent-based demand
    net.run_gravity_model(alpha=28507, beta=-0.02, gamma=0.123)

    # Step 8: generate agent-based demand
    net.gen_agent_based_demand()

    # Step 9: Output demand, agent, zone, zone_od_dist_table, zone_od_dist_matrix files
    net.save_results_to_csv()
