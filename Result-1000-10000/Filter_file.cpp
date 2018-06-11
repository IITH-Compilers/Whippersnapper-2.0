#include <iostream>
#include <math.h>
#include <vector>

using namespace std;

int main(int argc, char **argv)
{
	char *in_file = argv[1];
	char *out_file = argv[2];


	FILE *in = fopen(in_file, "r");
	FILE *out = fopen(out_file, "w");

	vector<float> data;
	float temp;
	char line[100];

	do
	{
		int i = 0;
		data.clear();
		while(fgets(line, sizeof line, in))
		{
	     	//cout<<line;   
	        if (line[0] == '\n') {
	        	i++;
	        }
	        if(i==2){
	        	break;
	        }

			// fscanf(in, "%f", &temp);
			data.push_back(atof(line));
		}

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
		//cout<<mean-lim<<" "<<mean+lim<<endl;

		temp=0;	
		for(int i=0;i<n;i++)
			if(data[i]<mean+lim && data[i]>mean-lim)
			{
				//cout<<data[i]<<endl;
				temp+=data[i];
				count++;
			}

		//cout<<endl<<temp/count<<endl;
		fprintf(out, "%6.3f\n", temp/count);

	}
	while(!feof(in));

	return 0;

}