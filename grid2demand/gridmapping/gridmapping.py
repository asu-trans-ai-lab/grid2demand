# -*- coding:utf-8 -*-
##############################################################
# Created Date: Friday, June 9th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import itertools
import pandas as pd
import shapely
import numpy as np
import copy


def calc_distance_on_unit_sphere(pt1, pt2, unit='km', precision=None):
    """
    Calculate distance between two points.

    :param pt1: one point
    :type pt1: shapely.geometry.Point | tuple | numpy.ndarray
    :param pt2: another point
    :type pt2: shapely.geometry.Point | tuple | numpy.ndarray
    :param unit: distance unit (for output), defaults to ``'miles'``;
        valid options include ``'mile'`` and ``'km'``
    :type unit: str
    :param precision: decimal places of the calculated result, defaults to ``None``
    :type precision: None | int
    :return: distance (in miles) between ``pt1`` and ``pt2`` (relative to the earth's radius)
    :rtype: float | None

    **Examples**::

        >>> from pyhelpers.geom import calc_distance_on_unit_sphere
        >>> from pyhelpers._cache import example_dataframe

        >>> example_df = example_dataframe()
        >>> example_df
                    Longitude   Latitude
        City
        London      -0.127647  51.507322
        Birmingham  -1.902691  52.479699
        Manchester  -2.245115  53.479489
        Leeds       -1.543794  53.797418

        >>> london, birmingham = example_df.loc[['London', 'Birmingham']].values
        >>> london
        array([-0.1276474, 51.5073219])
        >>> birmingham
        array([-1.9026911, 52.4796992])

        >>> arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham)
        >>> arc_len_in_miles  # in miles
        101.10431101941569

        >>> arc_len_in_miles = calc_distance_on_unit_sphere(london, birmingham, precision=4)
        >>> arc_len_in_miles
        101.1043

    .. note::

        This function is modified from the original code available at
        [`GEOM-CDOUS-1 <https://www.johndcook.com/blog/python_longitude_latitude/>`_].
        It assumes the earth is perfectly spherical and returns the distance based on each
        point's longitude and latitude.
    """

    earth_radius = 3960.0 if unit == "mile" else 6371.0

    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = np.pi / 180.0

    if not all(isinstance(x, shapely.geometry.Point) for x in (pt1, pt2)):
        try:
            pt1_, pt2_ = map(shapely.geometry.Point, (pt1, pt2))
        except Exception as e:
            print(e)
            return None
    else:
        pt1_, pt2_ = map(copy.copy, (pt1, pt2))

    # phi = 90 - latitude
    phi1 = (90.0 - pt1_.y) * degrees_to_radians
    phi2 = (90.0 - pt2_.y) * degrees_to_radians

    # theta = longitude
    theta1 = pt1_.x * degrees_to_radians
    theta2 = pt2_.x * degrees_to_radians

    # Compute spherical distance from spherical coordinates.
    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta', phi')
    # cosine( arc length ) = sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cosine = (np.sin(phi1) * np.sin(phi2) *
              np.cos(theta1 - theta2) + np.cos(phi1) * np.cos(phi2))
    arc_length = np.arccos(cosine) * earth_radius

    if precision:
        arc_length = np.round(arc_length, precision)

    # To multiply arc by the radius of the earth in a set of units to get length.
    return arc_length


def partition_grid(df_node: pd.DataFrame,
                   num_x_blocks: int = 0,
                   num_y_blocks: int = 0,
                   cell_width: float = 0,
                   cell_height: float = 0) -> pd.DataFrame:
    """Partition the study area into grid cells

    Parameters
        path_node: str, Path to the node.csv file, node.csv is GMNS format file
        num_x_blocks: int, Number of blocks in x direction, default 0
        num_y_blocks: int, Number of blocks in y direction, default 0
        cell_width: float, Width of each cell, unit in km, default 0
        cell_height: float, Height of each cell, unit in km, default 0

    Returns
        grid: pd.DataFrame, Grid cells with columns ['grid_id', 'geometry', 'centroid']

    """

    # get the boundary of the study area
    coord_x_min, coord_x_max = df_node['x_coord'].min() - 0.1, df_node['x_coord'].max() + 0.1
    coord_y_min, coord_y_max = df_node['y_coord'].min() - 0.1, df_node['y_coord'].max() + 0.1

    # Priority: num_x_blocks, number_y_blocks > cell_width, cell_height
    # if num_x_blocks and num_y_blocks are given, use them to partition the study area
    # else if cell_width and cell_height are given, use them to partition the study area
    # else raise error

    if num_x_blocks > 0 and num_y_blocks > 0:
        x_block_width = (coord_x_max - coord_x_min) / num_x_blocks
        y_block_height = (coord_y_max - coord_y_min) / num_y_blocks
    elif cell_width > 0 and cell_height > 0:
        x_dist_km = calc_distance_on_unit_sphere((coord_x_min, coord_y_min), (coord_x_max, coord_y_min), unit='km')
        y_dist_km = calc_distance_on_unit_sphere((coord_x_min, coord_y_min), (coord_x_min, coord_y_max), unit='km')

        num_x_blocks = int(np.ceil(x_dist_km / cell_width))
        num_y_blocks = int(np.ceil(y_dist_km / cell_height))

        x_block_width = (coord_x_max - coord_x_min) / num_x_blocks
        y_block_height = (coord_y_max - coord_y_min) / num_y_blocks
    else:
        raise ValueError('Please provide num_x_blocks and num_y_blocks or cell_width and cell_height')

    # partition the study area into grid cells
    x_block_min_lst = [coord_x_min + i * x_block_width for i in range(num_x_blocks)]
    y_block_min_lst = [coord_y_min + i * y_block_height for i in range(num_y_blocks)]

    x_block_minmax_list = list(zip(x_block_min_lst[:-1], x_block_min_lst[1:])) + [(x_block_min_lst[-1], coord_x_max)]
    y_block_minmax_list = list(zip(y_block_min_lst[:-1], y_block_min_lst[1:])) + [(y_block_min_lst[-1], coord_y_max)]

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

    grid_lst = []
    ceil_id = 0
    for x_minmax in x_block_minmax_list:
        for y_minmax in y_block_minmax_list:
            cell_polygon = generate_polygon(x_minmax[0], x_minmax[1], y_minmax[0], y_minmax[1])
            grid_lst.append([ceil_id,
                             cell_polygon,
                             cell_polygon.centroid]
                            )
            ceil_id += 1

    return pd.DataFrame(grid_lst, columns=['grid_id', 'geometry', 'centroid'])


def node_mapping_grid(df_node, df_grid) -> pd.DataFrame:
    """Map nodes to grid cells

    Parameters
        df_node: pd.DataFrame, Nodes
        df_grid: pd.DataFrame, Grid cells

    Returns
        df_node_grid: pd.DataFrame, Nodes with grid id

    """

    df_node['grid_id'] = None

    if isinstance(df_node.loc[0, 'geometry'], str):
        df_node['geometry'] = df_node["geometry"].apply(shapely.from_wkt)

    if isinstance(df_grid.loc[0, 'geometry'], str):
        df_grid['geometry'] = df_grid["geometry"].apply(shapely.from_wkt)

    for i in range(len(df_node)):
        for j in range(len(df_grid)):
            if shapely.within(df_node.loc[i, "geometry"], df_grid.loc[j, "geometry"]):
                df_node.loc[i, 'grid_id'] = df_grid.loc[j, 'grid_id']
                break

    return df_node


def grid_OD_distance(df_grid, isDataFrame: bool = True) -> dict | pd.DataFrame:

    if isinstance(df_grid.loc[0, 'centroid'], str):
        df_grid['centroid'] = df_grid["centroid"].apply(shapely.from_wkt)

    len_df_grid = len(df_grid)
    grid_id_lst = df_grid['grid_id'].tolist()

    dist_dict = {
        (grid_id_lst[i], grid_id_lst[j]): calc_distance_on_unit_sphere(
            df_grid.loc[i, "centroid"], df_grid.loc[j, "centroid"], unit='km'
        )
        for i, j in itertools.product(range(len_df_grid), range(len_df_grid))
    }

    if isDataFrame:
        # create empty od matrix
        od_matrix = [["" for _ in range(len_df_grid)] for _ in range(len_df_grid)]

        for key in dist_dict:
            od_matrix[key[0]][key[1]] = dist_dict[key]

        df_od_matrix = pd.DataFrame(od_matrix, columns=grid_id_lst, index=grid_id_lst)
        return df_od_matrix

    return dist_dict


def path_to_grid(df_node_grid, df_path_assignment) -> pd. DataFrame:
    node2grid_dict = dict(zip(df_node_grid['node_id'], df_node_grid['grid_id']))

    df_path_assignment['grid_sequence'] = None

    for i in range(len(df_path_assignment)):
        node_sequence = df_path_assignment.loc[i, 'node_sequence'].split(';')
        grid_sequence = list(
            {node2grid_dict[int(node)] for node in node_sequence if node != ''}
        )
        df_path_assignment.loc[i, 'grid_sequence'] = str(grid_sequence)
    return df_path_assignment

if __name__ == "__main__":

    # initialize the overall processing steps

    # 1. Generate grid cells using node.csv file, the result is grid.csv
    path_node = "./node.csv"
    df_node = pd.read_csv(path_node)
    df_grid = partition_grid(df_node, num_x_blocks=10, num_y_blocks=10)
    df_grid.to_csv("step1_grid.csv", index=False)

    # 2. Generate OD matrix using grid.csv file, the result is grid_od.csv
    path_grid = "step1_grid.csv"
    df_grid = pd.read_csv(path_grid)
    df_grid_od = grid_OD_distance(df_grid)
    df_grid_od.to_csv("step2_grid_od.csv", index=False)

    # 3. Map nodes to grid cells using node.csv and grid.csv, the result is node_grid.csv
    path_node = "./node.csv"
    path_grid = "step1_grid.csv"

    df_node = pd.read_csv(path_node)
    df_grid = pd.read_csv(path_grid)

    df_node_grid = node_mapping_grid(df_node, df_grid)
    df_node_grid.to_csv("step3_node_grid.csv", index=False)

    # 4. Map paths to grid cells using node_grid.csv and path_assignment.csv, the result is path_assignment_grid.csv
    path_assignment = "./path_assignment.csv"
    path_node_grid = "./step3_node_grid.csv"

    df_path_assignment = pd.read_csv(path_assignment)
    df_node_grid = pd.read_csv(path_node_grid)

    df_assignment_grid = path_to_grid(df_node_grid, df_path_assignment)
    df_assignment_grid.to_csv("step4_path_assignment_grid.csv", index=False)
