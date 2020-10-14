'''
    PyElph - Background substraction procedures 
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


from numpy import append, array, greater, mean, ones, zeros


def middleOfGapBackgroundLevels(data, lanes):
    backg = [lanes[0][0]/2]
    for i in range(len(lanes)-1):
        backg.append((lanes[i][1] + lanes[i+1][0])/2)
    backg.append((lanes[-1][1]+data.shape[1])/2)
    
    backgLevels = array(data[:, backg[:-1]]/2, dtype='uint32')
    backgLevels += data[:, backg[1:]]/2
    return backgLevels

def meanGapBackgroundLevels(data, lanes):
    backg = array([[0, lanes[0][0]]])
    for i in range(len(lanes)-1):
        backg = append(backg, array([[lanes[i][1], lanes[i+1][0]]]), 0)
    backg = append(backg, array([[lanes[-1][1], data.shape[1]]]), 0)
    
    backgLevels = zeros([data.shape[0], len(lanes)], dtype='uint32')
    for i in range(len(lanes)):
        if backg[i, 0] < backg[i, 1]:
            backgLevels[:, i] += mean(data[:, backg[i, 0]:backg[i, 1]], 1)/2
        if backg[i+1, 0] < backg[i+1, 1]:
            backgLevels[:, i] += mean(data[:, backg[i+1, 0]:backg[i+1, 1]], 1)/2
    return backgLevels

def backgroundSubstraction(data, lanes,
                           getBackGroundLevels = meanGapBackgroundLevels):
    backgLevels = getBackGroundLevels(data, lanes)
    
    idx = 0
    back = zeros(data.shape, dtype='uint8')
    for idxBegin, idxEnd in lanes:
        blockData = backgLevels[:, [idx]] * ones([1, idxEnd - idxBegin])
        back[:, idxBegin:idxEnd] = (data[:, idxBegin:idxEnd] - blockData)\
                                * greater(data[:, idxBegin:idxEnd], blockData)
    
    return back
