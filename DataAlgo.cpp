#include <iostream>
#include <map>
#include <list>

using namespace std;

int main()
{

	FILE *in = fopen("output/temp.txt", "r");
	FILE *out = fopen("output/data.txt" , "a");

	vector<float> data;

	do
	{
		fscanf(in, "%-6.3f", temp);
		vector.push(temp);
		
		//Put in hashtable accordingly
		

	}
	while(!feof(in));

	//More algo to write to out file

	return 0;

}
























	return 0;
}
