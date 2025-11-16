from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QGraphicsView, QGraphicsScene
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt
from data.loader import load_json, load_edges
from ui.html_plot import build_visjs_html, create_plot_html
from ui.graph_canvas import QAOALayerCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive QAOA")
        (self.params_prob, self.data_prob) = load_json("resources/charts/state_probability_aggregate/state_probability_aggregate.json")
        (self.params_phase, self.data_phase) = load_json("resources/charts/state_phase_aggregate/state_phase_aggregate.json")
        self.setup_ui()

    def setup_ui(self):
        main = QWidget()
        horizontal_layout = QHBoxLayout(main)
        top_layout = self.setup_top()
        bottom_layout = self.setup_bottom()        
        self.setup_left(horizontal_layout, [top_layout, bottom_layout])
        self.setup_right(horizontal_layout)
        self.setCentralWidget(main)

    def setup_left(self, parent_layout, children_layout):
        left_layout = QVBoxLayout()
        for child in children_layout:
            left_layout.addLayout(child)
        parent_layout.addLayout(left_layout)
        
    def setup_top(self):
        top_layout = QVBoxLayout()
        self.web_view_top = QWebEngineView()
        self.current_index_top = 0
        self.period = self.params_prob["Period"]
        self.top_content = create_plot_html(self.data_prob, self.params_prob, "Metric", "Probability", self.period, self.current_index_top)
        self.web_view_top.setHtml(self.top_content)
        self.slider_top = QSlider(Qt.Horizontal)
        self.slider_top.setMinimum(0)
        self.slider_top.setMaximum(len(self.data_prob) // self.period - 1)
        self.slider_top.valueChanged.connect(self.slider_update_top)
        self.slider_label_top = QLabel("Layer 0")
        top_layout.addWidget(self.web_view_top)
        top_layout.addWidget(self.slider_label_top)
        top_layout.addWidget(self.slider_top)
        return top_layout
    
    def setup_right(self, parent_layout):
        right = QVBoxLayout()
        edges = load_edges("resources/graph.txt")
        html = build_visjs_html(edges)
        self.graph_view = QWebEngineView()
        self.graph_view.setHtml(html)
        right.addWidget(self.graph_view)
        self.canvas_view = QGraphicsView()
        self.canvas_scene = QGraphicsScene()
        self.canvas_canvas = QAOALayerCanvas(self.canvas_scene)
        self.canvas_canvas.draw_layers(5) # hardcode, fix later
        self.canvas_view.setScene(self.canvas_scene)
        right.addWidget(self.canvas_view)
        parent_layout.addLayout(right)

    def setup_bottom(self):
        bottom_layout = QVBoxLayout()
        self.web_view_bottom = QWebEngineView()
        self.current_index_bottom = 0
        self.period = self.params_prob["Period"]
        self.bottom_html = create_plot_html(self.data_phase, self.params_phase, "Metric", "Phase", self.period, self.current_index_bottom)
        self.web_view_bottom.setHtml(self.bottom_html)
        self.slider_bottom = QSlider(Qt.Horizontal)
        self.slider_bottom.setMinimum(0)
        self.slider_bottom.setMaximum(len(self.data_phase) // self.period - 1)
        self.slider_bottom.valueChanged.connect(self.slider_update_bottom)
        self.slider_label_bottom = QLabel("Layer 0")
        bottom_layout.addWidget(self.web_view_bottom)
        bottom_layout.addWidget(self.slider_label_bottom)
        bottom_layout.addWidget(self.slider_bottom)
        return bottom_layout

    def slider_update_top(self, value):
        self.slider_label_top.setText(f"Layer: {value}")
        start_index = value * self.period
        next_indices = [(start_index + i) % len(self.data_prob) for i in range(self.period)]
        new_y_values = [self.data_prob[idx]["Metric"] for idx in next_indices]
        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        self.web_view_top.page().runJavaScript(f"updateData({js_array});")
        self.canvas_canvas.update_arrow(value)


    def slider_update_bottom(self, value):
        self.slider_label_bottom.setText(f"Layer: {value}")
        start_index = value * self.period
        next_indices = [(start_index + i) % len(self.data_phase) for i in range(self.period)]
        new_y_values = [self.data_phase[idx]["Metric"] for idx in next_indices]
        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        self.web_view_bottom.page().runJavaScript(f"updateData({js_array});")
        self.canvas_canvas.update_arrow(value)
