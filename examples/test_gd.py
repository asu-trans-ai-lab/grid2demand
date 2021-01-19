import grid2demand as gd

"Step 1: Read Input Network Data"
net = gd.readNetworkFile("./data_folder")

"Step 2: Network Partition into Grids"
zone = gd.NetworkPartition(number_of_x_blocks = 5, number_of_y_blocks = 5)
# user can customize number of grids or grid's length and width

"Step 3: Get Production/Attraction Rates of Each Land Use Type with a Specific Trip Purpose"
triprate = gd.getPoiTripRate()
# user can customize poi_trip_rate.csv and trip purpose

"Step 4: Define Production/Attraction Value of Each Node According to POI Type"
nodedemand = gd.getNodeDemand()

"Step 5: Calculate Zone-to-zone Accessibility Matrix by Centroid-to-centroid Straight Distance"
accessibility = gd.AccessMatrix()
# user can customize the latitude of the research area

"Step 6: Apply Gravity Model to Conduct Trip Distribution"
demand = gd.GravityModel()

"Step 7: Output zone.csv, poi_trip_rate.csv, accessibility.csv, demand.csv and Update node.csv, poi.csv"
gd.outputCSV("./data_folder")