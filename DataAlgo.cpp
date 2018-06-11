#include <iostream>
#include <math.h>
#include <vector>

using namespace std;

int main()
{

	FILE *in = fopen("output/temp.txt", "r");
	FILE *out = fopen("output/data.txt" , "a");

	vector<float> data;
	float temp;

	do
	{
		fscanf(in, "%f", &temp);
		data.push_back(temp);
		
		//Put in hashtable accordingly
		

	}
	while(!feof(in));

	//More algo to write to out file

	int n = data.size();
	int count=0;
	float mean=0, lim=0;

	for(int i=0;i<n;i++)
		mean+=data[i];

	mean = mean/n;

	for(int i=0;i<n;i++)
		lim += (data[i]-mean)*(data[i]-mean);

	lim = sqrt(lim);

	temp=0;	
	for(int i=0;i<n;i++)
		if(data[i]<mean+lim && data[i]>mean-lim)
		{
			temp+=data[i];
			count++;
		}

	cout<<endl<<temp/count<<endl;
	fprintf(out, "%6.3f\n", temp/count);

	return 0;

}