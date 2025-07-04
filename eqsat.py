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
    height = 0
    size = 0
    cost = 0
    for child in node.children:
        eid, h, sz, c = insert_node(child, conn)
        children.append(eid)
        height = max(height, h)
        size += sz
        cost += c
    enode = Node(node.symbol, node.data, children)
    height += 1
    size += 1
    cost += 1
    children += [-1] * (2 - len(children))  # Ensure exactly two children
    tpl = node.to_row(children)

    query = f"""
    INSERT INTO enode_map VALUES({tpl}) ON CONFLICT (enode) DO UPDATE SET enode=EXCLUDED.enode RETURNING eid;
    """
    with conn.cursor() as cursor:
        eid = cursor.one(query)
        query_eclass = f"""
        INSERT INTO eclass VALUES({eid}, {height}, {size}, {cost}, {enode.to_row()})
        ON CONFLICT (eid)
        DO UPDATE SET
           height = EXCLUDED.height,
           size   = EXCLUDED.size,
           best   = EXCLUDED.best,
           cost   = EXCLUDED.cost
        WHERE eclass.cost > EXCLUDED.cost;
        INSERT INTO canonical_map VALUES({eid},{eid})
        ON CONFLICT (from_eid)
        DO NOTHING;
        """
        cursor.execute(query_eclass)
        for c in children:
            if c > -1:
                query_parent = f"""INSERT INTO parents VALUES({c}, {eid}, {enode.to_row()}) ON CONFLICT (eid, parent_eid, enode) DO NOTHING"""
                cursor.execute(query_parent)
        conn.commit()
        return eid, height, size, cost

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

    print(query)
    with conn.cursor() as cursor:
        eid = cursor.one(query)
        conn.commit()
        return eid

def assemble_tree(eid, conn):
    query = f"""
    WITH RECURSIVE enode_tree AS (
        SELECT
            em.eid,
            em.enode,
            1 AS depth,
            ARRAY[em.eid] AS path
        FROM
            enode_map em
        WHERE
            em.eid = {eid}

        UNION ALL
        SELECT
            child.eid,
            child.enode,
            parent.depth + 1,
            parent.path || child.eid -- Append current eid to the path
        FROM
            enode_map child
        JOIN
            enode_tree parent ON (parent.enode).left_c = child.eid OR (parent.enode).right_c = child.eid
        WHERE
            NOT (child.eid = ANY(parent.path))
    )

    SELECT
        eid,
        enode,
        (enode).op AS op,
        (enode).value AS value,
        depth
    FROM
        enode_tree
    ORDER BY
        path;
    """
    with conn.cursor() as cursor:
        enodes = cursor.all(query)
        conn.commit()
        return enodes

x0 = Node("VAR", 0, [])
t0 = Node("PARAM", 0, [])
tree = Node("ADD", None, [x0, t0])
tree2 = Node("MUL", None, [x0, tree])
tree3 = Node("LN", None, [tree2])

with db.get_connection() as conn:
    print(insert_node(tree, conn))
    print(get_eclass(tree, conn))
    print(assemble_tree(3, conn))
    print(insert_node(tree3, conn))
    eid = get_eclass(tree3, conn)
    print(assemble_tree(eid, conn))
