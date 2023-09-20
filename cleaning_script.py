import sys, getopt
import pandas as pd
import re
import pprint

# usage: python3 cleaning_script.py 
# resultsFile:=[filepath] target:=[rtarget] agents:=[[agentlist]] 
# truthFile:=[filepath] target:=[ttarget] agents:=[[agentlist]]

# requires installation of seaborn - use pip3 install seaborn

def isolateTargetCoordsTruth(csvfile, targetname):
    file_df = pd.read_csv(csvfile)
    df_copy = file_df.copy() # so we don't mess with the original data
    
    coordinateDictionary = dict()
    coordinateDictionary['target'] = targetname
    coordinateDictionary['data'] = list()
    target_index = df_copy[".name"][0].strip("[]").replace("'","").split(", ").index(targetname) # so we can find right target data in position list
    
    for index, item in enumerate(list(df_copy[".pose"].items())):
        plain_text_coords = item[1].split(",")[target_index].replace(" ","") # get just positioning data for target, format as well
        timestamp = list(df_copy["time"].items())[index][1]
        first_timestamp = timestamp[0]
        xyz = re.findall(r"[xyz]:[-+]?(?:\d*\.*\d+)", plain_text_coords)  # regex the text
        xyz = [p[2:] for p in xyz]
        xyz = [plain_text_coords.split()[p] for p in [1, 2, 3]]
        xyz = [p[2:] for p in xyz]  # drop the axis
        coordinateDictionary['data'].append({'timestamp' : timestamp, 'timestep' : index, 'coordinates' : {'x': xyz[0], 'y': xyz[1], 'z' : xyz[2]}}) # list of timestamps, each with dict of coords
    return coordinateDictionary

def isolateTargetCoordsAndCovarienceTest(csvfile, agentname):
    file_df = pd.read_csv(csvfile)
    df_copy = file_df.copy() # so we don't mess with the original data
    coordandcovdict = dict()
    coordandcovdict['agent'] = agentname
    coordandcovdict['data'] = list()
    items = df_copy.items()
    for index, item in enumerate(list(df_copy[".TMu"].items())):
        if list(df_copy[".Agent"].items())[index][1] == agentname:
            timestamp = list(df_copy["time"].items())[index][1]
            timestep = list(df_copy[".TimeStep"].items())[index][1]
            TMu = item[1].strip("()").replace(" ","").split(",")
            TCov = list(df_copy[".TCov"].items())[index][1].strip("()").replace(" ","").split(",")
            coordandcovdict['data'].append({'timestamp' : timestamp, 'timestep' : timestep ,
                                            'x' : TMu[0], 'y' : TMu[1], 'vx' : TMu[2], 'vy' : TMu[3] ,
                                            'varX' : TCov[0], 'varY' : TCov[5], 'varVx' : TCov[10], 'varVy' : TCov[15]})
    return coordandcovdict

def createErrorGraph(truthdict, resultsdict):
    """
    *Calculate xy standard deviation (two variables), and plot it as a horizontal line
    *Plot the square root of the covarience
    *plot the error
    x axis is timestamp, y axis is in m? Whatever the x,y pos is in
    Make a graph for each item in the vector
    To standardise data, make a timestep for each bit. What is the timestep for the results? What is the timestep for the gazebo?
    The gazebo file might have a longer run time, so we need to use only the data that is also present in the truth.
    """
    pass

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
    
def standardiseData(truthdict, resultsdict, startingtime):
    """
    Timesteps in truth file are about 
    """
    newdict = dict()
    newdict['target'] = truthdict['target']
    newdict['data'] = list()
    counter = 0
    startingindex = 0
    for index, item in enumerate(truthdict['data']):
        if item.get('timestamp') == startingtime:
            startingindexindex = index
            break 
    timestep = round(findAverageTimestep(resultsdict) / findAverageTimestep(truthdict))
    while (counter < len(resultsdict['data'])):
        try:
            newdict['data'].append(truthdict['data'][timestep * counter + startingindex])
            counter = counter + 1
        except:
            break
    return newdict
    

def main():
    # testing
    gazebo_truth = isolateTargetCoordsTruth("2023-08-16-12-58-55-gazebo-model_states.csv","tycho_bot_1")
    resultsX1 = isolateTargetCoordsAndCovarienceTest("2023-08-29-10-20-22-results.csv", 'X1')
    resultsX2 = isolateTargetCoordsAndCovarienceTest("2023-08-29-10-20-22-results.csv", 'X2')
    gazebo_standard = standardiseData(gazebo_truth, resultsX1,'1969/12/31/17:06:35.445000')
    pprint.pprint(gazebo_standard)
    pprint.pprint(resultsX1)
    
main()