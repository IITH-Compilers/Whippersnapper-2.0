import csv 
import numpy as np

#array_in = np.genfromtxt('test_in.csv',delimiter='\n', dtype=str, skip_header=1)
#array_out = np.genfromtxt('test_out.csv',delimiter='\n', dtype=str, skip_header=1)

file_in = open('test_in.csv', "rU")
file_out = open('test_out.csv', "rU")

reader_in = csv.reader(file_in, delimiter="\n")
reader_out = csv.reader(file_out, delimiter="\n")

n=0
array_in = []
array_out = []

for row in reader_in :
        array_in.append(row[0])
        n += 1
for row in reader_out :
        array_out.append(row[0])

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
	sum = sum + float(array_out[i]) - float(array_in[i])
	i += 1

print sum/i
