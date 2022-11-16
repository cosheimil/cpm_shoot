# import cv2 as cv
import numpy as np

x_0, y_0 = 300, 300

def sorting(data):
    dist = []
    for i in data:
        dist.append(((i[0] - x_0) ** 2 + (i[1] - y_0) ** 2) ** 0.5)
    hard_str = []
    for i in range(5):
        hard_str.append((data[i], dist[i]))
    hard_str.sort(key=lambda x: x[1])
    ans = []
    for i in hard_str:
        ans.append(i)
    return ans

def main():
    x = np.zeros(5)
    y = np.zeros(5)

    print('Введите координаты:\n')

    for _ in range(5):
        _x, _y = map(int, input().split())
        x[_], y[_] = _x, _y

    h = int(input('Расстояние до доски'))

    coord = [(x[i], y[i]) for i in range(5)]
    coord = sorting(coord)
    ans = []
    for _ in range(5):
        ans.append((np.arctan(x[_]/h), np.arctan(y[_]/h)))
    print(ans)

if __name__ == '__main__':
    main()