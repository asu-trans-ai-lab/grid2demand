# -*- coding:utf-8 -*-
##############################################################
# Created Date: Tuesday, September 5th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

from __future__ import absolute_import
import pandas as pd
import shapely
import numpy as np


def set_system_path() -> None:
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).parent.parent))

set_system_path()
from utils_lib.net_utils import Zone
from utils_lib.utils import calc_distance_on_unit_sphere, int2alpha


def net2zone(df_node: pd.DataFrame,
             num_x_blocks: int = 0,
             num_y_blocks: int = 0,
             cell_width: float = 0,
             cell_height: float = 0) -> dict:
    """Partition the study area into zone cells

    Parameters
        path_node: str, Path to the node.csv file, node.csv is GMNS format file
        num_x_blocks: int, Number of blocks in x direction, default 0
        num_y_blocks: int, Number of blocks in y direction, default 0
        cell_width: float, Width of each cell, unit in km, default 0
        cell_height: float, Height of each cell, unit in km, default 0

    Returns
        Zone: dictionary, Zone cells with keys are zone names, values are Zone

    """

    # get the boundary of the study area
    coord_x_min, coord_x_max = df_node['x_coord'].min(
    ) - 0.1, df_node['x_coord'].max() + 0.1
    coord_y_min, coord_y_max = df_node['y_coord'].min(
    ) - 0.1, df_node['y_coord'].max() + 0.1

    # Priority: num_x_blocks, number_y_blocks > cell_width, cell_height
    # if num_x_blocks and num_y_blocks are given, use them to partition the study area
    # else if cell_width and cell_height are given, use them to partition the study area
    # else raise error

    if num_x_blocks > 0 and num_y_blocks > 0:
        x_block_width = (coord_x_max - coord_x_min) / num_x_blocks
        y_block_height = (coord_y_max - coord_y_min) / num_y_blocks
    elif cell_width > 0 and cell_height > 0:
        x_dist_km = calc_distance_on_unit_sphere(
            (coord_x_min, coord_y_min), (coord_x_max, coord_y_min), unit='km')
        y_dist_km = calc_distance_on_unit_sphere(
            (coord_x_min, coord_y_min), (coord_x_min, coord_y_max), unit='km')

        num_x_blocks = int(np.ceil(x_dist_km / cell_width))
        num_y_blocks = int(np.ceil(y_dist_km / cell_height))

        x_block_width = (coord_x_max - coord_x_min) / num_x_blocks
        y_block_height = (coord_y_max - coord_y_min) / num_y_blocks
    else:
        raise ValueError(
            'Please provide num_x_blocks and num_y_blocks or cell_width and cell_height')

    # partition the study area into zone cells
    x_block_min_lst = [coord_x_min + i *
                       x_block_width for i in range(num_x_blocks)]
    y_block_min_lst = [coord_y_min + i *
                       y_block_height for i in range(num_y_blocks)]

    x_block_minmax_list = list(zip(
        x_block_min_lst[:-1], x_block_min_lst[1:])) + [(x_block_min_lst[-1], coord_x_max)]
    y_block_minmax_list = list(zip(
        y_block_min_lst[:-1], y_block_min_lst[1:])) + [(y_block_min_lst[-1], coord_y_max)]

    def generate_polygon(x_min, x_max, y_min, y_max) -> shapely.geometry.Polygon:
        """Generate polygon from min and max coordinates

        Parameters
            x_min: float, Min x coordinate
            x_max: float, Max x coordinate
            y_min: float, Min y coordinate
            y_max: float, Max y coordinate

        Returns
            polygon: sg.Polygon, Polygon

        """
        return shapely.geometry.Polygon([(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max), (x_min, y_min)])

    zone_dict = {}
    zone_upper_row = []
    zone_lower_row = []
    zone_left_col = []
    zone_right_col = []
    zone_id_flag = 0

    # convert y from min-max to max-min
    y_block_maxmin_list = y_block_minmax_list[::-1]

    # generate zone cells with id and labels
    # id: A1, A2, A3, ...,
    #     B1, B2, B3, ...,
    #     C1, C2, C3, ...
    for j in range(len(y_block_maxmin_list)):
        for i in range(len(x_block_minmax_list)):
            x_min = x_block_minmax_list[i][0]
            x_max = x_block_minmax_list[i][1]
            y_min = y_block_maxmin_list[j][0]
            y_max = y_block_maxmin_list[j][1]

            cell_polygon = generate_polygon(x_min, x_max, y_min, y_max)
            row_alpha = int2alpha(j)
            zone_dict[f"{row_alpha}{i}"] = Zone(
                id=zone_id_flag,
                name=f"{row_alpha}{i}",
                centroid_x=cell_polygon.centroid.x,
                centroid_y=cell_polygon.centroid.y,
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
                geometry=cell_polygon
            )

            # add boundary zone names to list
            if j == 0:
                zone_upper_row.append(f"{row_alpha}{i}")
            if j == len(y_block_maxmin_list) - 1:
                zone_lower_row.append(f"{row_alpha}{i}")

            if i == 0:
                zone_left_col.append(f"{row_alpha}{i}")
            if i == len(x_block_minmax_list) - 1:
                zone_right_col.append(f"{row_alpha}{i}")

            # update zone id
            zone_id_flag += 1

    # generate outside boundary centroids
    upper_points = [shapely.geometry.Point(zone_dict[zone_name].centroid_x,
                                           zone_dict[zone_name].centroid_y + y_block_height
                                           ) for zone_name in zone_upper_row]
    lower_points = [shapely.geometry.Point(zone_dict[zone_name].centroid_x,
                                           zone_dict[zone_name].centroid_y - y_block_height
                                           ) for zone_name in zone_lower_row]
    left_points = [shapely.geometry.Point(zone_dict[zone_name].centroid_x - x_block_width,
                                          zone_dict[zone_name].centroid_y
                                          ) for zone_name in zone_left_col]
    right_points = [shapely.geometry.Point(zone_dict[zone_name].centroid_x + x_block_width,
                                           zone_dict[zone_name].centroid_y
                                           ) for zone_name in zone_right_col]
    points_lst = upper_points + lower_points + left_points + right_points
    for i in range(len(points_lst)):
        zone_dict[f"gate{i}"] = Zone(
            id=zone_id_flag,
            name=f"gate{i}",
            centroid_x=points_lst[i].x,
            centroid_y=points_lst[i].y,
            centroid=points_lst[i],
            geometry=points_lst[i]
        )
        zone_id_flag += 1
    return zone_dict


def node_mapping_zone(node_dict: dict, zone_dict: dict) -> dict:
    """Map nodes to zone cells

    Parameters
        node_dict: dict, Nodes
        zone_dict: dict, zone cells

    Returns
        node_dict: dict, Update Nodes with zone id

    """
    for node in node_dict:
        for zone in zone_dict:
            if isinstance(node_dict[node].geometry, str):
                node_dict[node].geometry = shapely.from_wkt(node_dict[node].geometry)
            if isinstance(zone_dict[zone].polygon, str):
                zone_dict[zone].geometry = shapely.from_wkt(zone_dict[zone].geometry)

            if shapely.within(node_dict[node].geometry, zone_dict[zone].geometry):
                node_dict[node].zone_id = zone_dict[zone].id
                break

    return node_dict


if __name__ == "__main__":
    path_node = r"C:\Users\roche\Anaconda_workspace\001_Github\zone2demand\dataset\ASU\node.csv"
    df_node = pd.read_csv(path_node)

    zone_dict = net2zone(df_node, num_x_blocks=10, num_y_blocks=10)
    df_zone = pd.DataFrame.from_dict(zone_dict, orient='index')