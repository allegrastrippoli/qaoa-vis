from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QGraphicsView, QGraphicsScene, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ui.html_plot import build_visjs_html, create_plot_html
from data.loader import load_json, load_edges
from ui.edit_widow import LayerEditDialog
from ui.graph_canvas import QAOALayerCanvas
from functools import partial
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive QAOA")
        (self.params_prob, self.data_prob) = load_json("resources/charts/state_probability_aggregate/state_probability_aggregate.json")
        (self.params_phase, self.data_phase) = load_json("resources/charts/state_phase_aggregate/state_phase_aggregate.json")
        with open("resources/styles.qss", "r") as f:
            self.setStyleSheet(f.read())
        self.setup_ui()

    def setup_ui(self):
        main = QWidget()
        horizontal_layout = QHBoxLayout(main)     
        top_layout = self.setup_linecharts(metric="Probability", data=self.data_prob, params=self.params_prob)
        bottom_layout = self.setup_linecharts(metric="Phase", data=self.data_phase, params=self.params_phase)
        self.setup_parent_children_layout(horizontal_layout, [top_layout, bottom_layout])
        self.setCentralWidget(main)

    def setup_parent_children_layout(self, parent_layout, children_layout):
        for child in children_layout:
            parent_layout.addLayout(child)
        
    def setup_linecharts(self, metric, data, params) -> QVBoxLayout:
        layout = QVBoxLayout()
        web_view = QWebEngineView()
        current_index = 0
        period = params["Period"]
        html_content = create_plot_html(data, params, "Metric", metric, period, current_index)
        web_view.setHtml(html_content)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(len(data) // period - 1)
        slider_label = QLabel("Layer 0")
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(
            partial(self.open_edit_dialog, params=params, web_view=web_view, data=data)
        )
        h = QHBoxLayout()
        h.addWidget(slider_label)
        h.addWidget(slider)
        h.addWidget(edit_button)
        h.addStretch()
        layout.addLayout(h)
        slider.valueChanged.connect(partial(self.slider_update, data=data, slider_label=slider_label, period=period, web_view=web_view))
        layout.addWidget(web_view)
        layout.addWidget(slider_label)
        layout.addWidget(slider)
        return layout

    def open_edit_dialog(self, params, web_view, data):
        dialog = LayerEditDialog(params)
        if dialog.exec_():
            new_values = dialog.get_values()
            params["Fixed parameters"] = new_values
            print(new_values)
            params["Period"] = len(new_values)
            # run qaoa here
            # write values on file
            # create plot html
            updated_html = create_plot_html(
                data, params, "Metric",
                "Updated",  
                params["Period"], 0
            )
            web_view.setHtml(updated_html)

    def slider_update(self, value, data, slider_label, period, web_view) -> None:
        slider_label.setText(f"Layer: {value}")
        start_index = value * period
        next_indices = [(start_index + i) % len(data) for i in range(period)]
        new_y_values = [data[idx]["Metric"] for idx in next_indices]
        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        web_view.page().runJavaScript(f"updateData({js_array});")
