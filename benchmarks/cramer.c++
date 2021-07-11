#include <time.h>
#include <vector>
#include <iostream>
#include <math.h>

float det(std::vector<std::vector<float>>& a);
float cofactor(std::vector<std::vector<float>>& a,int i);

void copy_matrix(std::vector<std::vector<float>>& a,std::vector<std::vector<float>>& m)
{
    for(int i = 0;i < a.size();i++)
    {
        std::vector<float> list;
        for(int j = 0;j < a[0].size();j++)
            list.push_back(a[i][j]);
        m.push_back(list);
    }
}

float cofactor(std::vector<std::vector<float>>& a,int i)
{
    std::vector<std::vector<float>> m;
    copy_matrix(a,m);
    m.erase(m.begin() + 0);
    for(unsigned int j = 0;j < m.size();j++)
        m[j].erase(m[j].begin() + i);
    return powf(-1,i) * det(m);
}


float det(std::vector<std::vector<float>>& a)
{
    if(a.size() == 2)
        return a[0][0] * a[1][1] - a[0][1] * a[1][0];
    else
    {
        float result = 0;
        for(unsigned int i = 0; i < a.size();i++)
            result += a[0][i] * cofactor(a,i);
        return result;
    }
}

int main()
{
    std::vector<std::vector<float>> matrix = {{0, 5, 4, 8, 6, 10, 69, 301, 24},
          {5, 6, 19, 1, 75, 47, 456, 85, 65},
          {37, 1, 11, 83, 5, 7, 78, 3, 36},
          {5, 9, 87, 52, 41, 9, 56, 6, 87},
          {97, 53, 1, 65, 3, 103, 82, 78, 3},
          {45, 13, 2, 25, 5, 789, 19, 98, 189},
          {23, 58, 76, 91, 46, 2, 356, 62, 963},
          {58, 6, 358, 45, 42, 598, 7, 8, 12},
          {350, 20, 60, 40, 90, 70, 110, 13, 78}};

    std::vector<float> vector({4, 86, 32, 56, 89, 2, 103, 28, 110});

    float determinant = det(matrix);

    std::vector<float> x_i;

    for(unsigned int i = 0;i < matrix.size();i++)
    {
        std::vector<std::vector<float>> matrix_i;
        copy_matrix(matrix,matrix_i);
        for(unsigned int j = 0;j < matrix.size();j++)
        {
            matrix_i[i][j] = vector[j];
        }
        x_i.push_back(det(matrix_i) / determinant);
    }


    return 0;
}