#include <iostream>
#include <math.h>
#include <vector>

using namespace std;

int main()
{
	float temp;
	int n;

	cin>>n;

	float data[n];

	for(int i=0;i<n;i++)
		cin>>data[i];


	//More algo to write to out file
	int count=0;
	float mean=0, lim=0;

	for(int i=0;i<n;i++)
		mean+=data[i];

	for(int i=0;i<n;i++)
		cout<<data[i]<<endl;

	mean = mean/n;
	cout<<endl;

	for(int i=0;i<n;i++)
		lim += (data[i]-mean)*(data[i]-mean);

	lim = sqrt(lim);

	cout<<mean-lim<<" "<<mean+lim<<endl;
	cout<<endl;
	

	temp=0;	
	for(int i=0;i<n;i++)
		if(data[i]<mean+lim && data[i]>mean-lim)
		{	cout<<data[i]<<endl;
			temp+=data[i];
			count++;
		}

	cout<<endl<<temp/count<<endl;

	return 0;

}