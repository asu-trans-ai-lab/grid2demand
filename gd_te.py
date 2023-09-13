# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 11th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import grid2demand as gd
from dataclasses import asdict
import pandas as pd


node_dict = gd.read_node("./dataset/ASU/node.csv")
poi_dict = gd.read_poi("./dataset/ASU/poi.csv")

zone_dict = gd.net2zone(node_dict, num_x_blocks=10, num_y_blocks=10)


zone_node_dict = gd.sync_zone_and_node_geometry(zone_dict, node_dict)
zone_dict_update = zone_node_dict.get('zone_dict')
node_dict_update = zone_node_dict.get('node_dict')

zone_poi_dict = gd.sync_zone_and_poi_geometry(zone_dict_update, poi_dict)
zone_dict_update = zone_poi_dict.get('zone_dict')
poi_dict_update = zone_poi_dict.get('poi_dict')

zone_od_matrix = gd.calc_zone_od_matrix(zone_dict_update)

poi_trip_rate = gd.gen_poi_trip_rate(poi_dict_update)

node_prod_attr = gd.gen_node_prod_attr(node_dict_update, poi_trip_rate)