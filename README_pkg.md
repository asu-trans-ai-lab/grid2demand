## Project description

GRID2DEMAND: A tool for generating zone-to-zone travel demand based on grid cells or TAZs and gravity model

## Introduction

Grid2demand is an open-source quick demand generation tool based on the trip generation and trip distribution methods of the standard 4-step travel model for teaching transportation planning and applications. By taking advantage of OSM2GMNS tool to obtain route-able transportation network from OpenStreetMap, Grid2demand aims to further utilize Point of Interest (POI) data to construct trip demand matrix aligned with standard travel models.

You can get access to the introduction video with the link: [https://www.youtube.com/watch?v=EfjCERQQGTs&amp;t=1021s](https://www.youtube.com/watch?v=EfjCERQQGTs&t=1021s)

## Quick Start

Users can refer to the [code template and test data set](https://github.com/asu-trans-ai-lab/grid2demand) to have a quick start.

## Installation

```
pip install grid2demand
```

If you meet installation issues, please refer to the [user guide](https://github.com/asu-trans-ai-lab/grid2demand) for solutions.

## Simple Example

### Generate Demand with node.csv and poi.csv

1. Create zone from node.csv (the boundary of nodes), this will generate grid cells (num_x_blocks, num_y_blocks, or x length and y length in km for each grid cell)
2. Generate demands for between zones (utilize nodes and pois)

```python
from __future__ import absolute_import
import grid2demand as gd

if __name__ == "__main__":

    # Specify input directory
    input_dir = "your-data-folder"

    # Initialize a GRID2DEMAND object
    net = gd.GRID2DEMAND(input_dir=input_dir)

    # load network: node and poi
    net.load_network()

    # Generate zone dictionary from node dictionary by specifying number of x blocks and y blocks
    net.net2zone(num_x_blocks=10, num_y_blocks=10)
    # net.net2zone(cell_width=10, cell_height=10, unit="km")

    # Calculate demand by running gravity model
    net.run_gravity_model()

    # Save demand, zone, updated node, updated poi to csv
    net.save_results_to_csv()
```

# Generate Demand with node.csv, poi.csv and zone.csv (geometry filed in zone.csv)

```python
from __future__ import absolute_import
import grid2demand as gd

if __name__ == "__main__":

    # Specify input directory
    path_node = "your-path-to-node.csv"
    path_poi = "your-path-to-poi.csv"
    path_zone = "your-path-to-zone.csv"  # zone_id, geometry are required columns

    # Initialize a GRID2DEMAND object
    net = gd.GRID2DEMAND(zone_file = path_zone, node_file = path_node, poi_file = path_poi)

    # load network: node and poi
    net.load_network()

    # Generate zone
    net.taz2zone()

    # Calculate demand by running gravity model
    net.run_gravity_model()

    # Save demand, zone, updated node, updated poi to csv
    net.save_results_to_csv(overwrite_file=True)
```

# Generate Demand with node.csv, poi.csv and zone.csv (x_coord, y_coord fields represent zone centroids)

```python
from __future__ import absolute_import
import grid2demand as gd

if __name__ == "__main__":

    # Specify input directory
    path_node = "your-path-to-node.csv"
    path_poi = "your-path-to-poi.csv"
    path_zone = "your-path-to-zone.csv"  # zone_id, x_coord, y_coord are required columns

    # Initialize a GRID2DEMAND object
    net = gd.GRID2DEMAND(zone_file = path_zone, node_file = path_node, poi_file = path_poi)

    # load network: node and poi
    net.load_network()

    # Generate zone
    net.taz2zone()

    # Calculate demand by running gravity model
    net.run_gravity_model()

    # Save demand, zone, updated node, updated poi to csv
    net.save_results_to_csv(overwrite_file=True)
```

# Generate Demand with node.csv (if zone_id field exist, generated zone boundary cover zone_id that are not empty) and poi.csv

```python
from __future__ import absolute_import
import grid2demand as gd

if __name__ == "__main__":

    # Specify input directory
    path_node = "your-path-to-node.csv"  # make sure you have zone_id field in node.csv
    path_poi = "your-path-to-poi.csv"

    # Initialize a GRID2DEMAND object
    net = gd.GRID2DEMAND(node_file = path_node, poi_file = path_poi, use_zone_id=True)

    # load network: node and poi
    net.load_network()

    # Generate zone dictionary from node dictionary by specifying number of x blocks and y blocks
    net.net2zone(num_x_blocks=10, num_y_blocks=10)
    # net.net2zone(cell_width=10, cell_height=10, unit="km")

    # Calculate demand by running gravity model
    net.run_gravity_model(zone_prod_attr, zone_od_distance_matrix)

    # Save demand, zone, updated node, updated poi to csv
    net.save_results_to_csv(overwrite_file=True)
```

## Call for Contributions

The grid2demand project welcomes your expertise and enthusiasm!

Small improvements or fixes are always appreciated. If you are considering larger contributions to the source code, please contact us through email: [Xiangyong Luo](mailto:luoxiangyong01@gmail.com), [Dr. Xuesong Simon Zhou](mailto:xzhou74@asu.edu)

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


Xiangyong Luo, Dustin Carlino, and Xuesong Simon Zhou. (2023). [xyluo25/grid2demand](https://github.com/xyluo25/grid2demand/): Zenodo. https://doi.org/10.5281/zenodo.11212556
