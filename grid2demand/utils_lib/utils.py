# -*- coding:utf-8 -*-
##############################################################
# Created Date: Wednesday, September 6th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import copy
import os
import datetime
import itertools
from dataclasses import dataclass, field, fields, make_dataclass, MISSING, is_dataclass, asdict
from typing import Any, List, Tuple, Type, Dict
import shapely
import numpy as np


def create_dataclass_from_dict(name: str, data: Dict[str, Any]) -> Type:
    """
    Creates a dataclass with attributes and values based on the given dictionary.
    The dataclass will also support dictionary-like access via __getitem__ and __setitem__.

    Args:
        name (str): The name of the dataclass to create.
        data (Dict[str, Any]): A dictionary where keys are attribute names and values are attribute values.

    Returns:
        Type: A dataclass with fields and values corresponding to the dictionary.
    """
    # Define a method for __getitem__ for dictionary-like access

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            raise KeyError(f"Key {key} not found in {self.__class__.__name__}")

    # Define a method for __setitem__ for dictionary-like assignment
    def __setitem__(self, key, value):
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Key {key} not found in {self.__class__.__name__}")

    # Define a method to convert the dataclass to a dictionary
    def as_dict(self):
        return asdict(self)

    # Extract fields and their types from the dictionary
    dataclass_fields = []
    for key, value in data.items():
        if isinstance(value, (list, dict, set)):  # For mutable types
            dataclass_fields.append(
                (key, type(value), field(default_factory=lambda v=value: v)))
        else:  # For immutable types
            dataclass_fields.append((key, type(value), field(default=value)))

    # Create the dataclass dynamically
    DataClass = make_dataclass(
        cls_name=name,
        fields=dataclass_fields,
        bases=(),
        namespace={'__getitem__': __getitem__,
                   '__setitem__': __setitem__,
                   'as_dict': as_dict}
    )

    # Instantiate the dataclass with the values from the dictionary
    return DataClass(**data)


def extend_dataclass(
    base_dataclass: Type[Any],
    additional_attributes: List[Tuple[str, Type[Any], Any]]
) -> Type[Any]:
    """Creates a new dataclass by extending the base_dataclass with additional_attributes.

    Args:
        base_dataclass (dataclass): The base dataclass to extend.
        additional_attributes (list): A list of tuples in the form (name, type, default_value).
            or (name, default_value) to add to the base dataclass.

    Example:
        >>> from dataclasses import dataclass
        >>> from typing import List
        >>> from pyufunc import extend_dataclass
        >>> @dataclass
        ... class BaseDataclass:
        ...     name: str = 'base'

        >>> ExtendedDataclass = extend_dataclass(
        ...     base_dataclass=BaseDataclass,
        ...     additional_attributes=[('new_attr', List[int], [1, 2, 3])])
        >>> ExtendedDataclass



    Returns:
        dataclass: A new dataclass that includes fields from base_dataclass and additional_attributes.
    """

    # check inputs
    if not is_dataclass(base_dataclass):
        raise ValueError('base_dataclass must be a dataclass')

    for attr in additional_attributes:
        if len(attr) not in {2, 3}:
            raise ValueError('additional_attributes must be a list of tuples'
                             ' in the form (name, default_value) or (name, type, default_value)')

    # deepcopy the base dataclass
    base_dataclass_ = copy.deepcopy(base_dataclass)
    # base_dataclass_ = base_dataclass

    # Extract existing fields from the base dataclass
    base_fields = []
    for f in fields(base_dataclass_):
        if f.default is not MISSING:
            base_fields.append((f.name, f.type, f.default))
        elif f.default_factory is not MISSING:
            base_fields.append((f.name, f.type, field(
                default_factory=f.default_factory)))
        else:
            base_fields.append((f.name, f.type))

    # check if additional attributes:
    # if len == 2, adding Any as data type in the middle if the tuple
    # if len == 3, keep the original tuple
    additional_attributes = [
        val if len(val) == 3 else (val[0], Any, val[1])
        for val in additional_attributes
    ]

    # Combine base fields with additional attributes
    all_fields = base_fields + additional_attributes

    new_dataclass = make_dataclass(
        cls_name=f'{base_dataclass_.__name__}',
        fields=all_fields,
        bases=(base_dataclass,),
    )

    # Register the new dataclass in the global scope to allow pickling
    globals()[new_dataclass.__name__] = new_dataclass

    # new_dataclass.__module__ = base_dataclass_.__module__
    return new_dataclass


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


def get_filenames_from_folder_by_type(dir_name: str,
                                      file_type: str = "txt",
                                      isTraverseSubdirectory: bool = False) -> list:
    """Get all files in the folder with the specified file type

    Args:
        dir_name (str): the folder path
        file_type (str, optional): file type to specify, if "*" or "all", return all files in folder. Defaults to "txt".
        isTraverseSubdirectory (bool, optional): traverse all sub-folders or not. Defaults to False.

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
    print(f"  : input dir {dir_name}, traverse files by type: {file_type}")
    # files in the first layer of the folder
    if file_type in {"*", "all"}:
        return [path2linux(os.path.join(dir_name, file)) for file in os.listdir(dir_name)]
    return [path2linux(
        os.path.join(dir_name, file)) for file in os.listdir(dir_name) if file.split(".")[-1] == file_type]


def check_required_files_exist(required_files: list, dir_files: list, verbose: bool = True) -> bool:
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

    if verbose:
        print(f"  : Error: Required files are not satisfied, \
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


def split_dict_by_chunk(dictionary: dict, chunk_size: int, pair_val: list = []) -> list:
    """Split dictionary into chunks

    Args:
        dictionary (dict): the input dictionary with key-value pairs
        chunk_size (int): the size of each chunk
        pair_val (list, optional): the return value associate with each chunk dictionary. Defaults to [].

    Returns:
        list: a list including a chunk value and the pair value: [chunk_dict, pair_val]

    Yields:
        Iterator[list]: a generator of the list including a chunk value and the pair value: [chunk_dict, pair_val]
    """
    iterator = iter(dictionary.items())
    for _ in range(0, len(dictionary), chunk_size):
        chunk = dict(itertools.islice(iterator, chunk_size))
        if chunk:  # check if chunk is not empty
            yield [chunk] + pair_val
