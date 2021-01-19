import grid2demand as gd

"Step 1: Read Input Network Data"
net = gd.readNetworkFile()

"Step 2: Network Partition into Grids"
zone = gd.NetworkPartition(number_of_x_blocks=None,number_of_y_blocks=None,grid_width=500,grid_height=500,latitude=None)
# user can customize number of grids or grid's length and width

"Step 3: Get Production/Attraction Rates of Each Land Use Type with a Specific Trip Purpose"
triprate = gd.getPoiTripRate(trip_rate_folder=None,trip_purpose=1)
# user can customize poi_trip_rate.csv and trip purpose

"Step 4: Define Production/Attraction Value of Each Node According to POI Type"
nodedemand = gd.getNodeDemand()

"Step 5: Calculate Zone-to-zone Accessibility Matrix by Centroid-to-centroid Straight Distance"
accessibility = gd.AccessMatrix(latitude=None,accessibility_folder=None)
# user can customize the latitude of the research area and accessibility.csv

"Step 6: Apply Gravity Model to Conduct Trip Distribution"
demand = gd.GravityModel(trip_purpose=None,a=None,b=None,c=None)
# user can customize friction factor coefficients under a specific trip purpose

"Step 7: Output zone.csv, poi_trip_rate.csv, accessibility.csv, demand.csv and Update node.csv, poi.csv"
gd.outputCSV()