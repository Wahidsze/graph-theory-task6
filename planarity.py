import math
import sys


def read_graph(filename):
    graph = {}
    for line in open(filename, encoding="utf-8"):
        line = line.strip()
        if line == "":
            continue
        u, v = line.split()
        graph.setdefault(u, set()).add(v)
        graph.setdefault(v, set()).add(u)
    return graph


def edge(u, v):
    return (min(u, v), max(u, v))


def is_connected(graph, removed=None):
    vertices = [v for v in graph if v != removed]
    seen = {vertices[0]}
    stack = [vertices[0]]
    while stack:
        v = stack.pop()
        for u in graph[v]:
            if u != removed and u not in seen:
                seen.add(u)
                stack.append(u)
    return len(seen) == len(vertices)


def is_biconnected(graph):
    if len(graph) < 3 or not is_connected(graph):
        return False
    return all(is_connected(graph, v) for v in graph)


def find_cycle(graph):
    parent = {}

    def dfs(v, p):
        parent[v] = p
        for u in sorted(graph[v]):
            if u == p:
                continue
            if u in parent:
                cycle = [v]
                while cycle[-1] != u:
                    cycle.append(parent[cycle[-1]])
                return cycle
            found = dfs(u, v)
            if found:
                return found
        return None

    return dfs(min(graph), None)


def find_segments(graph, placed, placed_edges):
    segments = []
    for u in sorted(graph):
        for v in sorted(graph[u]):
            if u < v and u in placed and v in placed and edge(u, v) not in placed_edges:
                segments.append(({u, v}, set()))
    seen = set()
    for start in sorted(graph):
        if start in placed or start in seen:
            continue
        comp = {start}
        stack = [start]
        while stack:
            v = stack.pop()
            for u in graph[v]:
                if u not in placed and u not in comp:
                    comp.add(u)
                    stack.append(u)
        seen |= comp
        contacts = {u for v in comp for u in graph[v] if u in placed}
        segments.append((contacts, comp))
    return segments


def find_path(graph, contacts, comp):
    if not comp:
        return sorted(contacts)
    a = min(contacts)
    parent = {a: None}
    queue = [a]
    for v in queue:
        for u in sorted(graph[v]):
            if u in parent:
                continue
            if u in comp:
                parent[u] = v
                queue.append(u)
            elif u in contacts and v != a:
                path = [u, v]
                while path[-1] != a:
                    path.append(parent[path[-1]])
                return path


def split_face(face, path):
    a, b = path[0], path[-1]
    inner = path[1:-1]
    i, j = face.index(a), face.index(b)
    if i < j:
        part1 = face[i:j + 1]
        part2 = face[j:] + face[:i + 1]
    else:
        part1 = face[i:] + face[:j + 1]
        part2 = face[j:i + 1]
    return [part1 + inner[::-1], part2 + inner]


def demoucron(graph):
    cycle = find_cycle(graph)
    faces = [cycle, cycle[:]]
    placed = set(cycle)
    placed_edges = {edge(cycle[i - 1], cycle[i]) for i in range(len(cycle))}
    m = sum(len(graph[v]) for v in graph) // 2

    while len(placed_edges) < m:
        best = None
        for contacts, comp in find_segments(graph, placed, placed_edges):
            good = [f for f in faces if contacts <= set(f)]
            if not good:
                return None
            if best is None or len(good) < len(best[2]):
                best = (contacts, comp, good)
        contacts, comp, good = best
        path = find_path(graph, contacts, comp)
        faces.remove(good[0])
        faces.extend(split_face(good[0], path))
        placed.update(path)
        placed_edges.update(edge(path[i], path[i + 1]) for i in range(len(path) - 1))
    return faces


def tutte_layout(graph, outer, radius=4):
    pos = {}
    for i, v in enumerate(outer):
        angle = math.pi / 2 + 2 * math.pi * i / len(outer)
        pos[v] = (radius * math.cos(angle), radius * math.sin(angle))
    inner = [v for v in graph if v not in pos]
    for v in inner:
        pos[v] = (0.0, 0.0)
    for _ in range(100000):
        shift = 0.0
        for v in inner:
            x = sum(pos[u][0] for u in graph[v]) / len(graph[v])
            y = sum(pos[u][1] for u in graph[v]) / len(graph[v])
            shift = max(shift, abs(x - pos[v][0]) + abs(y - pos[v][1]))
            pos[v] = (x, y)
        if shift < 1e-12:
            break
    return pos


def num(x):
    return "%g" % (round(x, 3) + 0.0)


def to_dot(graph, pos):
    lines = ["graph G {", "  layout=neato;", "  node [shape=circle];"]
    for v in sorted(graph):
        lines.append('  "%s" [pos="%s,%s!"];' % (v, num(pos[v][0]), num(pos[v][1])))
    for u in sorted(graph):
        for v in sorted(graph[u]):
            if u < v:
                lines.append('  "%s" -- "%s";' % (u, v))
    lines.append("}")
    return "\n".join(lines)


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "planar.txt"
    graph = read_graph(filename)

    if not is_biconnected(graph):
        print("Граф не двусвязный, алгоритм Демукрона к нему не применяется")
        sys.exit()

    faces = demoucron(graph)
    if faces is None:
        print("Граф не планарен")
        sys.exit()

    print("Граф планарен")
    print("Грани (%d):" % len(faces))
    for face in faces:
        print("  " + " ".join(face))

    pos = tutte_layout(graph, max(faces, key=len))
    print("Координаты вершин:")
    for v in sorted(graph):
        print("  %s: (%s, %s)" % (v, num(pos[v][0]), num(pos[v][1])))

    dot_name = filename.rsplit(".", 1)[0] + ".dot"
    open(dot_name, "w", encoding="utf-8").write(to_dot(graph, pos))
