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
    # input_dir = "./datasets/DC_Downtown"
    input_dir = "./datasets/Tuscon_zone"
    zone = "./datasets/Tuscon_zone/zone.csv"
    node = "./datasets/Tuscon_zone/node.csv"

    # Initialize a GRID2DEMAND object
    net = gd.GRID2DEMAND(node_file=node, zone_file=zone)

    # Step 1: Load node and poi data from input directory
    net.load_network()

    # Step 2: Generate zone dictionary from zone.csv file
    zone_dict = net.taz2zone()

    # Step 3: synchronize geometry info between zone, node and poi
    net.sync_geometry_between_zone_and_node_poi()

    # Step 7: Run gravity model to generate agent-based demand
    net.run_gravity_model()

    net.save_results_to_csv()
