## Project description

GRID2DEMAND: A tool for generating zone-to-zone travel demand based on grid cells

## Introduction

Grid2demand is an open-source quick demand generation tool based on the trip generation and trip distribution methods of the standard 4-step travel model for teaching transportation planning and applications. By taking advantage of OSM2GMNS tool to obtain routable transportation network from OpenStreetMap, Grid2demand aims to further utilize Point of Interest (POI) data to construct trip demand matrix aligned with standard travel models.

You can get access to the introduction video with the link: [https://www.youtube.com/watch?v=EfjCERQQGTs&amp;t=1021s](https://www.youtube.com/watch?v=EfjCERQQGTs&t=1021s)

## Quick Start

Users can refer to the [code template and test data set](https://github.com/asu-trans-ai-lab/grid2demand) to have a quick start.

## Installation

```
pip install grid2demand
```

If you meet installation issues, please refer to the [user guide](https://github.com/asu-trans-ai-lab/grid2demand) for solutions.

## Simple Example

```python
from __future__ import absolute_import
from grid2demand import GRID2DEMAND


if __name__ == "__main__":

    # Step 0: Specify input directory, if not, use current working directory as default input directory
    input_dir = "./datasets/ASU"

    # Initialize a GRID2DEMAND object
    gd = GRID2DEMAND(input_dir)

    # Step 1: Load node and poi data from input directory
    node_dict, poi_dict = gd.load_network.values()

    # Step 2: Generate zone dictionary from node dictionary by specifying number of x blocks and y blocks
    zone_dict = gd.net2zone(node_dict, num_x_blocks=10, num_y_blocks=10)

    # # Generate zone based on grid size with 10 km width and 10km height for each zone
    # zone_dict = gd.net2zone(node_dict, cell_width=10, cell_height=10)

    # Step 3: synchronize geometry info between zone, node and poi
    #       add zone_id to node and poi dictionaries
    #       also add node_list and poi_list to zone dictionary
    updated_dict = gd.sync_geometry_between_zone_and_node_poi(zone_dict, node_dict, poi_dict)
    zone_dict_update, node_dict_update, poi_dict_update = updated_dict.values()

    # Step 4: Calculate zone-to-zone od distance matrix
    zone_od_distance_matrix = gd.calc_zone_od_distance_matrix(zone_dict_update)

    # Step 5: Generate poi trip rate for each poi
    poi_trip_rate = gd.gen_poi_trip_rate(poi_dict_update)

    # Step 6: Generate node production attraction for each node based on poi_trip_rate
    node_prod_attr = gd.gen_node_prod_attr(node_dict_update, poi_trip_rate)

    # Step 6.1: Calculate zone production and attraction based on node production and attraction
    zone_prod_attr = gd.calc_zone_prod_attr(node_prod_attr, zone_dict_update)

    # Step 7: Run gravity model to generate agent-based demand
    df_demand = gd.run_gravity_model(zone_prod_attr, zone_od_distance_matrix)

    # Step 8: generate agent-based demand
    df_agent = gd.gen_agent_based_demand(node_prod_attr, zone_prod_attr, df_demand=df_demand)

    # You can also view and edit the package setting by using gd.pkg_settings
    print(gd.pkg_settings)

    # Step 9: Output demand, agent, zone, zone_od_dist_table, zone_od_dist_matrix files to output directory
    gd.save_demand
    gd.save_agent
    gd.save_zone
    gd.save_zone_od_dist_table
    gd.save_zone_od_dist_matrix
```

## Visualization

Option 1: Open [QGIS](https://www.qgis.org/) and add Delimited Text Layer of the files.

Option 2: Upload files to the website of [ASU Trans+AI Lab](https://asu-trans-ai-lab.github.io/index.html#/) and view input and output files.

Option 3: Import input_agent.csv to [A/B Street](https://a-b-street.github.io/docs/howto/asu.html) and view dynamic simulation of the demand.

## User guide

Users can check the [user guide](https://github.com/asu-trans-ai-lab/grid2demand/blob/main/README.md) for a detailed introduction of grid2demand.

## Call for Contributions

The grid2demand project welcomes your expertise and enthusiasm!

Small improvements or fixes are always appreciated. If you are considering larger contributions to the source code, please contact us through email:

    Xiangyong Luo :  luoxiangyong01@gmail.com

    Dr. Xuesong Simon Zhou :  xzhou74@asu.edu

Writing code isn't the only way to contribute to grid2demand. You can also:

* review pull requests
* help us stay on top of new and old issues
* develop tutorials, presentations, and other educational materials
* develop graphic design for our brand assets and promotional materials
* translate website content
* help with outreach and onboard new contributors
* write grant proposals and help with other fundraising efforts

For more information about the ways you can contribute to grid2demand, visit [our GitHub](https://github.com/asu-trans-ai-lab/grid2demand). If you' re unsure where to start or how your skills fit in, reach out! You can ask by opening a new issue or leaving a comment on a relevant issue that is already open on GitHub.

## Citing grid2demand

If you use grid2demand in your research please use the following BibTeX entry:

```
Xiangyong Luo, Dustin Carlino, and Xuesong Simon Zhou. (2023). xyluo25/grid2demand: new lease to v0.3.5-rc.2 (0.3.5-rc.2). Zenodo. https://doi.org/10.5281/zenodo.8397105
```
