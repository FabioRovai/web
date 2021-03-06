# -*- coding: utf-8 -*-

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
from __future__ import generators
import itertools
import IPython
import IPython.display as ipd
import matplotlib.pyplot as plt
import numpy as np
import os 
import pandas as pd
import random
import re
import requests 
import seaborn as sns
import shutil 
import soundfile as sf
import sys
import warnings
import zipfile

from contextlib import suppress

from IPython.display import clear_output 
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial import ConvexHull
from scipy.io import wavfile

warnings.filterwarnings("ignore")

pdb=pd.read_csv ('PDB.txt', delim_whitespace=True, header=0).sort_values(by=['resolution'])

full_protein_ID_foo ="1QOWB"#@param {type:"string"} 

import argparse
parser = argparse.ArgumentParser(description='insert protein.') 
parser.add_argument('-full_protein_ID_foo', help='protein name', default='1QOWB') 
args = parser.parse_args()

full_protein_ID=re.sub(r"\t", '',args.full_protein_ID_foo) 
full_protein_ID=re.sub(r" ", '',full_protein_ID) 
 
protein_ID = pdb.IDs.loc[pdb.iloc[:,0].str.contains(full_protein_ID)].iloc[0][:-1]

data = requests.get('https://files.rcsb.org/download/{}.pdb'.format(protein_ID.lower())).text


text = data.split("\n") 

ca_coordinates = []

for line in text:
  
  if 'ATOM' == line[0:4] or 'HETATOM' == line[0:7]:
    # Matches lines with c-alpha coordinates, altLoc A or ' ', and chain A
    # If using the dunbrack list the final == statement should be line[21] == protein_ID[4] (the fifth character)
    if line[13:15] == 'CA' and line[16] in ['A',' '] and line[21] == 'A': 
      # Extract x, y, and z coordinates and 
      # add to coordinates list
      x = float(line[30:38])      
      y = float(line[38:46])     
      z = float(line[46:54])
      ca_coordinates.append([x,y,z])

# Save coordinates as array
ca_coordinates = np.asarray(ca_coordinates)


#@title Calculate Convex hull
# convex hull (Graham scan by x-coordinate) and diameter of a set of points
# David Eppstein, UC Irvine, 7 Mar 2002
def orientation(p,q,r):
    '''Return positive if p-q-r are clockwise, neg if ccw, zero if colinear.'''
    return (q[1]-p[1])*(r[0]-p[0]) - (q[0]-p[0])*(r[1]-p[1])
def hulls(Points):
    '''Graham scan to find upper and lower convex hulls of a set of 2d points.'''
    U = []
    L = []
    #Points.sort()
    for p in Points:
        while len(U) > 1 and orientation(U[-2],U[-1],p) <= 0: U.pop()
        while len(L) > 1 and orientation(L[-2],L[-1],p) >= 0: L.pop()
        U.append(p)
        L.append(p)
    return U,L

def rotatingCalipers(Points):
    '''Given a list of 2d points, finds all ways of sandwiching the points
between two parallel lines that touch one point each, and yields the sequence
of pairs of points touched by each pair of lines.'''
    U,L = hulls(Points)


    i = 0
    j = len(L) - 1
    while i < len(U) - 1 or j > 0:
        yield U[i],L[j]
        # if all the way through one side of hull, advance the other side
        if i == len(U) - 1: j -= 1
        elif j == 0: i += 1
        # still points left on both lists, compare slopes of next hull edges
        # being careful to avoid divide-by-zero in slope calculation
        elif (U[i+1][1]-U[i][1])*(L[j][0]-L[j-1][0]) > \
                (L[j][1]-L[j-1][1])*(U[i+1][0]-U[i][0]):
            i += 1
        else: j -= 1
def diameter(Points):
    '''Given a list of 2d points, returns the pair that's farthest apart.'''
    diam,pair = max([((p[0]-q[0])**2 + (p[1]-q[1])**2, (p,q))
                     for p,q in rotatingCalipers(Points)])
  

    return pair

# 8 points defining the cube corners    
pts = ca_coordinates
hull = ConvexHull(pts)
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")




# Plot defining corner points
ax.plot(pts.T[0], pts.T[1], pts.T[2], "ko")

# 12 = 2 * 6 faces are the simplices (2 simplices per square face)
for s in hull.simplices:
    s = np.append(s, s[0])  # Here we cycle back to the first coordinate
    ax.plot(pts[s, 0], pts[s, 1], pts[s, 2], "r-")

# Make axis label
for i in ["x", "y", "z"]:
    eval("ax.set_{:s}label('{:s}')".format(i, i))
foo=hull.simplices.tolist()
foo=pts[s]
baz = list(itertools.chain(*foo))

plt.show()

#@title Calculate Max Width or farthest distance from the center (experimental)



def incremental_farthest_search(points, k):
  with suppress(IndexError):
    remaining_points = points[:]
    solution_set = []
    mean=int(np.mean(baz))
    
    solution_set.append(remaining_points.pop(\
                                             (mean - 0)))
    
    for _ in range(k-1):
        distances = [distance(p, solution_set[0]) for p in remaining_points]
        for i, p in enumerate(remaining_points):
            for j, s in enumerate(solution_set):
                distances[i] = min(distances[i], distance(p, s))
        solution_set.append(remaining_points.pop(distances.index(max(distances))))
    return solution_set
def distance(A, B):
    return abs(A - B)

max_width=0

try:
    bar=incremental_farthest_search(baz,2)
    max_width = np.linalg.norm(bar[0] - bar[1])
except TypeError:
  print('max width cannot be calculates, 0 value assigned')
else:
  print()

#@title  Calculate Volume of Convex Hull, Farthest Distance using Rotating Calipers and Centroid and Calculate number of positive and negative points on each axis. 

# Calculate Volume of Convex Hull and Centroid
hull_volume=ConvexHull(ca_coordinates).volume


# Calculate Max Distance using rotating caliper
max_points = list(diameter(ca_coordinates))
max_distance = np.linalg.norm(max_points[0] - max_points[1])
centroid = np.sum(ca_coordinates,axis=0)/len(ca_coordinates)


# Translate structure to be centered on centroid
closest_dist = np.linalg.norm(ca_coordinates[0]-centroid)
closest_point = 0
for i in range(len(ca_coordinates)):
  p = ca_coordinates[i]
  if np.linalg.norm(p-centroid) < closest_dist:
    closest_dist = np.linalg.norm(p-centroid)
    closest_point = i
translated_ca_coors = []
for i in range(len(ca_coordinates)):
  p = ca_coordinates[i]
  translated_ca_coors.append(p-ca_coordinates[closest_point])
translated_ca_coors = np.asarray(translated_ca_coors)

# Calculate number of positive and negative points on each axis 
pos_neg_xyz = [0,0,0,0,0,0]
for i in range(len(translated_ca_coors)):
  p = translated_ca_coors[i]
  if p[0] > 0:
    pos_neg_xyz[0]+=1
  else:
    pos_neg_xyz[1]+=1
  if p[1] > 0:
    pos_neg_xyz[2]+=1
  else:
    pos_neg_xyz[3]+=1
  if p[1] > 0:
    pos_neg_xyz[4]+=1
  else:
    pos_neg_xyz[5]+=1


'''#Plot
fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.scatter(ca_coordinates[:,0],ca_coordinates[:,1],ca_coordinates[:,2],label='Original Coordinates')
ax.scatter(translated_ca_coors[:,0],translated_ca_coors[:,1],translated_ca_coors[:,2],label='Translated Coordinates')
plt.legend()
plt.show()'''

#@title  Add characteristics to a Combinational Wave
samplerate = 44100

# Volume wave
hull_volume_freq = hull_volume/1000 # scaling down a bit
t = np.linspace(0., 10., samplerate)/(len(ca_coordinates)/100)
amplitude = np.iinfo(np.int16).max
volume_signal = amplitude * np.sin(2. * np.pi * hull_volume_freq * t)

# Waveshaping against hull_volume_freq 

# Pos X wave
pos_x = amplitude * np.sin(2. * np.pi * (hull_volume_freq+pos_neg_xyz[0]) * t)
# Neg X wave
neg_x = amplitude * np.sin(2. * np.pi * (hull_volume_freq+pos_neg_xyz[1]) * t)
# Pos Y wave
pos_y = amplitude * np.sin(2. * np.pi * (hull_volume_freq+pos_neg_xyz[2]) * t)
# Neg X wave
neg_y = amplitude * np.sin(2. * np.pi * (hull_volume_freq+pos_neg_xyz[3]) * t)
# Pos Z wave
pos_z = amplitude * np.sin(2. * np.pi * (hull_volume_freq+pos_neg_xyz[4]) * t)
# Neg Z wave
neg_z = amplitude * np.sin(2. * np.pi * (hull_volume_freq+pos_neg_xyz[5]) * t)

# Waveshaping against max_distance

# Pos X wave
pos_ax = amplitude * np.sin(2. * np.pi * (max_distance+pos_neg_xyz[0]) * t)
# Neg X wave
neg_ax = amplitude * np.sin(2. * np.pi * (max_distance+pos_neg_xyz[1]) * t)
# Pos Y wave
pos_ay = amplitude * np.sin(2. * np.pi * (max_distance+pos_neg_xyz[2]) * t)
# Neg X wave
neg_ay = amplitude * np.sin(2. * np.pi * (max_distance+pos_neg_xyz[3]) * t)
# Pos Z wave
pos_az = amplitude * np.sin(2. * np.pi * (max_distance+pos_neg_xyz[4]) * t)
# Neg Z wave
neg_az = amplitude * np.sin(2. * np.pi * (max_distance+pos_neg_xyz[5]) * t)

# Waveshaping against max_width (if experimental part works)
if 'solution_set' in globals():
  pos_axa = amplitude * np.sin(2. * np.pi * (max_width+pos_neg_xyz[0]) * t)
  neg_axa = amplitude * np.sin(2. * np.pi * (max_width+pos_neg_xyz[1]) * t)
  pos_aya = amplitude * np.sin(2. * np.pi * (max_width+pos_neg_xyz[2]) * t)
  neg_aya = amplitude * np.sin(2. * np.pi * (max_width+pos_neg_xyz[3]) * t)
  pos_aza = amplitude * np.sin(2. * np.pi * (max_width+pos_neg_xyz[4]) * t)
  neg_aza = amplitude * np.sin(2. * np.pi * (max_width+pos_neg_xyz[5]) * t)
else:
  pos_axa = 0
  neg_axa = 0
  pos_aya = 0
  neg_aya = 0
  pos_aza = 0
  neg_aza = 0



# Combination wave
data = volume_signal + pos_x + neg_x + pos_y + neg_y + pos_z + neg_z + pos_ax + neg_ax + pos_ay + neg_ay + pos_az + neg_az + pos_axa + neg_axa + pos_aya + neg_aya + pos_aza + neg_aza 

# Plot
n = 200

'''
plt.plot(volume_signal[0:n],label='hull volume',linewidth=0.5)
plt.plot(pos_x[0:n],label='pos x(hull_volume_freq)',linewidth=0.5)
plt.plot(neg_x[0:n],label='neg x(hull_volume_freq)',linewidth=0.5)
plt.plot(pos_y[0:n],label='pos y(hull_volume_freq)',linewidth=0.5)
plt.plot(neg_y[0:n],label='neg y(hull_volume_freq)',linewidth=0.5)
plt.plot(pos_z[0:n],label='pos z(hull_volume_freq)',linewidth=0.5)
plt.plot(neg_z[0:n],label='neg z(hull_volume_freq)',linewidth=0.5)

plt.plot(pos_ax[0:n],label='pos x(max_distance)',linewidth=0.5)
plt.plot(neg_ax[0:n],label='neg x(max_distance)',linewidth=0.5)
plt.plot(pos_ay[0:n],label='pos y(max_distance)',linewidth=0.5)
plt.plot(neg_ay[0:n],label='neg y(max_distance)',linewidth=0.5)
plt.plot(pos_az[0:n],label='pos z(max_distance)',linewidth=0.5)
plt.plot(neg_az[0:n],label='neg z(max_distance)',linewidth=0.5)

if 'solution_set' in globals():
  plt.plot(pos_axa[0:n],label='pos x(max_width)',linewidth=0.5)
  plt.plot(neg_axa[0:n],label='neg x(max_width)',linewidth=0.5)
  plt.plot(pos_aya[0:n],label='pos y(max_width)',linewidth=0.5)
  plt.plot(neg_aya[0:n],label='neg y(max_width)',linewidth=0.5)
  plt.plot(pos_aza[0:n],label='pos z(max_width)',linewidth=0.5)
  plt.plot(neg_aza[0:n],label='neg z(max_width)',linewidth=0.5)
else: 
  pass

plt.plot(data[0:n],label='comb wave',linewidth=2)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.show()'''

#@title  Rescale, store and retrive

# Rescale data because adding waves increases the amplitude beyond the limit
data += -(np.min(data))
data /= np.max(data) / (np.iinfo(np.int16).max - np.iinfo(np.int16).min)
data += np.iinfo(np.int16).min
wavfile.write('test_wave.wav', 44100, data.astype(np.int16))

# Store and retrive signal
bigData=pd.DataFrame(data,columns=[protein_ID]) #protein_ID
retrive=bigData.iloc[:,0].to_numpy()
wavfile.write('retrive.wav', 44100, data.astype(np.int16))
IPython.display.Audio("test_wave.wav")

#IPython.display.Audio('retrive.wav')

#@title Generating Datasets for protein quality retrival 
b=bigData.values.tolist()
pdb=pdb.T
pdb.rename(columns=pdb.iloc[0], inplace = True)

pdb.at[0, str(full_protein_ID)] = b
pdb.at[1, str(full_protein_ID)] = hull_volume_freq
pdb.at[2, str(full_protein_ID)] = max_distance
pdb.at[4, str(full_protein_ID)] = max_width

pdb=pdb.T
pdb=pdb.reset_index(drop=True)
pdb.rename(columns={ pdb.columns[6]: "sounds",pdb.columns[7]: "volume",pdb.columns[8]: "max_distance",pdb.columns[9]: "max_width" }, inplace = True)
pdb.replace(0, np.nan, inplace=True)

#print ()
displayPdb=pdb.set_index('IDs')

