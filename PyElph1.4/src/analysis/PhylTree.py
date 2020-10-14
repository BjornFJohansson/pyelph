'''
    PyElph - Phylogenetic tree computation
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


import math

from numpy import append, array, argmin, argwhere, delete, eye, linspace, \
                  ones, take, \
                  transpose, unravel_index, zeros


def similarityMatrix(data):
    # dice(i, j) = 2*n_ij/(n_i + n_j)
    
    nSamples = data.shape[1]
#    print nSamples
    
    numBands = data.sum(0)
#    print 'Sum over line:', numBands
    
    simMatrix = 100 * eye(nSamples)
    for i in range(nSamples):
        for j in range(i+1, nSamples):
            numBandsCommon = take(data, [i, j], 1).min(1).sum()
            simMatrix[i, j] = simMatrix[j, i] = \
                            200.0 * numBandsCommon / (numBands[i] + numBands[j])
    return simMatrix

def distanceMatrix(simMatrix):
    return 100-simMatrix

def neighbourJoining(distMatrix):
    N = distMatrix.shape[0]
    D = distMatrix[:, :]
    
    tree = -ones([N, 1])
    dist = zeros([N, 1])
    indices = linspace(0, N-1, N)
    
    while N > 2:
#        print '-----------------', N, '-----------------'
#        print 'D='
#        print D
        
        R = D.sum(0)
#        print 'R='
#        print R
        
        Q = (1+D.max()) * eye(N) # zeros([N, N]) #TODO: why does it work? safer:
        for i in range(N):
            for j in range(i+1, N):
                Q[i, j] = Q[j, i] = (N-2) * D[i, j] - R[i] - R[j]
        i, j = unravel_index(argmin(Q), Q.shape)
        mi = indices[i]
        mj = indices[j]
        
#        print 'Q='
#        print Q
#        print 'i,j=', (mi, mj), (i, j)
        
        # add parent to tree and change parent of leaf i and j
        tree = append(tree, -1)
        tree[mi] = tree[mj] = tree.size - 1
#        print 'Tree:', tree
    
        # compute distance to parent
        dist = append(dist, 0)
        dist[mi] = 0.5 * (D[i, j] + (R[i] - R[j])/(N-2) )
        dist[mj] = D[i, j] - dist[mi]
#        print 'Dist:', dist
        if dist[mi] < 0:
            dist[mj] -= dist[mi]
            dist[mi] = 0
        if dist[mj] < 0:
            dist[mi] -= dist[mj]
            dist[mj] = 0
        
        # recompute indices
        indices = delete(indices, [i, j])
        indices = append(indices, tree.size-1)
#        print 'Idxs:', indices
        
        # TODO: comment
        D_p = zeros([N-2, 1])
        idx = 0
        for k in range(N):
            if k!=i and k!=j:
                D_p[idx] = 0.5*(D[i, k] + D[j, k] - D[i, j])
                idx += 1
#        print 'D_p:', transpose(D_p)
        
#        print 'D - before:'
#        print D
        # compute distances from common parent to the other nodes
        D = delete(D, [i, j], 0)
        D = delete(D, [i, j], 1)
        
#        print 'D - after delete:'
#        print D
        
        # append new distances
        D = append(D, D_p, 1)
        D = append(D, append(transpose(D_p), 0).reshape(1, N-1), 0)
        
#        print 'D - after append:'
#        print D
        
        N -= 1
#        print '-------------------------------------'
    
    dist[indices[0]] = dist[indices[1]] = 0.5 * D[0, 1]
    
#    print '----------------FINAL----------------'
#    print 'Tree', tree
#    print 'Dist', dist
    
    return tree, dist

def singleLinkage(dik, djk, dij, ni, nj, nk):
    return min(dik, djk)

def completeLinkage(dik, djk, dij, ni, nj, nk):
    return max(dik, djk)

def upgma(dik, djk, dij, ni, nj, nk):
    return (dik * ni + djk * nj)/(ni + nj)

def wpgma(dik, djk, dij, ni, nj, nk):
    return (dik + djk)/2

def centroid(dik, djk, dij, ni, nj, nk):
    n = ni + nj
    return (dik * ni + djk * nk - (dij * ni * nj)/n )/n

def median(dik, djk, dij, ni, nj, nk):
    return (dik + djk - dij/2)/2

def ward(dik, djk, dij, ni, nj, nk):
    return (dik * (ni + nk) + djk * (nj + nk) - dij * nk) / (ni + nj + nk)

def computePhylTree(distMatrix, method):
    N = distMatrix.shape[0]
    D = distMatrix[:, :]
    
    tree = -ones([N, 1])
    dist = zeros([N, 1])
    distAbsl = zeros([N, 1])
    samples = ones([N, 1])
    indices = linspace(0, N-1, N)
    
    while N > 2:
#        print '-----------------', N, '-----------------'
        maxVal = 1 + D.max()
        D = D + eye(N) * (maxVal - D[0, 0])
#        print 'D='
#        print D

        i, j = unravel_index(argmin(D), D.shape)
        mi = indices[i]
        mj = indices[j]
#        print 'i,j=', (mi, mj), (i, j)
        
        # add parent to tree and change parent of leaf i and j
        tree = append(tree, -1)
        tree[mi] = tree[mj] = tree.size - 1
#        print 'Tree:', tree

        # compute absolute distance
        distAbsl = append(distAbsl, 0)    
        distAbsl[mi] = distAbsl[mj] = D[i, j]/2
#        print 'Dist absl:', distAbsl
        
        # compute distance to parent
        dist = append(dist, 0)
        if argwhere(tree == mi).size > 0:
            dist[mi] = distAbsl[mi] - distAbsl[argwhere(tree == mi)[0]]
        else:
            dist[mi] = distAbsl[mi]
        if argwhere(tree == mj).size > 0:
            dist[mj] = distAbsl[mj] - distAbsl[argwhere(tree == mj)[0]]
        else:
            dist[mj] = distAbsl[mj]
#        print 'Dist:', dist
        
        # compute number of samples
        samples = append(samples, samples[mi] + samples[mj])
        
        # TODO: comment
        D_p = zeros([N-2, 1])
        idx = 0
        for k in range(N):
            if k!=i and k!=j:
                D_p[idx] = method(D[i, k], D[j, k], D[i, j], \
                                  samples[mi], samples[mj], samples[indices[k]])
                idx += 1
#        print 'D_p:', transpose(D_p)
        
        # recompute indices
        indices = delete(indices, [i, j])
        indices = append(indices, tree.size-1)
#        print 'Idxs:', indices
        
#        print 'D - before:'
#        print D
        # compute distances from common parent to the other nodes
        D = delete(D, [i, j], 0)
        D = delete(D, [i, j], 1)
        
#        print 'D - after delete:'
#        print D
        
        # append new distances
        D = append(D, D_p, 1)
        D = append(D, append(transpose(D_p), maxVal).reshape(1, N-1), 0)
        
#        print 'D - after append:'
#        print D
        
        N -= 1
#        print '-------------------------------------'
    
    mi = indices[0]
    mj = indices[1]
    # compute absolute distance
    distAbsl[mi] = distAbsl[mj] = D[0, 1]/2
    
    # compute distance to parent
    if argwhere(tree == mi).size > 0:
        dist[mi] = distAbsl[mi] - distAbsl[argwhere(tree == mi)[0]]
    else:
        dist[mi] = distAbsl[mi]
    if argwhere(tree == mj).size > 0:
        dist[mj] = distAbsl[mj] - distAbsl[argwhere(tree == mj)[0]]
    else:
        dist[mj] = distAbsl[mj]
    
#    print '----------------FINAL----------------'
#    print 'Tree', tree
#    print 'Dist', dist
    
    return tree, dist

def computePhylogeneticTree(distMatrix, method):
    if method == neighbourJoining:
        return neighbourJoining(distMatrix)
    return computePhylTree(distMatrix, method)

def longestPath(tree, dist, current):
    new = argwhere(tree == current)
    if new.size == 0:
        return current, int(math.ceil(dist[current]))
    else:
        nodeL, pathDistL = longestPath(tree, dist, new[0])
        nodeR, pathDistR = longestPath(tree, dist, new[1])
        if pathDistL < pathDistR:
            if current >= 0:
                return nodeR, int(math.ceil(dist[current]) + 1 + pathDistR)
            else:
                return nodeR, 1 + pathDistR
        else:
            if current >=0:
                return nodeL, int(math.ceil(dist[current]) + 1 + pathDistL)
            else:
                return nodeL, 1 + pathDistL

def buildPathsForward(tree, dist, current, strList, line, col):
    endCol = col
    if current >= 0:
        endCol += int(math.ceil(dist[current]))
        for i in range(col, endCol):
            strList[line][i] = '-'
    
    new = argwhere(tree == current)
    if new.size == 0:
        strList[line][endCol] += str(current)
        return line + 2
    
    newLine = buildPathsForward(tree, dist, new[0], strList, line, endCol+1)
    
    for i in range(line, newLine+1):
        strList[i][endCol] = '|'
    
    return buildPathsForward(tree, dist, new[1], strList, newLine, endCol+1)

def showTree(tree, dist, N):
    node, length = longestPath(tree, dist, -1)
    
    strList = [[' '] * (length+1) for i in range(2*N-1)]
    strList[0][-1] = ' ' + str(node)
    
    newNode = int(node)
    lastIdx = length
    line = 2
    while newNode >= 0:
        beginIdx = lastIdx - int(math.ceil(dist[newNode])) 
        
        for i in range(beginIdx, lastIdx):
            strList[0][i] = '-'
        strList[0][beginIdx-1] = '|'
        
        sibling = argwhere(tree == tree[newNode])
        sibling = sibling[sibling!=newNode]
        
        for i in range(line+1):
            strList[i][beginIdx-1] = '|'
        
        line = buildPathsForward(tree, dist, sibling, strList, line, beginIdx)
        
        lastIdx = beginIdx - 1
        newNode = int(tree[newNode])
    
    for idx in range(2*N-1):
        print '#' + ''.join(strList[idx])
        
def showTreeRevised(tree, dist, N):
    node, length = longestPath(tree, dist, -1)
    strList = [[' '] * (length+1) for i in range(2*N-1)]
    
    buildPathsForward(tree, dist, -1, strList, 0, 0)
    
    for idx in range(2*N-1):
        print '#' + ''.join(strList[idx])

#TODO: add tree visualization procedure using matplotlib 

if __name__ == '__main__': pass
##TODO: redo test code
#    data = loadtxt('<TODO>.txt', dtype = 'int')
#    
#    print data
#    
#    simMatrix = similarityMatrix(data)
#    print simMatrix
#    
#    print distanceMatrix(simMatrix)
#    distMatrix = array([[ 0, 7, 11, 14],
#                        [ 7, 0,  6,  9],
#                        [11, 6,  0,  7],
#                        [14, 9,  7,  0]])
#    tree, dist = neighbourJoining(distMatrix)
#
#    distMatrix = array([[  0, 19, 27,  8, 33, 18, 13],
#                        [ 19,  0, 31, 18, 36,  1, 13],
#                        [ 27, 31,  0, 26, 41, 32, 29],
#                        [  8, 18, 26,  0, 31, 17, 14],
#                        [ 33, 36, 41, 31,  0, 35, 28],
#                        [ 18,  1, 32, 17, 35,  0, 12],
#                        [ 13, 13, 29, 14, 28, 12,  0]])
#    tree, dist = computePhylTree(distMatrix, upgma)
#    
#    showTree(tree, dist, distMatrix.shape[0])
#    showTree(array([5, 7, 6, 5, 6, 7, -1, -1]),\
#             array([5, 6, 3, 2, 4, 2,  3,  1]), 5)
#    
#    print
#    
#    showTreeRevised(array([5, 7, 6, 5, 6, 7, -1, -1]),\
#             array([5, 6, 3, 2, 4, 2,  3,  1]), 5)