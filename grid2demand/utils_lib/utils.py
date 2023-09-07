# -*- coding:utf-8 -*-
##############################################################
# Created Date: Wednesday, September 6th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import shapely
import copy
import numpy as np

# the initial value for trip purpose, usr can add more trip purposes
trip_purpose_dict = {0: 'home-based-work', 1: 'home-based-other', 2: 'non-home-based'}


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
