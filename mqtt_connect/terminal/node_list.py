from textual.containers import VerticalScroll
from textual.widgets import Tree


class NodeList(VerticalScroll):

    can_focus = True

    def __init__(self, id: str = "node-list", *args, **kwargs):
        super().__init__(id=id, *args, **kwargs)
        self.nodes = (
            {}
        )  # store nodes {node_id: (short_name, long_name, telemetry_data)}

    def compose(self):
        """Define UI components."""
        yield Tree("Nodes and Telemetry", id="nodes-tree")

    def update_nodes(self, node_id, short_name, long_name):
        """Add or update a node entry in the tree."""
        tree = self.query_one("#nodes-tree", Tree)  # Query for the tree
        if node_id not in self.nodes:
            self.nodes[node_id] = (short_name, long_name, None)
            tree.root.add(node_id, f"{short_name} ({long_name})")  # Add new node
        else:
            # Node exists, update the entry without modifying telemetry (if any)
            telemetry = self.nodes[node_id][2]
            self.nodes[node_id] = (short_name, long_name, telemetry)
            self.refresh_tree()

    def update_telemetry(self, node_id, battery, temperature, humidity, pressure):
        """Update telemetry data for an existing node."""
        if node_id in self.nodes:
            short_name, long_name, _ = self.nodes[node_id]  # Keep existing node info
            telemetry_data = f"Battery: {battery}%, Temp: {temperature}°C, Humidity: {humidity}%, Pressure: {pressure} hPa"
            self.nodes[node_id] = (short_name, long_name, telemetry_data)
            self.refresh_tree()

    def refresh_tree(self):
        """Rebuilds the tree view to reflect updated node information."""
        tree = self.query_one("#nodes-tree", Tree)  # Query for the tree
        tree.clear()
        for node_id, (short_name, long_name, telemetry) in self.nodes.items():
            node_text = f"{short_name} ({long_name})"
            if telemetry:
                node_entry = tree.root.add(node_id, node_text, expand=True)
                node_entry.add(telemetry)  # Add telemetry as a sub-item
            else:
                tree.root.add(node_id, node_text)
