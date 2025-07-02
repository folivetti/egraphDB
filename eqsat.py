import postgres as pg 

db = pg.Postgres("postgresql://localhost:5432/egraph")

class Node:
    def __init__(self, symbol, data=None, children=None):
        self.symbol = symbol
        self.data = data
        self.children = children if children is not None else []
    def to_tuple(self, child_eclass=[-1, -1]):
        l = child_eclass[0]
        r = child_eclass[1]
        return (self.symbol, l, r, self.data if self.data is not None else -1)
    def to_row(self, child_eclass=[-1, -1]):
        l = child_eclass[0]
        r = child_eclass[1]
        return f"ROW('{self.symbol}'::symbol, {l}, {r}, {self.data if self.data is not None else -1}::NUMERIC)"

def insert_node(node, conn):
    children = []
    for child in node.children:
        children.append(insert_node(child, conn))
    children += [-1] * (2 - len(children))  # Ensure exactly two children
    tpl = node.to_row(children)
    print(tpl)

    query = f"""
    INSERT INTO enode_map VALUES({tpl}) ON CONFLICT (enode) DO UPDATE SET enode=EXCLUDED.enode RETURNING eid;
    """
    print(query)
    with conn.cursor() as cursor:
        eid = cursor.one(query)
        conn.commit()
        return eid

def get_eclass(node, conn):
    children = []
    for child in node.children:
        children.append(get_eclass(child, conn))
    children += [-1] * (2 - len(children))  # Ensure exactly two children
    tpl = node.to_row(children)

    query = f"""
    SELECT eid FROM enode_map WHERE enode = {tpl};
    """

    print(query)
    with conn.cursor() as cursor:
        eid = cursor.one(query)
        conn.commit()
        return eid

x0 = Node("VAR", 0, [])
t0 = Node("PARAM", 0, [])
tree = Node("ADD", None, [x0, t0])

with db.get_connection() as conn:
    print(insert_node(tree, conn))
    print(get_eclass(tree, conn))
