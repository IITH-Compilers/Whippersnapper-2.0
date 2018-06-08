#include <iostream>

using namespace std;
#define loop(a,b) for(int i=a;i<=b;i++)

int main()
{
	int n;
	float base;

	cout<<"Enter the base latency value you would like to compare to: ";
	cin>>base;

	cout<<"Enter the size of list: ";
	cin>>n;

	float arr[n];

	loop(0,n-1) { cin>>arr[i]; }
	loop(0,n-1) { arr[i]=((arr[i]-base)*100)/base; }
	loop(0,n-1) { cout<<arr[i]<<endl; }

	return 0;
}