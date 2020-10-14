'''
    PyElph - Band detection, matching and processing
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


from numpy import argsort, array, compress, delete, exp, linspace, log, \
                  polyfit, polyval, rot90, zeros

from Lane import extractLevelsFormLanes


def extractBands(data, lanes, detectThreshold = 20, filterWidth = 3, filterPasses = 10): # for some images 40 # TODO: filter params in params list
    bands = [[] for i in range(len(lanes))]
    k=0
    
    for laneData, idx in extractLevelsFormLanes(data, lanes, filterWidth, filterPasses): # 2, 5; for small images , 1, 3
        
#        printLaneLevels(laneData, detectThreshold * (lanes[k][1] - lanes[k][0]))
         
        laneDataCompressed = array(laneData)
        indices = linspace(0, laneData.size-1, laneData.size)
        j = 1
        while j < laneDataCompressed.size:
            if laneDataCompressed[j] == laneDataCompressed[j-1]:
                laneDataCompressed = delete(laneDataCompressed, j)
                indices = delete(indices, j)
            else:
                j += 1
                
        for i in range(1, len(laneDataCompressed)-1):
            if laneDataCompressed[i-1] < laneDataCompressed[i] \
               and laneDataCompressed[i+1] < laneDataCompressed[i]:
                j = int((indices[i] + indices[i+1]-1)/2)
                if laneData[j] > detectThreshold * (lanes[k][1] - lanes[k][0]):
                    bands[k].append([idx, j])
        k += 1
        
    return bands

def bandMatching(bands, threshold = 10):
    bands[:] = map(lambda x: map(lambda y: y + [-1], x), bands)
#    print 'Add cluster index field:', bands
            
    bands = reduce(lambda x, y: x + y, bands)
#    print 'Flat bands list:', bands
    
    bands = sorted(bands, lambda x, y: cmp(x[1], y[1]))
#    print 'Sorted bands list by height:', bands
    
    dist = array(bands)[:, 1]
#    print 'Heights of bands:', dist

    dist = dist[1:] - dist [:-1]
#    print 'Distances between consecutive bands:', dist
    
    indices = argsort(dist)
#    print 'Indices in sorted vector of distances:', indices
    
    k = 0
    clusters = []
#    print clusters
    for i in indices:
#        print '----------------------------------------------------------------'
        if dist[i] > threshold or bands[i][0] == bands[i+1][0]: #TODO: add proper condition
#            print 'No match', i, dist[i], bands[i], bands[i+1]
            if bands[i][2] >= 0 and bands[i+1][2] < 0: # band i has cluster and band i+1 does not have a cluster
                bands[i+1][2] = k
                clusters.append([bands[i+1]])
                k += 1
            elif bands[i][2] < 0 and bands[i+1][2] >= 0: # band i does not have a cluster and band i+1 has a cluster
                bands[i][2] = k
                clusters.append([bands[i]])
                k += 1
            elif bands[i][2] < 0 and bands[i+1][2] < 0: # neither have clusters
                bands[i][2] = k
                clusters.append([bands[i]])
                k += 1
                bands[i+1][2] = k
                clusters.append([bands[i+1]])
                k += 1
        else:
#            print 'Match', i, dist[i], bands[i], bands[i+1]
            if (bands[i][2] >= 0 and bands[i+1][2] < 0) or (bands[i][2] < 0 and bands[i+1][2] >= 0): # one band has a cluster the other does not
#                print 'Cluster 0/1 :', bands[i], bands[i+1]
                if bands[i][2] >= 0:
                    cluster = bands[i][2]
                    newBand = bands[i+1]
                else:
                    cluster = bands[i+1][2]
                    newBand = bands[i]
                
                if any(map(lambda band: band[0] == newBand[0], clusters[cluster])): # pentru fiecare componenta din cluster verific daca lane-ul este acelasi (adica x)
                    newBand[2] = k             # new cluster
                    clusters.append([newBand])
                    k += 1
                else:
                    if any(map(lambda band: abs(band[1] - newBand[1]) > threshold, clusters[cluster])): # verify is distance is ok
                        newBand[2] = k             # new cluster
                        clusters.append([newBand])
                        k += 1
                    else:
                        newBand[2] = cluster
                        clusters[cluster].append(newBand)
#                print 'Cluster 0/1 :', bands[i], bands[i+1]
#            elif bands[i][2] < 0 and bands[i+1][2] > 0: # band i does not have a cluster and band i+1 has a cluster
#                bands[i][2] = bands[i+1][2]
            elif bands[i][2] < 0 and bands[i+1][2] < 0: # neither have clusters
#                print 'Cluster 0/0 :', bands[i], bands[i+1]
                bands[i][2] = bands[i+1][2] = k
                clusters.append([bands[i], bands[i+1]])
                k += 1
#                print 'Cluster 0/0 :', bands[i], bands[i+1]
            else: # both have clusters
#                print 'Cluster 1/1 :', bands[i], bands[i+1]
                cluster1 = bands[i][2]
                cluster2 = bands[i+1][2]
                if not any(map(lambda band1: any(map(lambda band2: band1[0] == band2[0], clusters[cluster2])), clusters[cluster1])):
#                    print 'Merge valid 1'
                    if not any(map(lambda band1: any(map(lambda band2: abs(band1[1] - band2[1]) > threshold, clusters[cluster2])), clusters[cluster1])):
#                        print 'Merge valid 2'
                        cluster, clusterRemove = min(cluster1, cluster2), max(cluster1, cluster2)
                        
                        for band in clusters[clusterRemove]:
                            band[2] = cluster
                        clusters[cluster].extend(clusters[clusterRemove])
                        
                        del clusters[clusterRemove]
                        
                        for cls in clusters[clusterRemove:]:
                            for band in cls:
                                band[2] -= 1
                        k -= 1
#                print 'Cluster 1/1 :', bands[i], bands[i+1]
#        print clusters

#    print array(bands)    
#    clNo = -1
#    last = -1
#    for b in bands:
#        if b[2] != last:
#            clNo += 1
#            last = b[2]
#        b[2] = clNo
        
#    print 'No clusters:', k
#    print array(bands)
#    for i, b in enumerate(bands):
#        print array(b), i
    
    clusters = map(lambda cl: sorted(cl, lambda x, y: cmp(x[0], y[0])), clusters)
    
#    minY = [array(zip(*cl)[1]).min() for cl in clusters]
#    for cl in clusters:
#        print cl
#    print 'minY:', minY
    clusters = sorted(clusters, key=lambda cl: array(zip(*cl)[1]).min())
    for k, cl in enumerate(clusters):
        for b in cl:
            b[2] = k
        
#    for cl in clusters:
#        print cl
    return clusters

def extractWeightsModel(bands, refWeights, markerLane=0):
    displ = map(lambda x: x[1], bands[markerLane])
    logM = log(refWeights)
#    return polyfit(displ, logM, 1)
    p = polyfit(logM, displ, 1)
    return array([1/p[0], -p[1]/p[0]])

def computeWeights(bands, model, markerLane=0):
    weights = map(lambda x: polyval(model, array(map(lambda y: y[1], x))), bands)
    return map(lambda x: array(exp(x), dtype='int32'), weights)

def computeMatchMatrix(bands, noClusters, markerLane=None):
    matrix = zeros([noClusters, len(bands)])
    
    for k in range(len(bands)):
        for x, y, cl in bands[k]:
            matrix[cl, k] = 1
    
#    print matrix
#    print
    if markerLane != None:
        matrix = delete(matrix, markerLane, 1)
#    print matrix
#    print
    
    #    k = 0
#    while k < matrix.shape[0]:
#        if not any(matrix[k, :]):
#            matrix = delete(matrix, k, 0)
#        else:
#            k += 1

    return compress(matrix.sum(1) != 0, matrix, axis=0)

def drawBands(data, bands):
    #TODO: plot bands on image with matplotlib
    pass

def drawBandMatching(data, bands):
    #TODO: plot band matching on image with matplotlib
    pass

#Deprecated
#TODO: use matplotlib instead
def generateMatlabPlotLanesData(data, lanes):
    k=1
    for laneData, idx in extractLevelsFormLanes(data, lanes):
        print 'Lane' + str(k), '=', map(int, laneData), ';'
        print 'figure(', k, ');hold on;'
        print 'plot(Lane'+str(k)+');'
        print 'plot('+str(lanes[k-1][1]-lanes[k-1][0])+'*20*ones(1, length(Lane'+str(k)+')));'
        print 'hold off;'
        k = k+1    

#Deprecated
#TODO: use matplotlib instead
def generateMatlabPlotBandsData(data, lanes, bands):
    k = 0
    for b in bands:
#        print 'Bands', k, ':', len(b)
        idxBegin = lanes[k][0]
        idxEnd = lanes[k][1]
        j=0
        for y, x in b:
            print 'Band' + str(k)+ str(j), '=', map(int, data[x, idxBegin:idxEnd]), ';'
            print 'plot(Band' + str(k)+ str(j) + ')'
            print "xlabel('Lane " + str(k) + ' Band ' + str(j) + "')"
            print 'ylim([0, 255])'
            print 'pause'
            j += 1
        k+=1


if __name__ == "__main__": pass
#TODO: redo test code
#    from numpy import savetxt
#    from BackgroundSubstraction import backgroundSubstraction
#    from Lane import extractLevelsFormLanes, drawLanes, extractLanes, printLaneLevels
#    from PhylTree import distanceMatrix, neighbourJoining, similarityMatrix, showTree
#
#    data = <TODO>
#    lanes = extractLanes(data)[0]
#    print lanes
#    
#    back = backgroundSubstraction(data, lanes)
#    
##    generateMatlabPlotLanesData(data, lanes)
#
#    bands = extractBands(back, lanes)
#    
##    generateMatlabPlotBandsData(back, lanes, bands)
#    
##    drawLanes(back, lanes)
##    drawBands(back, bands)
##    drawLanes(data, lanes)
##    drawBands(data, bands)
#    
#    model = extractWeightsModel(bands, array([2*(10**10), 2*(10**9), 2*(10**8),
#            2*(10**7), 2*(10**6), 2*(10**5), 2*(10**4), 2*(10**3), 2*(10**2),
#            2*(10**1), 2]))
#    print model
##    weigths = computeWeights(bands, model)
##    print 'Molecular Weights:'
##    for w in weigths:
##        print w
##    print
##    
##    print 'Bands:', bands
##    noClusters = len(bandMatching(bands, 10))
##    print 'clusters', noClusters
##    print 'Bands:', bands
##    
##    drawBandMatching(back, bands)
###    drawBandMatching(data, bands)
##
##    matrix = computeMatchMatrix(bands, noClusters)
##    print matrix
##    savetxt('match_matrix.txt', matrix, '%d')
#    
##    simMatrix = similarityMatrix(matrix)
##    print simMatrix
##    distMatrix = distanceMatrix(simMatrix)
##    print distMatrix
##    tree, dist = neighbourJoining(distMatrix)    
##    showTree(tree, dist, distMatrix.shape[0])