# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 4th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


from dataclasses import dataclass, asdict, field


@dataclass
class Node:
    """A node in the network.

    Attributes:
        id: The node ID.
        zone_id: The zone ID. default is 0, only three conditions to become an activity node
                1) POI node, 2) is_boundary node(freeway),  3) residential in activity_type
        x_coord: The x coordinate of the node.
        y_coord: The y coordinate of the node.
        production: The production of the node.
        attraction: The attraction of the node.
        boundary_flag: The boundary flag of the node. = 1 (current node is boundary node)
        poi_id: The POI ID of the node. default = -1; to be assigned to a POI ID after reading poi.csv
        activity_type: The activity type of the node. provided from osm2gmns such as motoway, residential, ...
        activity_location_tab: The activity location tab of the node.
    """
    id: int = 0
    zone_id: int = 0
    x_coord: float = 0
    y_coord: float = 0
    production: float = 0
    attraction: float = 0
    boundary_flag: int = 0
    poi_id: int = -1
    activity_type: str = ''
    activity_location_tab: str = ''


@dataclass
class POI:
    """A POI in the network.

    Attributes:
        id: The POI ID.
        zone_id: The zone ID. mapping from zone
        x_coord: The x coordinate of the POI.
        y_coord: The y coordinate of the POI.
        count: The count of the POI. Total POI values for this POI node or POI zone
        area: The area of the POI. Total area of polygon for this POI zone. unit is square meter
        type: The type of the POI. Default is empty string
        geometry: The polygon of the POI. based on wkt format. Default is empty string
    """

    id: int = 0
    zone_id: int = 0
    x_coord: float = 0
    y_coord: float = 0
    count: int = 1
    area: float = 0
    type: str = ''
    geometry: str = ''


@dataclass
class Zone:
    """A zone in the network.

    Attributes:
        id: The zone ID.
        name: The name of the zone.
        centroid_x: The centroid x coordinate of the zone.
        centroid_y: The centroid y coordinate of the zone.
        centroid: The centroid of the zone. (x, y) based on wkt format
        x_max: The max x coordinate of the zone.
        x_min: The min x coordinate of the zone.
        y_max: The max y coordinate of the zone.
        y_min: The min y coordinate of the zone.
        poi_count: The POI count of the zone. Total POIs in this zone
        node_id_list: Node IDs which belong to this zone.
        poi_id_list: The POIs which belong to this zone.
        polygon: The polygon of the zone. based on wkt format
    """

    id: int = 0
    name: str = ''
    centroid_x: float = 0
    centroid_y: float = 0
    centroid: tuple = field(default_factory=tuple)
    x_max: float = 0
    x_min: float = 0
    y_max: float = 0
    y_min: float = 0
    poi_count: int = 0
    node_id_list: list = field(default_factory=list)
    poi_id_list: list = field(default_factory=list)
    polygon: str = ''


class Agent:
    """An agent in the network.

    Attributes:
        agent_id: The agent ID.
        agent_type: The agent type.
        o_zone_id: The origin zone ID.
        d_zone_id: The destination zone ID.
        o_node_id: The origin node ID. default = 0
        d_node_id: The destination node ID. default = 0
        path_node_seq_no_list: The path node sequence number list. default = []
        path_link_seq_no_list: The path link sequence number list. default = []
        current_link_se_no_in_path: The current link sequence number in path. default = 0
        path_cost: The path cost. default = 0
        b_generated: The flag of whether the agent is generated. default = False
        b_complete_trip: The flag of whether the agent completes the trip. default = False
    """

    def __init__(self, agent_id: int, agent_type: str, o_zone_id: int, d_zone_id: int) -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.o_zone_id = o_zone_id
        self.d_zone_id = d_zone_id

        # some attributes to be assigned later
        self.o_node_id = 0
        self.d_node_id = 0
        self.path_node_seq_no_list = field(default_factory=list)
        self.path_link_seq_no_list = field(default_factory=list)
        self.current_link_se_no_in_path = 0
        self.path_cost = 0
        self.b_generated = False
        self.b_complete_trip = False

