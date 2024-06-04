import re

def findDataAfterColon(data):
    return re.findall(r':(.*)', data)[0]

def jsonify(data, pose_dicts):
    # Split the data into poses
    poses = data.split('pose:')[1:]
    for elem in poses:
        elem = elem.split(',,,,,\n')
        elem = [e.replace(" ", "") for e in elem]
        elem.pop(0)
        elem[8] = elem[8].split(',')
        elem[8] = [elem[8][0], elem[8][1], elem[8][-1]]
        elem.insert(9, elem[8][1])
        elem.insert(10, elem[8][-1].replace('\n', ''))
        elem[8] = elem[8][0]
        pose_dicts.append({
            'position': {
                'x': float(findDataAfterColon(elem[1])),
                'y': float(findDataAfterColon(elem[2])),
                'z': float(findDataAfterColon(elem[3]))
            },
            'orientation': {
                'x': float(findDataAfterColon(elem[5])),
                'y': float(findDataAfterColon(elem[6])),
                'z': float(findDataAfterColon(elem[7])),
                'w': float(findDataAfterColon(elem[8]))
            },
            'header': {
                'seq': float(findDataAfterColon(elem[10])),
                'stamp': {
                    'secs': int(findDataAfterColon(elem[12])),
                    'nsecs': int(findDataAfterColon(elem[13]))
                },
                'frame_id': findDataAfterColon(elem[14].replace('"', ''))
            }
        })

    return pose_dicts


def read_data(filepath):
    datalist = []
    with open(filepath, 'r') as file: # peacemealed so that this func doesn't take up a huge amount of memory
        for i in range(7): file.readline()
        while True:
            datapiece = ""
            for i in range(15):
                datapiece += file.readline()
                if not datapiece:
                    return datalist
            print(datapiece)
            jsonify(datapiece, datalist)
            
print(read_data('H03_may24_0-H03-lio_sam-mapping-path_short.csv'))
