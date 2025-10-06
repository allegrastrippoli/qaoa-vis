from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGraphicsView, QGraphicsScene, QPushButton,
    QGraphicsEllipseItem, QGraphicsTextItem, QSlider, QLabel
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import Qt
import networkx as nx
import json, sys


with open("state_probability_1.json") as f:
    data = json.load(f)


class GraphNode(QGraphicsEllipseItem):
    def __init__(self, node_id, x, y, r=20, color="white"):
        super().__init__(-r, -r, 2 * r, 2 * r)
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemIsSelectable, True)
        self.setZValue(200)
        self.node_id = node_id

        self.label = QGraphicsTextItem(str(node_id), self)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setPos(-r / 2, -r / 2)
        self.label.setZValue(300)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive QAOA")
        self.setGeometry(100, 100, 1200, 600)

        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        chart_layout = QVBoxLayout()

        self.web_view = QWebEngineView()
        self.current_index = 0
        self.period = data[0]["Period"]

        self.create_html_plot()
        self.web_view.setHtml(self.html_content)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(data) // self.period - 1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.slider_update)
        chart_layout.addWidget(self.web_view)

        self.slider_label = QLabel("Layer 0")

        chart_layout.addWidget(self.slider_label)
        chart_layout.addWidget(self.slider)
        
        layout.addLayout(chart_layout)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

        self.load_graph()

    def load_graph(self):
        try:
            with open("graph.txt") as f:
                edges = [tuple(map(int, line.strip().split(','))) for line in f]
        except FileNotFoundError:
            return 

        G = nx.Graph()
        G.add_edges_from(edges)
        pos = nx.spring_layout(G, k=10, scale=100)
        node_objs = {}

        for node_id, (x, y) in pos.items():
            node = GraphNode(node_id, x, y)
            self.scene.addItem(node)
            node_objs[node_id] = node

        for u, v in G.edges():
            self.add_edge(self.scene, node_objs[u], node_objs[v])

        group = self.scene.createItemGroup(self.scene.items())
        group.setFlag(group.ItemIsMovable, True)

    def add_edge(self, scene, node1, node2):
        x1 = node1.rect().x() + node1.rect().width() / 2 + node1.pos().x()
        y1 = node1.rect().y() + node1.rect().height() / 2 + node1.pos().y()
        x2 = node2.rect().x() + node2.rect().width() / 2 + node2.pos().x()
        y2 = node2.rect().y() + node2.rect().height() / 2 + node2.pos().y()
        line = scene.addLine(x1, y1, x2, y2)
        line.setPen(QPen(Qt.black, 2))
        line.setZValue(100)
        return line

    def create_html_plot(self):
        first_group = data[self.current_index:self.current_index + self.period]
        traces_js = ""

        for i, elem in enumerate(first_group):
            x_values = json.dumps([str(s) for s in elem["State"]])
            y_values = json.dumps(elem["Probability"])  # Serialize to JSON array
            traces_js += f"""
            {{
                x: {x_values},
                y: {y_values},
                mode: 'lines+markers',
                name: 'γ,β=0.0{i + 1}'
            }},"""

        self.html_content = f"""
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div id="plot" style="width:100%;height:100%"></div>
            <script>
                var traces = [{traces_js}];

                var layout = {{
                    title: 'State Probabilities',
                    xaxis: {{title: 'State', type: 'category' }},
                    yaxis: {{title: 'Probability'}}
                }};

                Plotly.newPlot('plot', traces, layout);

                function updateData(newYs) {{
                    for (var i = 0; i < newYs.length; i++) {{
                        Plotly.animate('plot', {{
                            data: [{{ y: newYs[i] }}],
                            traces: [i],
                            layout: {{}}
                        }}, {{
                            transition: {{ duration: 1000, easing: 'cubic-in-out' }},
                            frame: {{ duration: 1000, redraw: false }}
                        }});
                    }}
                }}
            </script>
        </body>
        </html>
        """

    def animate_update(self):
        next_indices = [
            (self.current_index + self.period + i) % len(data)
            for i in range(self.period)
        ]
        new_y_values = [data[idx]["Probability"] for idx in next_indices]

        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        js_command = f"updateData({js_array});"
        self.web_view.page().runJavaScript(js_command)

        self.current_index = (self.current_index + self.period) % len(data)
        
    def slider_update(self, value):
        """Called whenever the slider moves."""
        self.slider_label.setText(f"Layer: {value}")

        start_index = value * self.period
        next_indices = [
            (start_index + i) % len(data)
            for i in range(self.period)
        ]
        new_y_values = [data[idx]["Probability"] for idx in next_indices]

        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        js_command = f"updateData({js_array});"
        self.web_view.page().runJavaScript(js_command)

        self.current_index = start_index



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
