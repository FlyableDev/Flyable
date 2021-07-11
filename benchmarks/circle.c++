#include <vector>
#include <iostream>
#include <math.h>

class CirclePoint
{
    public:
    float x;
    float y;

    CirclePoint(float x,float y)
    {
        this->x = x;
        this->y = y;
    }
};


int main()
{
    std::vector<CirclePoint>results;
    float radius = 12.3f;
    int points = 5000000;
    float angle_by_points = (3.1415f * 2.f) / points;
    for(int e = 0;e < points;e++)
    {
        float x = (float) cos(angle_by_points * e) * radius;
        float y = (float) sin(angle_by_points * e) * radius;
        results.push_back(CirclePoint(x,y));
    }
}