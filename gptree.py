from collections import Counter
from queue import Queue
import time

class GPNode:
    __slots__ = {"item", "count", "parent", "children", "nodeLink"}
    def __init__(self, item, parent=None):
        self.item = item
        self.count = 0
        self.parent = parent
        self.children = {}
        self.nodeLink = None

    def addChild(self, item):
        child = GPNode(item, parent=self)
        self.children[item] = child
        return child

def getNbrCnt(hypergraph, node, g):
    cnt = {}
    for hyperedge in hypergraph.nodes[node]['hyperedges']:
        for neighbor in hyperedge:
            if neighbor != node:
                cnt[neighbor] = cnt.get(neighbor,0)+1
    ng = {node: count for node, count in cnt.items() if count >= g}
    return len(ng)

def buildGPList(hypergraph, k, g):
    H = set(hypergraph.nodes())
    gpList = {}
    for v in H:
        count = getNbrCnt(hypergraph, v, g)
        if count >= k:
            gpList[v] = count
    return sorted(gpList, key=lambda x: gpList[x], reverse=True)

def addEdge(root, headerTable, e, order, gpSet):
    filtered = [v for v in e if v in gpSet]
    key = order.__getitem__
    filtered.sort(key=key)
    if not filtered:
        return
    current = root
    for v in filtered:
        if v in current.children:
            # increment the count of existing child
            child = current.children[v]
            child.count += 1
        else:
            # Create a new child node
            child = current.addChild(v)
            child.count = 1
            if headerTable[v] is None:
                headerTable[v] = child
            else:
                # Maintain the nodeLink
                currentHead = headerTable[v]
                headerTable[v] = child
                child.nodeLink = currentHead
        current = child

def deleteEdge(root, e, order, gpSet):
    filtered = [v for v in e if v in gpSet]
    key = order.__getitem__
    filtered.sort(key=key)
    if not filtered:
        return
    current = root
    for v in filtered:
        if v in current.children:
            # increment the count of existing child
            child = current.children[v]
            child.count -= 1
            if child.count == 0:
                del current.children[v]
        else:
            # 아마 이럴 일 없음
            print('error?')
        current = child
    
def buildGPTree(hypergraph, hyperedges, k, g):
    gpList = buildGPList(hypergraph, k, g)
    headerTable = {i: None for i in gpList}
    root = GPNode(None)
    order = {v: i for i, v in enumerate(gpList)} # to speed-up edge filtering & sorting
    for e in hyperedges:
        addEdge(root, headerTable, e, order, order)

    return root, headerTable, gpList

def mergeSubtree(parentSubtree, orphanSubtree, headerTable):\
    # 추후에 headerTable 연결도 정리 필요
    for orphanItem, orphanChild in orphanSubtree.children.items():
        if orphanItem in parentSubtree.children:
            existing = parentSubtree.children[orphanItem]
            existing.count += orphanChild.count
            orphanChild.parent = None # 죽은 노드 처리
            mergeSubtree(existing, orphanChild, headerTable)
            orphanChild.children = {}
        else:
            parentSubtree.children[orphanItem] = orphanChild
            orphanChild.parent = parentSubtree

def removeNode(node, headerTable):
    node = headerTable[node]
    while node:
        parent = node.parent
        if parent and node.item in parent.children:
            mergeSubtree(parent, node, headerTable)
            del parent.children[node.item]
        elif parent:
            del parent.children[node.item]
        node = node.nodeLink

def ascendPath(node, count):
    current = node.parent
    while current and current.item is not None:
        if current.item not in count:
            count[current.item] = 0
        count[current.item] += node.count
        current = current.parent
    return count

def descendPath(node, count):
    stack = [node]
    while stack:
        node = stack.pop()
        for child in node.children.values():
            if child.item not in count:
                count[child.item] = 0
            count[child.item] += child.count
            stack.append(child)
    return count

def findGNbr(headerTable, node, g):
    # headerTable에서 node에 해당하는 첫 노드 가져오기
    v = headerTable[node]
    count = {}
    # nodeLink를 따라가며 모든 노드 방문
    while v is not None:
        # 각 노드에서 ascendPath를 통해 dictionary에 노드 + count 저장 (count는 모두 node의 count)
        ascendPath(v, count)
        # 각 노드에서 children 끝까지 탐색하여 dictionary에 노드 + count 저장 (count는 모두 child의 count)
        descendPath(v, count)
        v = v.nodeLink
    # dictionary에서 count가 g 이상인 노드들만 반환
    return [v for v, c in count.items() if c >= g]

def kgComputation(hypergraph, E, k, g):
    Q = Queue()
    R = set()
    S = {}
    root, headerTable, gpList = buildGPTree(hypergraph, E, k, g)

    for v in reversed(gpList):
        nbrs = findGNbr(headerTable, v, g)
        # if len(nbrs) < k:
        S[v] = len(nbrs)
        if S[v] < k:
            Q.put(v)
            R.add(v)
    while not Q.empty():
        v = Q.get()
        gpList.remove(v)
        nbrs = findGNbr(headerTable, v, g)
        removeNode(v, headerTable)
        for u in nbrs:
            if u in R:
                continue
            newNbrs = findGNbr(headerTable, u, g)
            # if len(newNbrs) < k:
            S[u] -= 1 # EPA 처럼 개수까지 저장해놓으면 시간 거의 안 걸림
            if S[u] < k:
                Q.put(u)
                R.add(u)
        if v in headerTable: # 체크 필요한가?
            del headerTable[v]
    return set(headerTable.keys()), gpList, root, headerTable, S

def insertEdge(hypergraph, gpList, root, headerTable, hyperedge, k, g, S):
    N = set()
    gpSet = set(gpList)
    for v in hyperedge:
        if v not in gpSet:
            gpList.append(v)
            N.add(v)
    order = {v: i for i, v in enumerate(gpList)}
    # hyperedge 안 넣은 듯
    for v in N:
        headerTable[v] = None
        for e in hypergraph.nodes[v]['hyperedges']:
            addEdge(root, headerTable, e, order, N)
    
    Q = Queue()
    R = set()
    for v in reversed(gpList):
        nbrs = findGNbr(headerTable, v, g)
        S[v] = len(nbrs)
        if S[v] < k:
            Q.put(v)
            R.add(v)
    initialPhaseEnd = time.time()
    whileLoopStart = time.time()
    while not Q.empty():
        v = Q.get()
        gpList.remove(v)
        nbrs = findGNbr(headerTable, v, g)
        removeNode(v, headerTable)
        for u in nbrs:
            if u in R:
                continue
            S[u] -= 1 # EPA 처럼 개수까지 저장해놓으면 시간 거의 안 걸림
            if S[u] < k:
                Q.put(u)
                R.add(u)
        if v in headerTable: # 체크 필요한가?
            del headerTable[v]
    return set(headerTable.keys()), gpList, root, headerTable

def removeEdge(hypergraph, gpList, root, headerTable, hyperedge, k, g, S):

    gpSet = set(gpList)
    order = {v: i for i, v in enumerate(gpList)}
    deleteEdge(root, headerTable, hyperedge, order, gpSet)

    # peeling phase
    Q = Queue()
    R = set()
    for v in reversed(gpList):
        nbrs = findGNbr(headerTable, v, g)
        S[v] = len(nbrs)
        if S[v] < k:
            Q.put(v)
            R.add(v)
    initialPhaseEnd = time.time()
    whileLoopStart = time.time()
    while not Q.empty():
        v = Q.get()
        gpList.remove(v)
        nbrs = findGNbr(headerTable, v, g)
        removeNode(v, headerTable)
        for u in nbrs:
            if u in R:
                continue
            S[u] -= 1 # EPA 처럼 개수까지 저장해놓으면 시간 거의 안 걸림
            if S[u] < k:
                Q.put(u)
                R.add(u)
        if v in headerTable: # 체크 필요한가?
            del headerTable[v]
    return set(headerTable.keys()), gpList, root, headerTable

def printGPTree(root, headerTable):
    """
    root와 headerTable을 받아 현재 트리 구조를 보기 좋게 출력합니다.
    각 노드의 item, count, parent, children을 들여쓰기로 계층적으로 보여줍니다.
    """

    def printNode(node, depth=0):
        if node.item is not None:
            parent_item = node.parent.item if node.parent else None
            print("  " * depth + f"- item: {node.item}, count: {node.count}, parent: {parent_item}")
        for child in node.children.values():
            printNode(child, depth + 1)

    print("GP-Tree Structure:")
    printNode(root)
    print("\nHeader Table:")
    for item, node in headerTable.items():
        chain = []
        n = node
        while n:
            chain.append(f"(item:{n.item}, count:{n.count})")
            n = n.nodeLink
        print(f"{item}: {' -> '.join(chain) if chain else 'None'}")
    print("\n\n\n")