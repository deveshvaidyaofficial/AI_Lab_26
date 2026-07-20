"""
Graph Search Visualizer - BFS & DFS
====================================

A complete rewrite of a node/edge graph editor with animated Breadth
First Search and Depth First Search traversal, built from scratch with
an object oriented design and full compatibility with the
``simpleguitk`` library.

This file does not modify or depend on any previous implementation.
It is a standalone, runnable program.

Sections in this file:
    1. Configuration constants
    2. Node class
    3. Edge class
    4. Graph class (nodes / edges / adjacency list management)
    5. Search algorithms (SearchAlgorithm base, BFS, DFS)
    6. GraphEditor class (UI, interaction, drawing, animation)
    7. Program entry point

Only the simpleguitk event handlers that are actually supported are
used: ``set_mouseclick_handler``, ``set_mousedrag_handler`` and
``set_draw_handler``. Handlers such as ``set_mouseup_handler`` or
``set_mousedown_handler`` are intentionally NOT used, since they are
not part of the supported simpleguitk API.
"""

import json
import simpleguitk as simplegui


# ---------------------------------------------------------------------------
# 1. Configuration constants
# ---------------------------------------------------------------------------

WIDTH = 720
HEIGHT = 520

NODE_RADIUS = 15
NODE_CLICK_TOLERANCE = 20          # how close a click must be to "hit" a node
MIN_NODE_SEPARATION = NODE_RADIUS * 2 + 6   # minimum allowed gap between nodes

EDGE_COLOR = "Yellow"
EDGE_HIGHLIGHT_COLOR = "Purple"
EDGE_WIDTH = 2
EDGE_HIGHLIGHT_WIDTH = 4

NODE_COLOR = "Red"
NODE_VISITED_COLOR = "Green"
NODE_PATH_COLOR = "Blue"
NODE_START_COLOR = "Cyan"
NODE_GOAL_COLOR = "Orange"
NODE_SELECTED_RING_COLOR = "White"
NODE_BORDER_COLOR = "Black"
NODE_LABEL_COLOR = "White"

STATUS_TEXT_COLOR = "White"
STATUS_HIGHLIGHT_COLOR = "Yellow"

ANIMATION_DELAY_MS = 700            # milliseconds between animation steps

SAVE_FILE_NAME = "graph_save.json"
EXPORT_ADJACENCY_FILE_NAME = "adjacency_list.txt"
EXPORT_MATRIX_FILE_NAME = "adjacency_matrix.txt"
EXPORT_RESULT_FILE_NAME = "traversal_result.txt"


# ---------------------------------------------------------------------------
# 2. Node class
# ---------------------------------------------------------------------------

class Node:
    """Represents a single vertex of the graph.

    Attributes:
        node_id (int): The current numeric id / label of the node.
        x, y (float): Screen position of the node.
        radius (float): Drawing radius of the node.
        visited (bool): True once the node has been visited by a search.
        selected (bool): True while the node is selected/highlighted
            during editing (e.g. picked up for dragging, or chosen as
            the first endpoint of a new edge).
        on_path (bool): True if the node is part of the final
            reconstructed path after a successful search.
    """

    def __init__(self, node_id, x, y, radius=NODE_RADIUS):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.radius = radius
        self.visited = False
        self.selected = False
        self.on_path = False

    # -- geometry -----------------------------------------------------
    def contains_point(self, pos):
        """Return True if the given (x, y) position lies within the
        clickable tolerance radius of this node."""
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        distance_squared = dx * dx + dy * dy
        return distance_squared <= (NODE_CLICK_TOLERANCE ** 2)

    def distance_to(self, x, y):
        return ((self.x - x) ** 2 + (self.y - y) ** 2) ** 0.5

    def move(self, pos):
        """Move the node to a new position (used while dragging)."""
        self.x, self.y = pos[0], pos[1]

    # -- state ----------------------------------------------------------
    def reset(self):
        """Clear all transient search/selection state."""
        self.visited = False
        self.selected = False
        self.on_path = False

    # -- drawing ----------------------------------------------------------
    def draw(self, canvas, is_start=False, is_goal=False):
        """Draw the node on the canvas, colouring it according to its
        current state. Start/goal colouring takes priority so the user
        can always see which nodes are the current start and goal."""
        fill_color = NODE_COLOR
        if self.on_path:
            fill_color = NODE_PATH_COLOR
        elif self.visited:
            fill_color = NODE_VISITED_COLOR
        if is_start:
            fill_color = NODE_START_COLOR
        if is_goal:
            fill_color = NODE_GOAL_COLOR

        canvas.draw_circle(
            (self.x, self.y), self.radius, 2, NODE_BORDER_COLOR, fill_color
        )

        if self.selected:
            canvas.draw_circle(
                (self.x, self.y), self.radius + 5, 2, NODE_SELECTED_RING_COLOR
            )

        canvas.draw_text(
            str(self.node_id),
            (self.x - 6, self.y + 5),
            16,
            NODE_LABEL_COLOR,
        )


# ---------------------------------------------------------------------------
# 3. Edge class
# ---------------------------------------------------------------------------

class Edge:
    """Represents an undirected edge connecting two node ids."""

    def __init__(self, node_a_id, node_b_id):
        self.a = node_a_id
        self.b = node_b_id
        self.highlighted = False

    def involves(self, node_id):
        return self.a == node_id or self.b == node_id

    def other(self, node_id):
        """Return the id of the endpoint that is not ``node_id``."""
        return self.b if self.a == node_id else self.a

    def matches(self, a, b):
        """Return True if this edge connects the given pair of ids,
        regardless of order (the graph is undirected)."""
        return (self.a == a and self.b == b) or (self.a == b and self.b == a)

    def draw(self, canvas, nodes_by_id):
        node_a = nodes_by_id.get(self.a)
        node_b = nodes_by_id.get(self.b)
        if node_a is None or node_b is None:
            return
        color = EDGE_HIGHLIGHT_COLOR if self.highlighted else EDGE_COLOR
        width = EDGE_HIGHLIGHT_WIDTH if self.highlighted else EDGE_WIDTH
        canvas.draw_line((node_a.x, node_a.y), (node_b.x, node_b.y), width, color)


# ---------------------------------------------------------------------------
# 4. Graph class
# ---------------------------------------------------------------------------

class Graph:
    """Owns the collection of nodes and edges and provides all the
    graph-level operations (add/remove node, add/remove edge,
    renumbering, adjacency queries, serialization, ...).
    """

    def __init__(self):
        self.nodes = []   # list[Node], always kept sorted by node_id
        self.edges = []   # list[Edge]

    # -- node management -------------------------------------------------
    def add_node(self, x, y):
        """Attempt to add a new node at (x, y). Returns the created
        Node, or None if the position overlaps an existing node."""
        for existing in self.nodes:
            if existing.distance_to(x, y) < MIN_NODE_SEPARATION:
                return None
        new_node = Node(len(self.nodes), x, y)
        self.nodes.append(new_node)
        return new_node

    def remove_node(self, node_id):
        """Remove a node and every edge touching it, then renumber the
        remaining nodes/edges so ids stay contiguous starting at 0."""
        if self.get_node(node_id) is None:
            return False
        self.nodes = [n for n in self.nodes if n.node_id != node_id]
        self.edges = [e for e in self.edges if not e.involves(node_id)]
        self._renumber_after_removal(node_id)
        return True

    def _renumber_after_removal(self, removed_id):
        """Shift every id greater than the removed id down by one, both
        for nodes and for the edge endpoints that reference them."""
        for node in self.nodes:
            if node.node_id > removed_id:
                node.node_id -= 1
        for edge in self.edges:
            if edge.a > removed_id:
                edge.a -= 1
            if edge.b > removed_id:
                edge.b -= 1

    def renumber_nodes(self):
        """Re-derive node ids from their position in ``self.nodes``.
        Useful after bulk operations such as loading a saved graph."""
        self.nodes.sort(key=lambda n: n.node_id)
        remap = {}
        for new_id, node in enumerate(self.nodes):
            remap[node.node_id] = new_id
            node.node_id = new_id
        for edge in self.edges:
            edge.a = remap.get(edge.a, edge.a)
            edge.b = remap.get(edge.b, edge.b)

    def get_node(self, node_id):
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def find_node_at(self, pos):
        """Return the first node whose clickable area contains pos."""
        for node in self.nodes:
            if node.contains_point(pos):
                return node
        return None

    def node_count(self):
        return len(self.nodes)

    # -- edge management -------------------------------------------------
    def has_edge(self, a, b):
        return any(edge.matches(a, b) for edge in self.edges)

    def add_edge(self, a, b):
        """Add an undirected edge between a and b. Returns False if the
        edge already exists, is a self loop, or references an unknown
        node; True if the edge was created."""
        if a == b:
            return False
        if self.get_node(a) is None or self.get_node(b) is None:
            return False
        if self.has_edge(a, b):
            return False
        self.edges.append(Edge(a, b))
        return True

    def remove_edge(self, a, b):
        before = len(self.edges)
        self.edges = [edge for edge in self.edges if not edge.matches(a, b)]
        return len(self.edges) < before

    def edge_count(self):
        return len(self.edges)

    def get_neighbors(self, node_id):
        """Return a sorted list of node ids adjacent to node_id."""
        neighbors = []
        for edge in self.edges:
            if edge.a == node_id:
                neighbors.append(edge.b)
            elif edge.b == node_id:
                neighbors.append(edge.a)
        return sorted(neighbors)

    def adjacency_list(self):
        """Return {node_id: [neighbor_ids...]} for every node."""
        return {node.node_id: self.get_neighbors(node.node_id) for node in self.nodes}

    def adjacency_matrix(self):
        """Return a 2D list representing the adjacency matrix."""
        n = len(self.nodes)
        matrix = [[0] * n for _ in range(n)]
        for edge in self.edges:
            if 0 <= edge.a < n and 0 <= edge.b < n:
                matrix[edge.a][edge.b] = 1
                matrix[edge.b][edge.a] = 1
        return matrix

    # -- bulk state operations --------------------------------------------
    def reset_marks(self):
        """Clear per-node/edge search state (visited, path, highlight)
        without touching the graph structure itself."""
        for node in self.nodes:
            node.reset()
        for edge in self.edges:
            edge.highlighted = False

    def clear(self):
        self.nodes = []
        self.edges = []

    # -- serialization -----------------------------------------------------
    def to_dict(self):
        return {
            "nodes": [
                {"id": node.node_id, "x": node.x, "y": node.y}
                for node in self.nodes
            ],
            "edges": [{"a": edge.a, "b": edge.b} for edge in self.edges],
        }

    def from_dict(self, data):
        self.clear()
        for node_data in data.get("nodes", []):
            node = Node(node_data["id"], node_data["x"], node_data["y"])
            self.nodes.append(node)
        self.nodes.sort(key=lambda n: n.node_id)
        for edge_data in data.get("edges", []):
            self.edges.append(Edge(edge_data["a"], edge_data["b"]))


# ---------------------------------------------------------------------------
# 5. Search algorithms
# ---------------------------------------------------------------------------

class SearchAlgorithm:
    """Base class implementing a generic stepwise graph search so the
    UI can animate one step at a time. Subclasses only need to define
    how the frontier behaves (FIFO queue for BFS, LIFO stack for DFS).

    Public results, matching the behaviour of the original BFS/DFS:
        visited_order: list of node ids in the order they were expanded
        parent: dict mapping node_id -> parent node_id (or None for start)
        path: the reconstructed start->goal path once found (else [])
        found: True if the goal was reached
        finished: True once the algorithm has nothing more to do
        current: the node id most recently expanded (the "pointer")
        frontier: the current queue/stack contents (for visualisation)
    """

    def __init__(self, graph, start, goal):
        self.graph = graph
        self.start = start
        self.goal = goal

        self.visited_order = []
        self.parent = {start: None}
        self.frontier = [start]

        self.found = False
        self.finished = False
        self.current = None
        self.path = []

    def step(self):
        """Advance the search by exactly one expansion. Returns True
        once the search has finished (goal found, or frontier empty)."""
        if self.finished:
            return True

        if not self.frontier:
            self.finished = True
            return True

        node_id = self._pop_frontier()
        self.current = node_id
        self.visited_order.append(node_id)

        if node_id == self.goal:
            self.found = True
            self.finished = True
            self._build_path()
            return True

        for neighbor_id in self.graph.get_neighbors(node_id):
            already_seen = neighbor_id in self.parent
            if not already_seen:
                self.parent[neighbor_id] = node_id
                self._add_to_frontier(neighbor_id)

        if not self.frontier:
            self.finished = True

        return self.finished

    def _build_path(self):
        path = [self.goal]
        node_id = self.goal
        while self.parent.get(node_id) is not None:
            node_id = self.parent[node_id]
            path.append(node_id)
        path.reverse()
        self.path = path

    # -- overridden by subclasses --------------------------------------------
    def _pop_frontier(self):
        raise NotImplementedError

    def _add_to_frontier(self, node_id):
        raise NotImplementedError


class BFS(SearchAlgorithm):
    """Breadth First Search: the frontier behaves as a FIFO queue, so
    nodes are expanded in the order they were discovered."""

    def _pop_frontier(self):
        return self.frontier.pop(0)

    def _add_to_frontier(self, node_id):
        self.frontier.append(node_id)


class DFS(SearchAlgorithm):
    """Depth First Search: newly discovered neighbours are pushed to
    the front of the frontier so that the most recently discovered
    node is expanded next, matching stack (LIFO) behaviour."""

    def _pop_frontier(self):
        return self.frontier.pop(0)

    def _add_to_frontier(self, node_id):
        self.frontier.insert(0, node_id)


# ---------------------------------------------------------------------------
# 6. GraphEditor class - user interface, interaction and rendering
# ---------------------------------------------------------------------------

class GraphEditor:
    """Ties together the Graph model, the search algorithms, and the
    simpleguitk frame. Owns all mutable UI state (current mode, drag
    state, animation state) and every event handler / button callback.
    """

    MODE_ADD_NODE = "Add Node"
    MODE_MOVE_NODE = "Move Node"
    MODE_ADD_EDGE = "Add Edge"
    MODE_DELETE_EDGE = "Delete Edge"
    MODE_DELETE_NODE = "Delete Node"

    def __init__(self):
        self.graph = Graph()

        self.mode = self.MODE_ADD_NODE
        self.locked = False              # False = edit mode, True = search mode

        self.edge_first_node_id = None   # first endpoint chosen for add/delete edge
        self.drag_node_id = None         # node currently being dragged

        self.start_node_id = None
        self.goal_node_id = None

        self.algorithm = None            # active BFS/DFS instance, or None
        self.algorithm_name = None
        self.animation_running = False

        self.status_message = "Welcome! Click on the canvas to add nodes."

        self.frame = simplegui.create_frame(
            "Graph Search Visualizer - BFS & DFS", WIDTH, HEIGHT
        )
        self.frame.set_mouseclick_handler(self.on_click)
        self.frame.set_mousedrag_handler(self.on_drag)
        self.frame.set_draw_handler(self.draw)

        self._build_toolbar()

        self.timer = simplegui.create_timer(ANIMATION_DELAY_MS, self._animate_step)

    # -- UI construction --------------------------------------------------
    def _build_toolbar(self):
        self.frame.add_button("Add Node", self.set_mode_add_node)
        self.frame.add_button("Move Node", self.set_mode_move_node)
        self.frame.add_button("Add Edge", self.set_mode_add_edge)
        self.frame.add_button("Delete Edge", self.set_mode_delete_edge)
        self.frame.add_button("Delete Node", self.set_mode_delete_node)

        self.frame.add_button("Lock Graph (enter Search Mode)", self.lock_graph)
        self.frame.add_button("Unlock Graph (back to Edit Mode)", self.unlock_graph)

        self.start_input = self.frame.add_input(
            "Set Start Node #", self.handle_start_input, 60
        )
        self.goal_input = self.frame.add_input(
            "Set Goal Node #", self.handle_goal_input, 60
        )

        self.frame.add_button("Run BFS", self.run_bfs)
        self.frame.add_button("Run DFS", self.run_dfs)
        self.frame.add_button("Reset Search", self.reset_search)
        self.frame.add_button("Clear Graph", self.clear_graph)

        self.frame.add_button("Save Graph", self.save_graph)
        self.frame.add_button("Load Graph", self.load_graph)
        self.frame.add_button("Export Adjacency List", self.export_adjacency_list)
        self.frame.add_button("Export Adjacency Matrix", self.export_adjacency_matrix)

    # -- mode switching (edit mode only) ------------------------------------
    def _clear_edge_selection(self):
        if self.edge_first_node_id is not None:
            node = self.graph.get_node(self.edge_first_node_id)
            if node is not None:
                node.selected = False
        self.edge_first_node_id = None

    def _clear_drag_selection(self):
        if self.drag_node_id is not None:
            node = self.graph.get_node(self.drag_node_id)
            if node is not None:
                node.selected = False
        self.drag_node_id = None

    def _switch_mode(self, new_mode):
        if self.locked:
            self.status_message = "Unlock the graph first to edit it."
            return
        self._clear_edge_selection()
        self._clear_drag_selection()
        self.mode = new_mode
        self.status_message = "Mode: " + new_mode

    def set_mode_add_node(self):
        self._switch_mode(self.MODE_ADD_NODE)

    def set_mode_move_node(self):
        self._switch_mode(self.MODE_MOVE_NODE)

    def set_mode_add_edge(self):
        self._switch_mode(self.MODE_ADD_EDGE)

    def set_mode_delete_edge(self):
        self._switch_mode(self.MODE_DELETE_EDGE)

    def set_mode_delete_node(self):
        self._switch_mode(self.MODE_DELETE_NODE)

    # -- locking -----------------------------------------------------------
    def lock_graph(self):
        if self.locked:
            self.status_message = "Graph is already locked."
            return
        if self.graph.node_count() == 0:
            self.status_message = "Add at least one node before locking the graph."
            return
        self._clear_edge_selection()
        self._clear_drag_selection()
        self.locked = True
        self.status_message = (
            "Graph locked. Set a start and goal node, then run BFS or DFS."
        )

    def unlock_graph(self):
        self._stop_animation()
        self.locked = False
        self.algorithm = None
        self.algorithm_name = None
        self.graph.reset_marks()
        self.mode = self.MODE_ADD_NODE
        self.status_message = "Edit mode enabled. The graph can be modified again."

    # -- mouse interaction ---------------------------------------------------
    def on_click(self, pos):
        if self.locked:
            # In search mode, clicking the canvas has no editing effect;
            # start/goal are chosen through the text inputs instead.
            return

        if self.mode == self.MODE_ADD_NODE:
            self._handle_add_node_click(pos)
        elif self.mode == self.MODE_MOVE_NODE:
            self._handle_move_node_click(pos)
        elif self.mode == self.MODE_ADD_EDGE:
            self._handle_add_edge_click(pos)
        elif self.mode == self.MODE_DELETE_EDGE:
            self._handle_delete_edge_click(pos)
        elif self.mode == self.MODE_DELETE_NODE:
            self._handle_delete_node_click(pos)

    def _handle_add_node_click(self, pos):
        node = self.graph.add_node(pos[0], pos[1])
        if node is None:
            self.status_message = "Cannot place a node on top of another node."
        else:
            self.status_message = "Node {0} added.".format(node.node_id)

    def _handle_move_node_click(self, pos):
        if self.drag_node_id is None:
            node = self.graph.find_node_at(pos)
            if node is not None:
                self.drag_node_id = node.node_id
                node.selected = True
                self.status_message = (
                    "Dragging node {0}. Drag the mouse to move it, "
                    "click again to drop it.".format(node.node_id)
                )
        else:
            self._clear_drag_selection()
            self.status_message = "Node dropped."

    def _handle_add_edge_click(self, pos):
        node = self.graph.find_node_at(pos)
        if node is None:
            return
        if self.edge_first_node_id is None:
            self.edge_first_node_id = node.node_id
            node.selected = True
            self.status_message = (
                "Selected node {0}. Click a second node to connect it."
                .format(node.node_id)
            )
            return

        first_id = self.edge_first_node_id
        if node.node_id == first_id:
            self.status_message = "Self loops are not allowed."
            return

        if self.graph.add_edge(first_id, node.node_id):
            self.status_message = "Edge {0}-{1} created.".format(first_id, node.node_id)
        else:
            self.status_message = "That edge already exists."
        self._clear_edge_selection()

    def _handle_delete_edge_click(self, pos):
        node = self.graph.find_node_at(pos)
        if node is None:
            return
        if self.edge_first_node_id is None:
            self.edge_first_node_id = node.node_id
            node.selected = True
            self.status_message = (
                "Selected node {0}. Click the other endpoint to delete that edge."
                .format(node.node_id)
            )
            return

        first_id = self.edge_first_node_id
        if self.graph.remove_edge(first_id, node.node_id):
            self.status_message = "Edge {0}-{1} deleted.".format(first_id, node.node_id)
        else:
            self.status_message = "No edge exists between those nodes."
        self._clear_edge_selection()

    def _handle_delete_node_click(self, pos):
        node = self.graph.find_node_at(pos)
        if node is None:
            return
        deleted_id = node.node_id
        self.graph.remove_node(deleted_id)
        self.start_node_id = self._shift_reference_after_delete(
            self.start_node_id, deleted_id
        )
        self.goal_node_id = self._shift_reference_after_delete(
            self.goal_node_id, deleted_id
        )
        self._clear_edge_selection()
        self._clear_drag_selection()
        self.status_message = "Node {0} deleted.".format(deleted_id)

    @staticmethod
    def _shift_reference_after_delete(reference_id, deleted_id):
        """Update a stored node id (start/goal) after a node has been
        removed and the remaining nodes renumbered."""
        if reference_id is None:
            return None
        if reference_id == deleted_id:
            return None
        if reference_id > deleted_id:
            return reference_id - 1
        return reference_id

    def on_drag(self, pos):
        if self.locked:
            return
        if self.mode == self.MODE_MOVE_NODE and self.drag_node_id is not None:
            node = self.graph.get_node(self.drag_node_id)
            if node is not None:
                node.move(pos)

    # -- start / goal text inputs --------------------------------------------
    def handle_start_input(self, text):
        if not self.locked:
            self.status_message = "Lock the graph before setting the start node."
            return
        node_id = self._parse_valid_node_id(text)
        if node_id is None:
            self.status_message = "Invalid start node number."
            return
        self.start_node_id = node_id
        self.status_message = "Start node set to {0}.".format(node_id)

    def handle_goal_input(self, text):
        if not self.locked:
            self.status_message = "Lock the graph before setting the goal node."
            return
        node_id = self._parse_valid_node_id(text)
        if node_id is None:
            self.status_message = "Invalid goal node number."
            return
        self.goal_node_id = node_id
        self.status_message = "Goal node set to {0}.".format(node_id)

    def _parse_valid_node_id(self, text):
        text = text.strip()
        if not text.isdigit():
            return None
        value = int(text)
        if 0 <= value < self.graph.node_count():
            return value
        return None

    # -- search execution / animation ------------------------------------
    def run_bfs(self):
        self._start_search(BFS, "BFS")

    def run_dfs(self):
        self._start_search(DFS, "DFS")

    def _start_search(self, algorithm_cls, name):
        if not self.locked:
            self.status_message = "Lock the graph before running a search."
            return
        if self.start_node_id is None or self.goal_node_id is None:
            self.status_message = "Set both a start node and a goal node first."
            return

        self.graph.reset_marks()
        self.algorithm = algorithm_cls(self.graph, self.start_node_id, self.goal_node_id)
        self.algorithm_name = name
        self.animation_running = True
        self.status_message = "Running {0}...".format(name)
        self.timer.start()

    def _animate_step(self):
        if self.algorithm is None or not self.animation_running:
            self.timer.stop()
            return

        finished = self.algorithm.step()

        current_id = self.algorithm.current
        if current_id is not None:
            current_node = self.graph.get_node(current_id)
            if current_node is not None:
                current_node.visited = True

        if finished:
            self._stop_animation()
            self._finalize_search()

    def _stop_animation(self):
        self.animation_running = False
        self.timer.stop()

    def _finalize_search(self):
        if self.algorithm is None:
            return
        if self.algorithm.found:
            self._highlight_path(self.algorithm.path)
            self.status_message = "{0} succeeded! Path: {1}".format(
                self.algorithm_name, self._format_path(self.algorithm.path)
            )
            self._export_traversal_result()
        else:
            self.status_message = "{0} finished. Goal is not reachable from start.".format(
                self.algorithm_name
            )

    def _highlight_path(self, path):
        for node_id in path:
            node = self.graph.get_node(node_id)
            if node is not None:
                node.on_path = True
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            for edge in self.graph.edges:
                if edge.matches(a, b):
                    edge.highlighted = True

    @staticmethod
    def _format_path(path):
        return " -> ".join(str(node_id) for node_id in path)

    def reset_search(self):
        self._stop_animation()
        self.algorithm = None
        self.algorithm_name = None
        self.graph.reset_marks()
        self.status_message = "Search state reset. Nodes and edges are unchanged."

    # -- clearing / persistence --------------------------------------------
    def clear_graph(self):
        self._stop_animation()
        self.graph.clear()
        self.start_node_id = None
        self.goal_node_id = None
        self.algorithm = None
        self.algorithm_name = None
        self.locked = False
        self.mode = self.MODE_ADD_NODE
        self.edge_first_node_id = None
        self.drag_node_id = None
        self.status_message = "Graph cleared."

    def save_graph(self):
        try:
            data = self.graph.to_dict()
            data["start"] = self.start_node_id
            data["goal"] = self.goal_node_id
            with open(SAVE_FILE_NAME, "w") as save_file:
                json.dump(data, save_file)
            self.status_message = "Graph saved to {0}.".format(SAVE_FILE_NAME)
        except (IOError, OSError, TypeError, ValueError) as error:
            self.status_message = "Save failed: {0}".format(error)

    def load_graph(self):
        try:
            with open(SAVE_FILE_NAME, "r") as save_file:
                data = json.load(save_file)
            self._stop_animation()
            self.graph.from_dict(data)
            self.start_node_id = data.get("start")
            self.goal_node_id = data.get("goal")
            self.algorithm = None
            self.algorithm_name = None
            self.locked = False
            self.mode = self.MODE_ADD_NODE
            self.edge_first_node_id = None
            self.drag_node_id = None
            self.status_message = "Graph loaded from {0}.".format(SAVE_FILE_NAME)
        except (IOError, OSError, ValueError, KeyError) as error:
            self.status_message = "Load failed: {0}".format(error)

    def export_adjacency_list(self):
        adjacency = self.graph.adjacency_list()
        lines = []
        for node_id in sorted(adjacency.keys()):
            neighbors = " ".join(str(n) for n in adjacency[node_id])
            lines.append("{0} -> {1}".format(node_id, neighbors))
        text = "\n".join(lines)
        try:
            with open(EXPORT_ADJACENCY_FILE_NAME, "w") as out_file:
                out_file.write(text)
            self.status_message = "Adjacency list exported to {0}.".format(
                EXPORT_ADJACENCY_FILE_NAME
            )
        except (IOError, OSError) as error:
            self.status_message = "Export failed: {0}".format(error)
        print("Adjacency List:")
        print(text)

    def export_adjacency_matrix(self):
        matrix = self.graph.adjacency_matrix()
        lines = [" ".join(str(v) for v in row) for row in matrix]
        text = "\n".join(lines)
        try:
            with open(EXPORT_MATRIX_FILE_NAME, "w") as out_file:
                out_file.write(text)
            self.status_message = "Adjacency matrix exported to {0}.".format(
                EXPORT_MATRIX_FILE_NAME
            )
        except (IOError, OSError) as error:
            self.status_message = "Export failed: {0}".format(error)
        print("Adjacency Matrix:")
        print(text)

    def _export_traversal_result(self):
        if self.algorithm is None:
            return
        lines = [
            "Algorithm: {0}".format(self.algorithm_name),
            "Visited order: {0}".format(
                " ".join(str(n) for n in self.algorithm.visited_order)
            ),
            "Path: {0}".format(self._format_path(self.algorithm.path)),
        ]
        text = "\n".join(lines)
        try:
            with open(EXPORT_RESULT_FILE_NAME, "w") as out_file:
                out_file.write(text)
        except (IOError, OSError):
            pass

    # -- drawing -----------------------------------------------------------
    def draw(self, canvas):
        nodes_by_id = {node.node_id: node for node in self.graph.nodes}

        for edge in self.graph.edges:
            edge.draw(canvas, nodes_by_id)

        for node in self.graph.nodes:
            is_start = node.node_id == self.start_node_id
            is_goal = node.node_id == self.goal_node_id
            node.draw(canvas, is_start, is_goal)

        self._draw_status_bar(canvas)
        if self.algorithm is not None:
            self._draw_search_panel(canvas)

    def _draw_status_bar(self, canvas):
        y = 20
        line_height = 20

        mode_text = "Current State :SEARCH MODE" if self.locked else "Current State : Editing Mode - " + self.mode
        canvas.draw_text(mode_text, (10, y), 15, STATUS_TEXT_COLOR)
        y += line_height

        counts_text = "Nodes: {0}   Edges: {1}".format(
            self.graph.node_count(), self.graph.edge_count()
        )
        canvas.draw_text(counts_text, (10, y), 14, STATUS_TEXT_COLOR)
        y += line_height

        start_goal_text = "Start: {0}   Goal: {1}".format(
            self.start_node_id, self.goal_node_id
        )
        canvas.draw_text(start_goal_text, (10, y), 14, STATUS_TEXT_COLOR)
        y += line_height

        canvas.draw_text(self.status_message, (10, y), 14, STATUS_HIGHLIGHT_COLOR)

    def _draw_search_panel(self, canvas):
        y = HEIGHT - 80
        line_height = 20

        canvas.draw_text(
            "Algorithm: {0}".format(self.algorithm_name), (10, y), 14, STATUS_TEXT_COLOR
        )
        y += line_height

        pointer_text = "Pointer: {0}".format(self.algorithm.current)
        canvas.draw_text(pointer_text, (10, y), 14, STATUS_TEXT_COLOR)
        y += line_height

        visited_text = "Visited: " + " ".join(
            str(n) for n in self.algorithm.visited_order
        )
        canvas.draw_text(visited_text, (10, y), 14, STATUS_TEXT_COLOR)
        y += line_height

        frontier_label = "Stack" if self.algorithm_name == "DFS" else "Queue"
        frontier_text = "{0}: {1}".format(
            frontier_label, " ".join(str(n) for n in self.algorithm.frontier)
        )
        canvas.draw_text(frontier_text, (10, y), 14, STATUS_TEXT_COLOR)

    # -- lifecycle -----------------------------------------------------------
    def start(self):
        self.frame.start()


# ---------------------------------------------------------------------------
# 7. Program entry point
# ---------------------------------------------------------------------------

def main():
    editor = GraphEditor()
    editor.start()


if __name__ == "__main__":
    main()