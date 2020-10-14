'''
    PyElph - Lane detection and processing
    Copyright (C) 2012  Ana Brandusa Pavel <anabrandusa@gmail.com>,
                        Cristian Ioan Vasile <cristian.ioan.vasile@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


from numpy import array, greater, mean


def laneSpectrum(laneData, threshold):
    laneData = ''.join(map(str, greater(laneData, threshold)*1))

    lanes = []
    idxEnd = 0
    while True:
        idxBegin = laneData.find('1', idxEnd)
        if idxBegin == -1:
            break;
        idxEnd = laneData.find('0', idxBegin)
        if idxEnd == -1:
#            idxEnd = len(laneData)
            break
        
        lanes.append((idxBegin, idxEnd))
    
    return lanes

def computeMeanLaneWidth(laneData, level):
    laneLengths = array(map(lambda x: x[1] - x[0], laneSpectrum(laneData, level)))
#    print laneLengths
    
    meanLaneWidth = laneLengths.mean()
    laneLengths2 = array(filter(lambda x: meanLaneWidth <= x, laneLengths))

    meanLaneWidth = laneLengths2.mean()
    laneLengths3 = array(filter(lambda x: meanLaneWidth*0.75 <= x <= meanLaneWidth * 1.25, laneLengths2))
    
    if len(laneLengths3) == 0:
        return max(laneLengths2)
    
    return laneLengths3.mean()

def extractLanes(data, proc = 0.25, highTh = 0.70, lowTh = 0.15, meanLaneWidth = None):
    laneData = data.max(0)
    minLevel = laneData.min()
    maxLevel = laneData.max()
    
    if meanLaneWidth == None:
        absThH = minLevel + highTh * (maxLevel - minLevel)
        meanLaneWidth = computeMeanLaneWidth(laneData, absThH)
    
    lanes = []
    for level in range(maxLevel, int(minLevel + lowTh*(maxLevel-minLevel)), -1):
        lanes2 = laneSpectrum(laneData, level)
    #    print 'Low conf lanes:', lanes2
    #    data2 = array(data)
    #    drawLanes(data2, lanes2)
        
        i = 0
        for lane2 in lanes2:
    #        print '----------------------------------------------------------------'
    #        print 'Current low conf lane:', lane2
            if abs((lane2[1] - lane2[0]) - meanLaneWidth) < proc * meanLaneWidth: # daca latimea este buna
    #            print 'Current low conf lane:', lane2, ', accepted'
                
                idx = -1
                for j in range(len(lanes[i:])):
    #                print 'Compare with:', lanes[i+j]
                    if lane2[0] <= lanes[i+j][0]:
                        idx = i+j
                        break
                
                if idx >= 0:
    #                print 'Found match:', idx, lanes[idx] 
                    i = idx
                    if lane2[1] >= lanes[i][1]:
                        lanes[i] = lane2
                    else:
                        lanes.insert(i, lane2)
                        i += 1
                else:
    #                print 'Match not found'
                    lanes.append(lane2)
                    i = len(lanes)
    #        print '----------------------------------------------------------------'
    
    return lanes, meanLaneWidth

def extractLevelsFormLanes(data, lanes, windowWidth = 3, passes = 10):
    laneLevels = []
    for idxBegin, idxEnd in lanes:
        idxMiddle = (idxBegin + idxEnd)/2
#        laneLevels.append((data[:, idxMiddle], idxMiddle))
        laneLevel = data[:, idxBegin:idxEnd].sum(1)
        
        x = array(laneLevel)
        for i in range(passes):
            y = array(x)
            for t in range(windowWidth, x.size - windowWidth):
                y[t] = mean(x[t-windowWidth:t+windowWidth+1])
            x = array(y)
        
        laneLevels.append((x, idxMiddle))
    return laneLevels

def getRawLaneLevels(data, lane):
    idxBegin, idxEnd = lane
    idxMiddle = (idxBegin + idxEnd)/2
    return data[:, idxMiddle]


def drawLanes(data, lanes):
    #TODO: plot lanes on image with matplotlib
    pass

def printLaneLevels(laneLevels, detectionThreshold=0.20):
    import matplotlib.pyplot as plt
    
    plt.figure()
    x = range(len(laneLevels))
    plt.plot(x, map(int, laneLevels), 'b', \
             x, [detectionThreshold]*len(laneLevels), 'k')
    plt.show()

def printLaneSpectrum(data, filename, thH=0.70, thL=0.20):
    import matplotlib.pyplot as plt
    
    laneData = data.max(0)
    minVal = laneData.min()
    absThH = minVal + thH * (laneData.max() - minVal)
    absThL = minVal + thL * (laneData.max() - minVal)
    
    plt.figure()
    x = range(len(laneData))
    plt.plot(x, map(int, laneData), 'b', \
             x, [absThH]*len(laneData), 'k', \
             x, [absThL]*len(laneData), 'k')
#    plt.savefig(filename)
    plt.show()

if __name__ == '__main__': pass
#TODO: redo test code
#
#    filename = '<TODO>'
#    data = <TODO>
#    
#    printLaneSpectrum(data, filename + '.eps')
#    lanes, mL = extractLanes(data)
#    print lanes
#    
#    drawLanes(data, lanes)