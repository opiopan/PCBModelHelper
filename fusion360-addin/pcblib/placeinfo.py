import os

def load(path):
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        line = f.readline()
        while line:
            tokens = line.strip().split()
            if len(tokens) == 6:
                name, x, y, rot, mirror, fpname = tuple(tokens)
                entry = (float(x), float(y), float(rot), mirror == '0', name)
                if fpname in data:
                    data[fpname].append(entry)
                else:
                    data[fpname] = [entry]
            line = f.readline()
    return data
