import sys
import numpy as np
import networkx as nx
import plotly.graph_objects as go
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout , QHBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import Qt

x = np.linspace(0, 10, 1000)
frequencies = [0.5, 1.0, 2.0, 3.0]

fig = go.Figure()
for freq in frequencies:
    fig.add_trace(go.Scatter(x=x, y=np.sin(freq * x), name=f'freq={freq}'))

fig.update_layout(title="Sine Waves with Different Frequencies")

html = fig.to_html(include_plotlyjs='cdn')

class GraphNode(QGraphicsEllipseItem):
    def __init__(self, node_id, x, y, r=20, color="white"):
        super().__init__(-r, -r, 2*r, 2*r)
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemIsSelectable, True)
        self.setZValue(200)

        self.node_id = node_id
        self.label = QGraphicsTextItem(str(node_id), self)  # attach text to node
        self.label.setDefaultTextColor(Qt.black)
        self.label.setPos(-r/2, -r/2)  # center the text roughly
        self.label.setZValue(300)

        self.neighbors = set()

    def add_neighbor(self, other):
        self.neighbors.add(other)
        other.neighbors.add(self)
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive QAOA")
        self.setGeometry(100, 100, 1200, 600)

        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)

        chart_layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        self.web_view.setHtml(html)

        chart_layout.addWidget(self.web_view)
        layout.addLayout(chart_layout)

        # --- Right: Canvas for Drawing ---
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(self.view.renderHints())
        
        def add_edge(scene, node1, node2):
            x1 = node1.rect().x() + node1.rect().width()/2 + node1.pos().x()
            y1 = node1.rect().y() + node1.rect().height()/2 + node1.pos().y()
            x2 = node2.rect().x() + node2.rect().width()/2 + node2.pos().x()
            y2 = node2.rect().y() + node2.rect().height()/2 + node2.pos().y()

            line = scene.addLine(x1, y1, x2, y2)
            line.setPen(QPen(Qt.black, 2))
            line.setZValue(100) 
            # scene.addItem(line)
            return line
        
        G = nx.Graph()
        G.add_nodes_from([1,2,3,4,5])
        G.add_edges_from([(1,2),(1,3),(1,4),(1,5)])
        pos = nx.spring_layout(G, k=50, scale=100) 
        nodes = {}
        for node_id, (x, y) in pos.items():
            node = GraphNode(node_id, x, y)
            self.scene.addItem(node)
            nodes[node_id] = node
        for u, v in G.edges():
            add_edge(self.scene, nodes[u], nodes[v])
        
        group = self.scene.createItemGroup(self.scene.items())
        group.setFlag(group.ItemIsMovable, True)

        # for item in self.scene.items():
        #     item.setFlag(item.ItemIsMovable, True)
        #     item.setFlag(item.ItemIsSelectable, True)

        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
