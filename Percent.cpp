#include <iostream>
#include <vector>

using namespace std;
#define loop(a,b) for(int i=a;i<=b;i++)

int main(int argc, char **argv)
{
	char *out_file;

	if(argc>0) out_file = argv[1];

	FILE *in = fopen("output/data.txt", "r");
	FILE *out = fopen(out_file , "w");

	vector<float> arr;
	float temp;
	float base;

	fscanf(in, "%f", &base);

	do
	{
		fscanf(in, "%f", &temp);
		arr.push_back(temp);		

	}
	while(!feof(in));

	//More algo to write to out file

	int n = arr.size();
	fprintf(out, "0\n");
	loop(0,n-2) { arr[i]=((arr[i]-base)*100)/base; }
	loop(0,n-2) { fprintf(out, "%f\n", arr[i]); }

	return 0;
}