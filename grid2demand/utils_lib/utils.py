# -*- coding:utf-8 -*-
##############################################################
# Created Date: Wednesday, September 6th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import shapely
import copy
import numpy as np
import os
import datetime


def calc_distance_on_unit_sphere(pt1: shapely.Point, pt2: shapely.Point, unit='km', precision=None):
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


def int2alpha(num: int) -> str:
    """Convert integer to alphabet, e.g., 0 -> A, 1 -> B, 26 -> AA, 27 -> AB

    Parameters
        num: int, Integer

    Returns
        alpha: str, Alphabet

    """

    if num < 26:
        return chr(num + 65)
    else:
        return int2alpha(num // 26 - 1) + int2alpha(num % 26)


def set_system_path() -> None:
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).parent.parent))


def func_running_time(func):
    """A decorator to measure the time of a function"""

    def inner(*args, **kwargs):
        print(f'INFO Begin to run function: {func.__name__} …')
        time_start = datetime.datetime.now()
        res = func(*args, **kwargs)
        time_diff = datetime.datetime.now() - time_start
        print(
            f'INFO Finished running function: {func.__name__}, total: {time_diff.seconds}s')
        print()
        return res
    return inner


def path2linux(path: str) -> str:
    """Convert OS path to standard linux path

    Parameters
    ----------
    path : str
        the path to be converted

    Returns
    -------
    str
        the converted path
    """

    try:
        return path.replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def get_filenames_from_folder_by_type(dir_name: str, file_type: str = "txt", isTraverseSubdirectory: bool = False) -> list:
    """Get all files in the folder with the specified file type

    Args:
        dir_name (str): the folder path
        file_type (str, optional): the exact file type to specify, if file_type is "*" or "all", return all files in the folder. Defaults to "txt".
        isTraverseSubdirectory (bool, optional): get files inside the subfolder or not, if True, will traverse all subfolders. Defaults to False.

    Returns:
        list: a list of file paths

    Examples:
        # get all files in the folder without traversing subfolder
        >>> from pyhelpers.dirs import get_filenames_from_folder_by_type
        >>> get_filenames_from_folder_by_type("C:/Users/user/Desktop", "txt")
        ['C:/Users/user/Desktop/test.txt']

        # get all files in the folder with traversing subfolder
        >>> from pyhelpers.dirs import get_filenames_from_folder_by_type
        >>> get_filenames_from_folder_by_type("C:/Users/user/Desktop", "txt", isTraverseSubdirectory=True)
        ['C:/Users/user/Desktop/test.txt', 'C:/Users/user/Desktop/sub_folder/test2.txt']
    """

    if isTraverseSubdirectory:
        files_list = []
        for root, dirs, files in os.walk(dir_name):
            files_list.extend([os.path.join(root, file) for file in files])
        if file_type in {"*", "all"}:
            return [path2linux(file) for file in files_list]
        return [path2linux(file) for file in files_list if file.split(".")[-1] == file_type]
    print("input dir:", dir_name, "input file type", file_type)
    # files in the first layer of the folder
    if file_type in {"*", "all"}:
        return [path2linux(os.path.join(dir_name, file)) for file in os.listdir(dir_name)]
    return [path2linux(os.path.join(dir_name, file)) for file in os.listdir(dir_name) if file.split(".")[-1] == file_type]


def check_required_files_exist(required_files: list, dir_files: list) -> bool:
    # format the required file name to standard linux path
    required_files = [path2linux(os.path.abspath(filename))
                      for filename in required_files]

    required_files_short = [filename.split(
        "/")[-1] for filename in required_files]
    dir_files_short = [filename.split("/")[-1] for filename in dir_files]

    # mask have the same length as required_files
    mask = [file in dir_files_short for file in required_files_short]
    if all(mask):
        return True

    print(f"Error: Required files are not satisfied, \
          missing files are: {[required_files_short[i] for i in range(len(required_files_short)) if not mask[i]]}")

    return False


def gen_unique_filename(path_filename: str, ) -> str:
    """if the file name exist in path,then create new file name with _1, _1_1, ..."""
    filename_abspath = path2linux(os.path.abspath(path_filename))

    file_suffix = filename_abspath.split(".")[-1]
    file_without_suffix = filename_abspath[:-len(file_suffix) - 1]

    if os.path.exists(filename_abspath):
        filename_update = f"{file_without_suffix}_1.{file_suffix}"
        return gen_unique_filename(filename_update)
    return filename_abspath
