import time


def copy_matrix(a):
    m = []
    for i in a:
        list = []
        for j in i:
            list.append(j)
        m.append(list)
    return m


def cofactor(a, i):
    m = copy_matrix(a)
    m.pop(0)
    for j in range(0, len(m)):
        m[j].pop(i)
    return pow(-1, i) * det(m)


def det(a):
    if len(a) == 0:
        return 0.0

    if len(a) == 2:
        return (a[0][0] * a[1][1]) - (a[0][1] * a[1][0])
    else:
        result = 0.0
        for i in range(0, len(a)):
            result += a[0][i] * cofactor(a, i)
        return result


def main():
    matrix = [[0.0, 5.0, 4.0, 8.0, 6.0, 10.0, 69.0, 301.0, 24.0],
              [5.0, 6.0, 19.0, 1.0, 75.0, 47.0, 456.0, 85.0, 65.0],
              [37.0, 1.0, 11.0, 83.0, 5.0, 7.0, 78.0, 3.0, 36.0],
              [5.0, 9.0, 87.0, 52.0, 41.0, 9.0, 56.0, 6.0, 87.0],
              [97.0, 53.0, 1.0, 65.0, 3.0, 103.0, 82.0, 78.0, 3.0],
              [45.0, 13.0, 2.0, 25.0, 5.0, 789.0, 19.0, 98.0, 189.0],
              [23.0, 58.0, 76.0, 91.0, 46.0, 2.0, 356.0, 62.0, 963.0],
              [58.0, 6.0, 358.0, 45.0, 42.0, 598.0, 7.0, 8.0, 12.0],
              [350.0, 20.0, 60.0, 40.0, 90.0, 70.0, 110.0, 13.0, 78.0]]
    vector = [4.0, 86.0, 32.0, 56.0, 89.0, 2.0, 103.0, 28.0, 110.0]
    determinant = det(matrix)

    x_i = []

    for i in range(0, len(matrix)):
        matrix_i = copy_matrix(matrix)
        for j in range(0, len(matrix)):
            matrix_i[i][j] = vector[j]
        x_i.append(det(matrix_i) / determinant)

    print(x_i)