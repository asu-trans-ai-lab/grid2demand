# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 4th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


from dataclasses import dataclass, field, asdict


@dataclass
class Node:
    """A node in the network.

    Attributes:
        id: The node ID.
        x_coord: The x coordinate of the node.
        y_coord: The y coordinate of the node.
        production: The production of the node.
        attraction: The attraction of the node.
        is_boundary: The boundary flag of the node. = 1 (current node is boundary node)
        zone_id: The zone ID. default == -1, only three conditions to become an activity node
                1) POI node, 2) is_boundary node(freeway),  3) residential in activity_type
        poi_id: The POI ID of the node. default = -1; to be assigned to a POI ID after reading poi.csv
        activity_type: The activity type of the node. provided from osm2gmns such as motoway, residential, ...
        activity_location_tab: The activity location tab of the node.
        geometry: The geometry of the node. based on wkt format.
        _zone_id: The zone ID. default == -1,
                this will be assigned if field zone_id exists in the node.csv and is not empty
    """
    id: int = 0
    x_coord: float = -1
    y_coord: float = -1
    production: float = 0
    attraction: float = 0
    is_boundary: int = 0
    ctrl_type: int = -1
    zone_id: int = -1
    poi_id: int = -1
    activity_type: str = ''
    activity_location_tab: str = ''
    geometry: str = ''
    _zone_id: int = -1

    @property
    def as_dict(self):
        return asdict(self)


@dataclass
class POI:
    """A POI in the network.

    Attributes:
        id      : The POI ID.
        x_coord : The x coordinate of the POI.
        y_coord : The y coordinate of the POI.
        count   : The count of the POI. Total POI values for this POI node or POI zone
        area    : The area of the POI. Total area of polygon for this POI zone. unit is square meter
        poi_type: The type of the POI. Default is empty string
        geometry: The polygon of the POI. based on wkt format. Default is empty string
        zone_id : The zone ID. mapping from zone
    """

    id: int = 0
    x_coord: float = 0
    y_coord: float = 0
    count: int = 1
    area: list = field(default_factory=list)
    poi_type: str = ''
    trip_rate: dict = field(default_factory=dict)
    geometry: str = ''
    zone_id: int = -1

    @property
    def as_dict(self):
        return asdict(self)


@dataclass
class Zone:
    """A zone in the network.

    Attributes:
        id              : The zone ID.
        name            : The name of the zone.
        centroid_x      : The centroid x coordinate of the zone.
        centroid_y      : The centroid y coordinate of the zone.
        centroid        : The centroid of the zone. (x, y) based on wkt format
        x_max           : The max x coordinate of the zone.
        x_min           : The min x coordinate of the zone.
        y_max           : The max y coordinate of the zone.
        y_min           : The min y coordinate of the zone.
        node_id_list    : Node IDs which belong to this zone.
        poi_id_list     : The POIs which belong to this zone.
        production      : The production of the zone.
        attraction      : The attraction of the zone.
        production_fixed: The fixed production of the zone (implement different models).
        attraction_fixed: The fixed attraction of the zone (implement different models).
        geometry        : The geometry of the zone. based on wkt format
    """

    id: int = 0
    name: str = ''
    centroid_x: float = 0
    centroid_y: float = 0
    centroid: str = ""
    x_max: float = 0
    x_min: float = 0
    y_max: float = 0
    y_min: float = 0
    node_id_list: list = field(default_factory=list)
    poi_id_list: list = field(default_factory=list)
    production: float = 0
    attraction: float = 0
    production_fixed: float = 0
    attraction_fixed: float = 0
    geometry: str = ''

    @property
    def as_dict(self):
        return asdict(self)


@dataclass
class Agent:
    """An agent in the network.

    Attributes:
        id: The agent ID. default = 0
        agent_type: The agent type. default = ''
        o_zone_id: The origin zone ID. default = 0
        d_zone_id: The destination zone ID. default = 0
        o_zone_name: The origin zone name. default = ''
        d_zone_name: The destination zone name. default = ''

        o_node_id: The origin node ID. default = 0
        d_node_id: The destination node ID. default = 0

        path_node_seq_no_list: The path node sequence number list. default = []
        path_link_seq_no_list: The path link sequence number list. default = []
        path_cost: The path cost. default = 0

        b_generated: The flag of whether the agent is generated. default = False
        b_complete_trip: The flag of whether the agent completes the trip. default = False

        geometry: The geometry of the agent. based on wkt format. default = ''
        departure_time: The departure time of the agent. unit is second. default = 0
    """

    id: int = 0
    agent_type: str = ''
    o_zone_id: int = 0
    d_zone_id: int = 0
    o_zone_name: str = ''
    d_zone_name: str = ''

    # some attributes to be assigned later
    o_node_id: int = 0
    d_node_id: int = 0
    path_node_seq: list = field(default_factory=list)
    path_link_seq: list = field(default_factory=list)
    path_cost = 0
    b_generated: bool = False
    b_complete_trip: bool = False
    geometry: str = ''
    departure_time: int = 0  # unit is second

    @property
    def as_dict(self):
        return asdict(self)
