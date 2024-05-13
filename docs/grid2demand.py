# -*- coding:utf-8 -*-
##############################################################
# Created Date: Wednesday, April 5th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

# Step 1: Import the required packages

# pip install osm2gmns
# pip install grid2demand
#
# Step 2: Convert osm to gmns
import osm2gmns as og
import os

os.chdir("./dataset/Avondale_AZ/")


path_osm = "Avondale.osm"

net = og.getNetFromFile(path_osm, POI=True, network_types=('walk', 'railway', 'aeroway', 'bike', 'auto'))
og.connectPOIWithNet(net)
og.generateNodeActivityInfo(net)
og.consolidateComplexIntersections(net)
# og.outputNetToCSV(net, output_folder='consolidated')
og.outputNetToCSV(net)
# og.show(net)
# og.saveFig(net)


# Step 3: Run grid2demand to generate demand based POI rates
import grid2demand as gd

"Step 1: Read Input Network Data"
net = gd.ReadNetworkFiles('')

"Step 2: Partition Grid into cells"
zone = gd.PartitionGrid(number_of_x_blocks=5, number_of_y_blocks=5)
# user can customize number of grid cells or cell's width and height

"Step 3: Get Production/Attraction Rates of Each Land Use Type with a Specific Trip Purpose"
triprate = gd.GetPoiTripRate(trip_rate_folder='', trip_purpose=1)
# user can customize poi_trip_rate.csv and trip purpose

"Step 4: Define Production/Attraction Value of Each Node According to POI Type"
nodedemand = gd.GetNodeDemand()

"Step 5: Calculate Zone-to-zone Accessibility Matrix by Centroid-to-centroid Straight Distance"
accessibility = gd.ProduceAccessMatrix(latitude=30, accessibility_folder='')
# user can customize the latitude of the research area and accessibility.csv

"Step 6: Apply Gravity Model to Conduct Trip Distribution"
demand = gd.RunGravityModel(trip_purpose=1, a=None, b=None, c=None)
# user can customize friction factor coefficients under a specific trip purpose
"Step 7: Generate Agent"
demand = gd.GenerateAgentBasedDemand()
