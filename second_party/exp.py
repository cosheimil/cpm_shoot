x_0, y_0 = 300, 300


def sorting(data):
    dist = []
    for i in data:
        dist.append(((i[0] - x_0) ** 2 + (i[1] - y_0) ** 2) ** 0.5)
    hard_str = []
    for i in range(5):
        hard_str.append([data[i], dist[i]])
    hard_str.sort(lambda x: x[1])
    return hard_str


data = [(0, 0), (100, 200), (343, 757), (300, 200), (0, 200)]

print(sorting(data))
