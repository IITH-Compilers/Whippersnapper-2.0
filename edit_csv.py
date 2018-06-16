import csv 
import numpy as np

array_in = np.genfromtxt('test_in.csv',delimiter='\n', dtype=str, skip_header=1)
array_out = np.genfromtxt('test_out.csv',delimiter='\n', dtype=str, skip_header=1)

i = 0
while i < len(array_in) :
	array_in[i] = array_in[i][11:-1]
	array_in[i] = float(array_in[i])
	i += 1

i = 0
while i < len(array_out) :
	array_out[i] = array_out[i][11:-1]
	array_out[i] = float(array_out[i])	
	i += 1

i = 0
sum = 0
while i < len(array_out) :
	sum = sum*(i/(i+1)) + float(array_out[i])/(i+1) - float(array_in[i])/(i+1)
	i += 1

print sum
