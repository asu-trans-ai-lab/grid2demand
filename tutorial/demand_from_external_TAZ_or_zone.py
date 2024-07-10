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
    input_dir = r"C:\Users\xyluo25\anaconda3_workspace\001_GitHub\grid2demand\datasets\demand_from_TAZ\SF"

    # Initialize a GRID2DEMAND object
    net = gd.GRID2DEMAND(input_dir=input_dir, verbose=True)

    # Step 1: Load node and poi data from input directory
    net.load_network()

    # Step 2: Generate zone dictionary from zone.csv file
    net.taz2zone()

    # Step 3: Run gravity model to generate agent-based demand
    net.run_gravity_model()

    # Step 4: Output demand, agent, zone, zone_od_dist_table, zone_od_dist_matrix files
    net.save_results_to_csv(node=True, poi=False, zone=False, overwrite_file=False)

    def generate_path_flow(input_dir: str = "",
                           load_demand: bool = True,
                           length_unit: str = 'meter',
                           speed_unit: str = 'kph',
                           col_gen_num: int = 10,
                           col_update_num: int = 10) -> None:

        # check if settings.yml and setting.csv exist
        # if not exist, download from GitHub repository

        import path4gmns as pg
        import pyufunc as pf

        path_settings_yaml = "settings.yml"
        path_settings_csv = "settings.csv"

        if not os.path.exists(path_settings_yaml):
            print("Downloading settings.yml from GitHub repository...")
            pf.github_file_downloader(repo_url=r"https://github.com/jdlph/Path4GMNS/blob/master/data/Sioux_Falls/settings.yml",
                                      output_dir=input_dir,
                                      flatten=True)

        if not os.path.exists(path_settings_csv):
            print("Downloading settings.csv from GitHub repository...")
            pf.github_file_downloader(repo_url=r"https://github.com/jdlph/Path4GMNS/blob/master/data/Sioux_Falls/settings.csv",
                                      output_dir=input_dir,
                                      flatten=True)

        print("  :Using path4gmns to perform column generation...\n")
        # path4gmns: path flow
        network = pg.read_network(input_dir=input_dir,
                                  load_demand=load_demand,
                                  length_unit=length_unit,
                                  speed_unit=speed_unit)

        pg.perform_column_generation(col_gen_num, col_update_num, network)

        # if you do not want to include geometry info in the output file,
        # use pg.output_columns(network, False)
        pg.output_columns(network, output_dir=input_dir)
        pg.output_link_performance(network, output_dir=input_dir)

        return None

    input_dir_flow = r"C:\Users\xyluo25\anaconda3_workspace\001_GitHub\grid2demand\datasets\demand_from_TAZ\SF_demo"
    generate_path_flow(input_dir=input_dir_flow,
                       load_demand=True,
                       length_unit='meter',
                       speed_unit='kph',
                       col_gen_num=10,
                       col_update_num=10)
