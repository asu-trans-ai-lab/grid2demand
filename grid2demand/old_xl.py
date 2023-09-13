# -*- coding:utf-8 -*-
##############################################################
# Created Date: Monday, September 4th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import os
import pandas as pd
import numpy as np
import math
import csv
import re
import locale
import sys
from pprint import pprint
from collections import defaultdict
import logging
import random
from random import choice

"""PART 5  TRIP DISTRIBUTION"""
g_node_id_list = []
g_node_zone_id_list = []
g_node_production_dict = {}
g_node_attraction_dict = {}
g_trip_matrix = []
g_total_production_list = []
g_total_attraction_list = []
g_zone_to_nodes_dict = {}


def RunGravityModel(trip_purpose=None, a=None, b=None, c=None):
    logger.debug("Starting RunGravityModel")
    global g_node_id_list
    global g_node_production_dict
    global g_node_attraction_dict
    global g_trip_matrix
    global g_output_folder

    g_number_of_nodes = len(g_node_list)

    "deal with multiple nodes within one zone"
    g_zone_production = np.zeros(g_number_of_zones)
    g_zone_attraction = np.zeros(g_number_of_zones)
    error_flag = 0
    for i in range(g_number_of_nodes):
        if g_node_list[i].activity_location_tab == 'poi' or g_node_list[i].activity_location_tab == 'boundary' or \
                g_node_list[i].activity_location_tab == 'residential':
            node_id = g_node_id_list[i]
            if g_node_zone_dict.get(node_id) is not None:
                zone_id = g_node_zone_dict[node_id]
                zone_index = g_zone_index_dict[zone_id]
                node_prod = g_node_production_dict[node_id]
                node_attr = g_node_attraction_dict[node_id]
                g_zone_production[zone_index] = g_zone_production[zone_index] + node_prod
                g_zone_attraction[zone_index] = g_zone_attraction[zone_index] + node_attr
                error_flag += 1
    if error_flag == 0:
        # print("There is no node with activity_type = 'poi/residential' or is_boundary = '1'. Please check
        # node.csv!")
        logger.error("There is no node with activity_type = 'poi/residential' or is_boundary = '1'. Please check "
                     "node.csv!")
        sys.exit(0)

    for zone in g_zone_list:
        zone_index = g_zone_index_dict[zone.id]
        g_total_production_list.append(g_zone_production[zone_index])
        g_total_attraction_list.append(g_zone_attraction[zone_index])

    "perform the distribution with friction matrix"
    g_friction_matrix = np.ones((g_number_of_zones, g_number_of_zones)) * 9999  # initialize friction matrix
    for o_zone in g_zone_list:
        for d_zone in g_zone_list:
            o_zone_index = g_zone_index_dict[o_zone.id]
            d_zone_index = g_zone_index_dict[d_zone.id]
            od_distance = g_distance_matrix[o_zone_index][d_zone_index]
            if od_distance != 0:
                g_friction_matrix[o_zone_index][d_zone_index] = a * (od_distance ** b) * (np.exp(c * od_distance))
            else:
                g_friction_matrix[o_zone_index][d_zone_index] = 0

    "step 1: calculate total attraction for each zone"
    g_trip_matrix = np.zeros((g_number_of_zones, g_number_of_zones))
    total_attraction_friction = np.zeros(g_number_of_zones)
    for i in g_zone_id_list:
        prod_zone_index = g_zone_index_dict[i]
        for j in g_zone_id_list:
            attr_zone_index = g_zone_index_dict[j]
            total_attraction_friction[prod_zone_index] += g_zone_attraction[attr_zone_index] * \
                                                          g_friction_matrix[prod_zone_index][attr_zone_index]

    "step 2: update OD matrix"
    for i in g_zone_id_list:
        prod_zone_index = g_zone_index_dict[i]
        for j in g_zone_id_list:
            attr_zone_index = g_zone_index_dict[j]
            g_trip_matrix[prod_zone_index][attr_zone_index] = float(
                g_zone_production[prod_zone_index] * g_zone_attraction[attr_zone_index] *
                g_friction_matrix[prod_zone_index][attr_zone_index] / max(0.000001,
                                                                          total_attraction_friction[prod_zone_index]))


    # create demand.csv
    volume_list = []
    for i in range(len(o_zone_id_list)):
        od_volume = g_trip_matrix[g_zone_index_dict[o_zone_id_list[i]]][g_zone_index_dict[d_zone_id_list[i]]]
        volume_list.append(od_volume)

    data = pd.DataFrame(o_zone_id_list)
    data.columns = ["o_zone_id"]
    data["o_zone_name"] = pd.DataFrame(o_zone_name_list)
    data["d_zone_id"] = pd.DataFrame(d_zone_id_list)
    data["d_zone_name"] = pd.DataFrame(d_zone_name_list)
    data["accessibility"] = pd.DataFrame(od_distance_list)
    data["volume"] = pd.DataFrame(volume_list)
    data["geometry"] = pd.DataFrame(od_geometry_list)

    max_OD_index = volume_list.index(max(volume_list))
    print('\nZone-to-zone OD pair with largest volume is from ' + str(o_zone_name_list[max_OD_index]) + ' to ' +
          str(d_zone_name_list[max_OD_index]))
    logger.info('Zone-to-zone OD pair with largest volume is from ' + str(o_zone_name_list[max_OD_index]) + ' to ' +
          str(d_zone_name_list[max_OD_index]))

    # print(data)
    if g_output_folder is not None:
        demand_filepath = os.path.join(g_output_folder, 'demand.csv')
        data.to_csv(demand_filepath, index=False, line_terminator='\n')
    else:
        data.to_csv('demand.csv', index=False, line_terminator='\n')


"""PART 6  GENERATE AGENT"""
agent_list = []


def GenerateAgentBasedDemand():
    logger.debug("Starting GenerateAgentBasedDemand")
    global g_output_folder
    agent_id = 1
    agent_type = 'v'
    if g_output_folder is not None:
        demand_filepath = os.path.join(g_output_folder, 'demand.csv')
        agent_filepath = os.path.join(g_output_folder, 'input_agent.csv')
    else:
        demand_filepath = 'demand.csv'
        agent_filepath = 'input_agent.csv'

    with open(demand_filepath, 'r', errors='ignore') as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            for i in range(math.ceil(float(line['volume']))):
                agent = Agent(agent_id,
                              agent_type,
                              line['o_zone_id'],
                              line['d_zone_id'])

                # generate o_node_id and d_node_id randomly according to o_zone_id and d_zone_id
                agent.o_node_id = choice(g_zone_to_nodes_dict[str(agent.o_zone_id)])
                agent.d_node_id = choice(g_zone_to_nodes_dict[str(agent.d_zone_id)])
                agent_list.append(agent)
                agent_id += 1
    print('\nNumber of agents = ', len(agent_list))
    logger.info('Number of agents = '+str(len(agent_list)))
    if len(agent_list) == 0:
        print('Empty agent may be caused by empty poi demand. Please check node.csv or poi_trip_rate.csv!')
        logger.warning('Empty agent may be caused by empty poi demand. Please check node.csv or poi_trip_rate.csv!')

    with open(agent_filepath, 'w', newline='', encoding='gbk') as fp:
        writer = csv.writer(fp)
        line = ["agent_id", "agent_type", "o_node_id", "d_node_id", "o_osm_node_id",
                "d_osm_node_id", "o_zone_id", "d_zone_id", "geometry", "departure_time"]
        writer.writerow(line)
        for agent in agent_list:
            from_node = g_node_id_to_node[agent.o_node_id]
            to_node = g_node_id_to_node[agent.d_node_id]
            o_osm_node_id = from_node.osm_node_id
            d_osm_node_id = to_node.osm_node_id
            time_stamp = math.ceil(random.uniform(1, 60))
            if time_stamp == 60:
                departure_time = "0800"
            else:
                if time_stamp < 10:
                    departure_time = "070" + str(time_stamp)
                else:
                    departure_time = "07" + str(time_stamp)
            geometry = "LINESTRING({0} {1},{2} {3})".format(round(from_node.x_coord, 7), round(from_node.y_coord, 7),
                                                            round(to_node.x_coord, 7), round(to_node.y_coord, 7))
            line = [agent.agent_id, agent.agent_type, agent.o_node_id,
                    agent.d_node_id, o_osm_node_id,
                    d_osm_node_id, agent.o_zone_id, agent.d_zone_id, geometry, departure_time]
            writer.writerow(line)
    logger.debug("Ending GenerateAgentBasedDemand")
    # comments:
    # Please visit https://github.com/dabreegster/grid2demand/blob/scenario_script/src/demand_to_abst_scenario.py for simulation in AB Street

