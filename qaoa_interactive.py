from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QSlider, QLabel
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, QtCore
import json, sys

with open("state_probability.json") as f:
    data_prob = json.load(f)

params_prob = data_prob[0]
data_prob = data_prob[1:]

with open("state_phase.json") as f:
    data_phase = json.load(f)

params_phase = data_phase[0]
data_phase = data_phase[1:]

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
        main_widget = QWidget()
        horizontal_layout = QHBoxLayout(main_widget) 

        left_layout = QVBoxLayout()

        top_layout = QVBoxLayout()
        self.web_view_top = QWebEngineView()
        self.current_index_top = 0
        self.period = params_prob["Period"]

        self.create_html_plot(data_prob, params_prob, "Probability")
        self.web_view_top.setHtml(self.html_content)

        self.slider_top = QSlider(Qt.Horizontal)
        self.slider_top.setMinimum(0)
        self.slider_top.setMaximum(len(data_prob) // self.period - 1)
        self.slider_top.valueChanged.connect(self.slider_update_top)
        self.slider_label_top = QLabel("Layer 0 (Probability)")

        top_layout.addWidget(self.web_view_top)
        top_layout.addWidget(self.slider_label_top)
        top_layout.addWidget(self.slider_top)

        bottom_layout = QVBoxLayout()
        self.web_view_bottom = QWebEngineView()
        self.current_index_bottom = 0

        self.create_html_plot(data_phase, params_phase, "Phase")
        self.web_view_bottom.setHtml(self.html_content)

        self.slider_bottom = QSlider(Qt.Horizontal)
        self.slider_bottom.setMinimum(0)
        self.slider_bottom.setMaximum(len(data_phase) // self.period - 1)
        self.slider_bottom.valueChanged.connect(self.slider_update_bottom)
        self.slider_label_bottom = QLabel("Layer 0 (Phase)")

        bottom_layout.addWidget(self.web_view_bottom)
        bottom_layout.addWidget(self.slider_label_bottom)
        bottom_layout.addWidget(self.slider_bottom)

        left_layout.addLayout(top_layout)
        left_layout.addLayout(bottom_layout)
        horizontal_layout.addLayout(left_layout)

        right_layout = QVBoxLayout()

        self.graph_view = QWebEngineView()
        right_layout.addWidget(self.graph_view, stretch=3)

        self.canvas_view = QGraphicsView()
        self.canvas_scene = QGraphicsScene()
        self.canvas_view.setScene(self.canvas_scene)
        self.draw_arrow_canvas() 
        right_layout.addWidget(self.canvas_view, stretch=2)

        horizontal_layout.addLayout(right_layout)
        self.setCentralWidget(main_widget)

        self.load_graph_js()



    def load_graph_js(self):
            try:
                with open("graph.txt") as f:
                    edges = [tuple(map(int, line.strip().split(','))) for line in f]
            except FileNotFoundError:
                return

            nodes = sorted(set([n for e in edges for n in e]))

            js_nodes = json.dumps([{"id": n, "label": str(n)} for n in nodes])
            js_edges = json.dumps([{"from": u, "to": v} for u, v in edges])

            html = f"""
            <html>
            <head>
                <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
                <style>
                    #graph {{
                        width: 100%;
                        height: 100vh;
                        border: 1px solid lightgray;
                    }}
                </style>
            </head>
            <body>
                <div id="graph"></div>
                <script>
                    var nodes = new vis.DataSet({js_nodes});
                    var edges = new vis.DataSet({js_edges});
                    var container = document.getElementById('graph');
                    var data = {{ nodes: nodes, edges: edges }};
                    var options = {{
                        physics: true,
                        interaction: {{ hover: true }},
                        nodes: {{
                            shape: 'dot',
                            size: 10,
                            color: '#97C2FC',
                            font: {{ size: 14, color: '#333' }}
                        }},
                        edges: {{
                            color: '#555',
                            width: 2,
                            smooth: {{ type: 'continuous' }}
                        }}
                    }};
                    var network = new vis.Network(container, data, options);

                    // Example: function callable from Python
                    function highlightNode(id) {{
                        nodes.update({{id: id, color: {{background: 'orange'}}}});
                    }}
                </script>
            </body>
            </html>
            """

            self.graph_view.setHtml(html)


    def add_edge(self, scene, node1, node2):
        x1 = node1.rect().x() + node1.rect().width() / 2 + node1.pos().x()
        y1 = node1.rect().y() + node1.rect().height() / 2 + node1.pos().y()
        x2 = node2.rect().x() + node2.rect().width() / 2 + node2.pos().x()
        y2 = node2.rect().y() + node2.rect().height() / 2 + node2.pos().y()
        line = scene.addLine(x1, y1, x2, y2)
        line.setPen(QPen(Qt.black, 2))
        line.setZValue(100)
        return line
    
    def update_arrow_position(self, layer_index):
        if not hasattr(self, "squares") or layer_index >= len(self.squares):
            return

        square = self.squares[layer_index]
        rect = square.rect()
        x = square.rect().x() + square.pos().x() + rect.width() / 2
        y = square.rect().y() + square.pos().y()

        start_x = x 
        start_y = y - 40
        end_x = x
        end_y = y - 20
        self.arrow_line.setLine(start_x, start_y, end_x, end_y)

        arrow_size = 12
        points = QtGui.QPolygonF([
            QtCore.QPointF(end_x,  end_y  + arrow_size),
            QtCore.QPointF(end_x + arrow_size / 2, end_y),
            QtCore.QPointF(end_x - arrow_size / 2, end_y),
        ])
        self.arrow_head.setPolygon(points)

        self.canvas_scene.update()
        self.canvas_view.viewport().update()


    
    def draw_arrow_canvas(self):
        self.canvas_scene.clear()

        num_layers = self.slider_top.maximum() + 1  
        square_size = 80
        spacing = 30
        start_x = 50
        y = 100

        self.squares = []  
        
        cost_mixer_labels = ['C', 'M']
        idx = -1
        for i in range(num_layers):
            x = start_x + i * (square_size + spacing)
            rect_item = self.canvas_scene.addRect(
                x, y, square_size, square_size,
                QPen(Qt.black, 2),
                QBrush(Qt.lightGray)
            )              
            if i % 2 == 0:
                idx += 1
            label_html = f"<span style='font-size:16px;'>&#770;U<sub>{cost_mixer_labels[i%2]}</sub>(γ<sub>{idx}</sub>)</span>"
            label = self.canvas_scene.addText("")
            label.setHtml(label_html)
            label.setDefaultTextColor(Qt.black)

            text_rect = label.boundingRect()
            label.setPos(
                x + (square_size - text_rect.width()) / 2,
                y + (square_size - text_rect.height()) / 2
            )

            self.squares.append(rect_item)

        self.arrow_line = self.canvas_scene.addLine(0, 0, 0, 0, QPen(Qt.red, 3))

        self.arrow_head = self.canvas_scene.addPolygon(
            QtGui.QPolygonF(),
            QPen(Qt.red, 3),
            QBrush(Qt.red)
        )

        self.update_arrow_position(0)


    def create_html_plot(self, dataset, params, y_key):
        first_group = dataset[self.current_index_top:self.current_index_top + params["Period"]]
        traces_js = ""

        for i, elem in enumerate(first_group):
            x_values = json.dumps([str(s) for s in elem["State"]])
            y_values = json.dumps(elem[y_key])
            traces_js += f"""
            {{
                x: {x_values},
                y: {y_values},
                mode: 'lines+markers',
                name: 'γ,β={params["Fixed parameters"][i]}'
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
                    title: 'QAOA Viz ({y_key})',
                    xaxis: {{title: 'State', type: 'category' }},
                    yaxis: {{title: '{y_key}', range: [{params["Y range"][0]}, {params["Y range"][1]}] }}
                }};
                Plotly.newPlot('plot', traces, layout);

                function updateData(newYs) {{
                    for (var i = 0; i < newYs.length; i++) {{
                        Plotly.animate('plot', {{
                            data: [{{ y: newYs[i] }}],
                            traces: [i],
                        }}, {{
                            transition: {{ duration: 0 }},
                            frame: {{ duration: 100, redraw: false }}
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
        
  
    def slider_update_top(self, value):
        self.slider_label_top.setText(f"Layer: {value}")
        start_index = value * self.period
        next_indices = [(start_index + i) % len(data_prob) for i in range(self.period)]
        new_y_values = [data_prob[idx]["Probability"] for idx in next_indices]
        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        self.web_view_top.page().runJavaScript(f"updateData({js_array});")
        self.update_arrow_position(value)


    def slider_update_bottom(self, value):
        self.slider_label_bottom.setText(f"Layer: {value}")
        start_index = value * self.period
        next_indices = [(start_index + i) % len(data_phase) for i in range(self.period)]
        new_y_values = [data_phase[idx]["Phase"] for idx in next_indices]
        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        self.web_view_bottom.page().runJavaScript(f"updateData({js_array});")
        self.update_arrow_position(value)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())
