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

while i < n :
        array_in[i] = array_in[i][9:19]
        array_in[i] = float(array_in[i])
        i += 1

i = 0
while i < n :
        array_out[i] = array_out[i][9:19]
        array_out[i] = float(array_out[i])
        i += 1

i = 0
sum = 0
count0=0
count1=0
count2=0
count3=0
count4=0
count5=0
arr = []
mark = []
while i < n :
        arr.append(array_out[i] - array_in[i])
        if arr[i]>1 :
                count0 += 1
                mark.append(0)
        elif (arr[i]*10)>1 :
                count1 += 1
                mark.append(1)
        elif (arr[i]*100)>1 :
                mark.append(2)
                count2 += 1
        elif (arr[i]*1000)>1 :
                mark.append(3)
                count3 += 1
        elif (arr[i]*10000)>1 :
                mark.append(4)
                count4 += 1
        else :
                mark.append(5)
                count5 += 1
        i += 1
i=0
# print count0
# print count1
# print count2
# print count3
# print count4
# print count5
if count2==max(count2,count3,count4) :
        while i<n :
                if(mark[i]==2) :
                        sum += arr[i]
                i += 1
        print sum/count2
elif count3 ==max(count2,count3,count4) :
        while i<n :
                if(mark[i]==3) :
                        sum += arr[i]
                i += 1
        print sum/count3
elif count4 ==max(count2,count3,count4) :
        while i<n :
                if(mark[i]==4) :
                        sum += arr[i]
                i += 1
        print sum/count4

