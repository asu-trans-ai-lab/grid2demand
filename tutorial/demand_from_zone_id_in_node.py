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
    input_dir = r"../grid2demand/datasets/demand_from_zone_id_in_node/ASU/auto"

    # Initialize a GRID2DEMAND object, and specify the mode_type as "auto" in default
    net = gd.GRID2DEMAND(input_dir, use_zone_id=True, mode_type="auto")

    # Step 1: Load node and poi data from input directory
    net.load_network()

    # Step 2: Generate zone dictionary from node dictionary
    #   by specifying number of x blocks and y blocks
    net.taz2zone()

    # Step 3: Run gravity model to generate agent-based demand
    net.run_gravity_model()

    # Step 4: Output demand, agent, zone, zone_od_dist_table, zone_od_dist_matrix files
    net.save_results_to_csv(zone=True, node=True, poi=True, overwrite_file=False)
