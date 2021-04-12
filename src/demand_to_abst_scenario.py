"""
Transform the input_agents.csv file produced by Grid2Demand into the JSON
format used by A/B Street to import scenarios
(https://a-b-street.github.io/docs/trafficsim/travel_demand.html#custom-import).
"""

import argparse
import csv
import json
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    scenario = {
        'scenario_name': 'grid2demand',
        'people': []
    }
    with open(args.input) as f:
        for row in csv.DictReader(f):
            # If there are more values, just change 'Mode' below.
            assert(row['agent_type'] is 'v')
            origin, destination = parse_linestring(row['geometry'])
            departure = parse_time(row['departure_time'])
            # For each row in the CSV file, create a person who takes a single
            # trip from the origin to the destination. They do not take a later
            # trip to return home.
            scenario['people'].append({
                'origin': {
                    'Position': origin
                },
                'trips': [{
                    'departure': departure,
                    'destination': {
                        'Position': destination
                    },
                    'mode': 'Drive',
                    'purpose': 'Work'
                }]
            })

    with open(args.output, 'w') as f:
        f.write(json.dumps(scenario, indent=2))
    print('Wrote', args.output)
    print('Follow https://a-b-street.github.io/docs/trafficsim/travel_demand.html#custom-import to import into A/B Street')


def parse_linestring(string):
    '''Transform a linestring with two points into two JSON latitude/longitude objects.'''
    nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d*)?', string)]
    return ({'longitude': nums[0], 'latitude': nums[1]}, {'longitude': nums[2], 'latitude': nums[3]})


def parse_time(string):
    '''Transform an HHMM time into the number of seconds after midnight.'''
    hours = int(string[0:2])
    mins = int(string[2:])
    return (3600.0 * hours) + (60.0 * mins)


if __name__ == '__main__':
    main()
