import sys
import os
import pandas as pd
import re
import pprint
import matplotlib.pyplot as plt
import numpy as np
import json

# usage: python3 cleaning_script.py 
# resultsFile:=[filepath] target:=[rtarget] agents:=[[agentlist]] 
# truthFile:=[filepath] target:=[ttarget] agents:=[[agentlist]]

# requires installation of seaborn - use pip3 install seaborn

def readInputDataGazebo(csvfile, targetname):
    file_df = pd.read_csv(csvfile)
    df_copy = file_df.copy() # so we don't mess with the original data
    
    coordinateDictionary = dict()
    coordinateDictionary['target'] = targetname
    coordinateDictionary['data'] = list()
    target_index = df_copy[".name"][0].strip("[]").replace("'","").split(", ").index(targetname) # so we can find right target data in position list
    posedict = dict()
    twistdict = dict()
    
    for item in list(df_copy[".twist"].items()):
        plain_text_coords = item[1].split(",")[target_index].replace(" ","") # get just positioning data for target, format as well
        # print(re.findall(r"[xyzw]:[-+]?(?:\d*\.*\d+)", plain_text_coords))
        xyz = re.findall(r"[xyz]:[-+]?(?:\d*\.*\d+)", plain_text_coords)  # regex the text
        xyz = [p[2:] for p in xyz]
        xyz = [plain_text_coords.split()[p] for p in [1, 2, 3, 5, 6, 7]]
        xyz = [p[2:] for p in xyz]  # drop the axis
        twistdict = {'linear' : {'x': xyz[0], 'y': xyz[1], 'z' : xyz[2]}, 'angular' : {'x': xyz[3], 'y': xyz[4], 'z' : xyz[5]}}
    
    for index, item in enumerate(list(df_copy[".pose"].items())):
        plain_text_coords = item[1].split(",")[target_index].replace(" ","") # get just positioning data for target, format as well
        timestamp = list(df_copy["time"].items())[index][1]
        # print(re.findall(r"[xyzw]:[-+]?(?:\d*\.*\d+)", plain_text_coords))
        xyz = re.findall(r"[xyzw]:[-+]?(?:\d*\.*\d+)", plain_text_coords)  # regex the text
        xyz = [p[2:] for p in xyz]
        xyz = [plain_text_coords.split()[p] for p in [1, 2, 3, 5, 6, 7, 8]]
        xyz = [p[2:] for p in xyz]  # drop the axis
        posedict = {'position' : {'x': xyz[0], 'y': xyz[1], 'z' : xyz[2]}, 'orientation' : {'x': xyz[3], 'y': xyz[4], 'z' : xyz[5], 'w' : xyz[6]}}
        coordinateDictionary['data'].append({'timestamp' : timestamp, 'timestep' : index, '.pose' : posedict, '.twist' : twistdict}) # list of timestamps, each with dict of coords
    return coordinateDictionary

def readInputDataTest(csvfile, agentname, begindatarow):
    file_df = pd.read_csv(csvfile)
    df_copy = file_df.copy() # so we don't mess with the original data
    coordandcovdict = dict()
    coordandcovdict['agent'] = agentname
    coordandcovdict['data'] = list()
    items = df_copy.items()
    for index, item in enumerate(list(df_copy[".TMu"].items())):
        if list(df_copy[".Agent"].items())[index][1] == agentname:
            timestamp = list(df_copy["time"].items())[index][1]
            timestep = float(list(df_copy[".TimeStep"].items())[index][1]) - begindatarow
            TMu = item[1].strip("()").replace(" ","").split(",")
            TCov = list(df_copy[".TCov"].items())[index][1].strip("()").replace(" ","").split(",")
            coordandcovdict['data'].append({'timestamp' : timestamp, 'timestep' : timestep ,
                                            'x' : TMu[0], 'y' : TMu[1], 'vx' : TMu[2], 'vy' : TMu[3] ,
                                            'varX' : TCov[0], 'varY' : TCov[5], 'varVx' : TCov[10], 'varVy' : TCov[15]})
    return coordandcovdict

def createErrorGraph(truthdict, resultsdict, datapoint, datasubscriber, dataspecifier):
    """
    *Calculate xy standard deviation (two variables), and plot it as a horizontal line
    *Plot the square root of the covarience
    *plot the error
    x axis is timestamp, y axis is in m? Whatever the x,y pos is in
    Make a graph for each item in the vector
    To standardise data, make a timestep for each bit. What is the timestep for the results? What is the timestep for the gazebo?
    The gazebo file might have a longer run time, so we need to use only the data that is also present in the truth.
    """
    x = list()
    yTruth = list()
    yErr = list()
    yCov = list()
    yStandardDev = list()
    yNegSDev = list()
    for item in list(truthdict['data']):
        yTruth.append(float(item[datasubscriber][dataspecifier][datapoint]))
    for count, item in enumerate(list(resultsdict['data'])):
        x.append(int(item['timestep']))
        yErr.append((yTruth[count] - float(item[datapoint]))) # error = pos in gazebo - pos in results
        yCov.append(float(item['var'+datapoint.upper()]))
    yStandardDev = [(np.sqrt(np.abs(y)) * 2) for y in yCov] # standard deviation is sqrt of covariance
    yNegSDev = [-y for y in yStandardDev]
    # Create a Matplotlib figure and axis
    plt.figure(figsize=(8, 6))
    plt.title('Error and standard deviation for ' + str(dataspecifier) + ' ' + str(datapoint) + ' with agent ' +
              resultsdict['agent'] + ' and target ' + truthdict['target'])
    plt.xlabel('timestep')
    plt.ylabel(dataspecifier + ' error')
    
    plt.plot(x, yErr, label='Error', color='red')
    plt.plot(x, yStandardDev, label='2$\sigma$', color='green')
    plt.plot(x, yNegSDev, color='green')
    plt.axhline(y = 0, linestyle = 'dashed')
    plt.fill_between(x, yStandardDev, yNegSDev, alpha=.2, linewidth=0, color='green')
    plt.ylim(-40, 40)

    # Add a legend to distinguish the lines
    plt.legend()
    plt.savefig(resultsdict['agent']+datapoint+"_err.jpg", dpi=500)

def findAverageTimestep(dictfile):
    # All of the data is collected within a minute, so we can safely subtract without converting
    oddstep = []
    evenstep = []
    minitecorrection = 0
    startingminute = float(dictfile['data'][0]['timestamp'][-12:-10])
    
    sum = 0
    for count, item in enumerate(reversed(dictfile['data'])):
        minutecorrection = float(item['timestamp'][-12:-10]) - startingminute
        if count % 2 == 0: oddstep.append(float(item['timestamp'][-9:]) + (minutecorrection*60))
        else: evenstep.append(float(item['timestamp'][-9:]) + (minutecorrection*60))
    for count, item in enumerate(oddstep):
        try:
            sum += (item - evenstep[count])
        except:
            continue
    
    return sum / (len(oddstep))
    
def standardiseData(truthdict, resultsdict):
    """
    startingtime represents the starting time to match data in the gazebo file - starting time of gazebo truth to match with results
    Algo: 
        1. get the first row of data from the results
        2. Find the average timestep for the gazebo and the results
        3. Parse gazebo data into a new dict starting from that index up until the last index of the results file
    """
    newdict = dict()
    newdict['target'] = truthdict['target']
    newdict['data'] = list()
    counter = 0
    startingindex = 0
    for index, item in enumerate(truthdict['data']):
        if item.get('timestamp') == resultsdict['data'][0]['timestamp']: # want the first index of data from the results
            startingindex = index
            break 
    timestep = round(findAverageTimestep(resultsdict) / findAverageTimestep(truthdict))
    while (counter < len(resultsdict['data'])):
        try:
            newdict['data'].append(truthdict['data'][timestep * counter + startingindex])
            counter = counter + 1
        except:
            break
    return newdict
    

def main(args):
    # testing
    if(len(args) != 8):
        print("Missing one of the required arguments:\n" + """
    
        args[1] "2023-08-16-12-58-55-gazebo-model_states.csv" - truth file
        args[2] "tycho_bot_1" - truth target
        args[3] "2023-08-29-10-20-22-results.csv" - results file
        args[4] "X1" - agent
        args[5] "position" - datacategory
        args[6] ".pose" - subscriber
        args[7] "x,y" - datapoints
        
        I.E:
        "2023-08-16-12-58-55-gazebo-model_states.csv" "tycho_bot_1" "2023-08-29-10-20-22-results.csv" "X1" "position" ".pose" "x,y"
        """)
        print("Missing one of the required arguments:\n") 
        dateAndTime = "2023-08-16-12-58-55"       
        args = dict()
        args[1] = dateAndTime + "-gazebo-model_states.csv"  #truth file
        args[2] = "tycho_bot_1" #truth target
        args[3] = dateAndTime + "-results.csv" #- results file
        args[4] = "X2" #- agent
        # args[5] = "1969/12/31/17:4:4.896000" #- starting time
        args[5] = "position" #- datacategory
        args[6] = ".pose" #- subscriber
        args[7] = "x,y" #- datapoint
        
        """I.E:
        "2023-08-16-12-58-55-gazebo-model_states.csv" "tycho_bot_1" "2023-08-29-10-20-22-results.csv" "X1" "position" ".pose" "x"
        """
        # return -1
    
        # return -1
    
    datapoints = args[7].split(',')
    gazebo_truth = None
    results = None
    
    print('Creating Error graphs for datapoints',datapoints)
    
    # read gazebo file
    if (args[1][-4:] == ".csv"):
        print("Reading Gazebo simulation file...")
        gazebo_truth = readInputDataGazebo(args[1],args[2])
        # save csv results to json
        with open('gazebo_data.json', 'w') as file:
            json.dump(gazebo_truth, file)
        print('Data stored successfully!')
    elif (args[1][-5:] == ".json"):
        # read json file into dict format
        with open('gazebo_data.json', 'r') as file:
            gazebo_truth = json.load(file)
        pass
    else:
        print("Input file format not supported: {argv[1]} must be of type json or CSV.")
        return -1
    
    # read result file
    if (args[3][-4:] != ".csv"):
        print("Input file format not supported: {argv[3]} must be of type CSV.")
    else:
        print("Reading results file...")
        results = readInputDataTest(args[3], args[4], 2)
    
    # create the graphs
    print("Creating graphs...")
    gazebo_standard = standardiseData(gazebo_truth, results)
    for datapoint in datapoints:
        createErrorGraph(gazebo_standard, results, datapoint, args[6], args[5])
    print("Graphs saved to",os.getcwd())
    return 0

main(sys.argv)