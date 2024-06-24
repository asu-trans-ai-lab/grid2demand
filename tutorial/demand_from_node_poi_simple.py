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

    # Step 0: Specify input files
    input_dir = r"C:\Users\xyluo25\anaconda3_workspace\001_GitHub\grid2demand\datasets\dubai"

    # Initialize a GRID2DEMAND object
    net = gd.GRID2DEMAND()

    # Step 1: Load node and poi data from input directory
    net.load_network(input_dir=input_dir)

    # Step 2: Generate zone dictionary from node dictionary
    net.net2zone(num_x_blocks=10, num_y_blocks=10)

    # Step 3: Run gravity model to generate agent-based demand
    net.run_gravity_model()

    # Step 4: Output demand, agent, zone, zone_od_dist_table, zone_od_dist_matrix files
    net.save_results_to_csv(output_dir="./")
