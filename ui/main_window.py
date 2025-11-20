from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QGraphicsView, QGraphicsScene, QPushButton, QDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ui.html_plot import build_visjs_html, create_plot_html, create_init_html
from data.loader import load_json, load_edges, write_values
from ui.edit_widow import LayerEditDialog
from ui.init_window import LayerInitDialog
from ui.graph_canvas import QAOALayerCanvas
from functools import partial
from qaoa.qaoa import QAOAMaxCut
from PyQt5.QtCore import Qt
from qaoa.data_processor import DataProcessor

states = [
            "0000",
            "0001",
            "0010",
            "0011",
            "0100",
            "0101",
            "0110",
            "0111",
            "1000",
            "1001",
            "1010",
            "1011",
            "1100",
            "1101",
            "1110",
            "1111"
        ]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive QAOA")
        self.params_prob, self.data_prob = None, None
        with open("resources/styles.qss", "r") as f:
            self.setStyleSheet(f.read())
        self.setup_ui()

    def setup_ui(self):
        main = QWidget()
        horizontal_layout = QHBoxLayout(main)     
        top_layout = self.setup_linecharts()
        # bottom_layout = self.setup_linecharts(metric="Phase", data=self.data_phase, params=self.params_phase)
        self.setup_parent_children_layout(horizontal_layout, [top_layout])
        self.setCentralWidget(main)

    def setup_parent_children_layout(self, parent_layout, children_layout):
        for child in children_layout:
            parent_layout.addLayout(child)
        
    def setup_linecharts(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        web_view = QWebEngineView()
        init_html = create_init_html()
        web_view.setHtml(init_html)
        init_button = QPushButton("Init")
        init_button.clicked.connect( partial(self.open_init_dialog,web_view=web_view, layout=layout))
        h = QHBoxLayout()
        h.addWidget(init_button)
        h.addWidget(init_button)
        layout.addLayout(h)
        layout.addWidget(web_view)
        return layout
    
    def open_init_dialog(self, web_view, layout):
        key_offset = 0
        all_probs, all_phases = {}, {}
        dialog = LayerInitDialog()
        dialog.add_layer_init_row()
        dialog.add_layer_row()
        if dialog.exec_() == QDialog.Accepted:
            params = dialog.get_values()
            num_layers = dialog.get_number_of_layers()
            fixed_params = [[gamma for (gamma, _) in params], [beta for (_, beta) in params]]
            for (gamma, beta) in params:
                same_param_for_each_layer = [[gamma] * num_layers, [beta] * num_layers]
                qaoa = QAOAMaxCut(graph=[(0,1),(1,2),(2,3),(3,0)], num_layers=num_layers, params=same_param_for_each_layer)
                snaps = qaoa.run() 
                dp = DataProcessor(snaps)
                probs, phases = dp.get_values_from_snaps()
                
                n_snapshots = len(probs)
                for k, v in probs.items():
                    all_probs[key_offset + k] = v
                for k, v in phases.items():
                    all_phases[key_offset + k] = v
                key_offset += n_snapshots
            write_values(path="resources/prova.json", n_snapshots=2, y_range=[0,1], fixed_params=fixed_params, states=states, metric_dict=all_probs)
            (self.params_prob, self.data_prob) = load_json("resources/prova.json")
            current_index = 0
            num_runs = self.params_prob["Number of runs"]
            html_content = create_plot_html(self.data_prob, self.params_prob, "Metric", "Probability", num_runs, current_index)
            web_view.setHtml(html_content)
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(len(self.data_prob) // num_runs - 1)
            slider_label = QLabel("Layer 0")
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(
                partial(self.open_edit_dialog, params=self.params_prob, web_view=web_view, data=self.data_prob)
            )
            h = QHBoxLayout()
            h.addWidget(slider_label)
            h.addWidget(slider)
            h.addWidget(edit_button)
            h.addStretch()
            layout.addLayout(h)
            slider.valueChanged.connect(partial(self.slider_update, data=self.data_prob, slider_label=slider_label, period=num_runs, web_view=web_view))
            layout.addWidget(web_view)
            layout.addWidget(slider_label)
            layout.addWidget(slider)
                
    def slider_update(self, value, data, slider_label, period, web_view) -> None:
        slider_label.setText(f"Layer: {value}")
        start_index = value * period
        next_indices = [(start_index + i) % len(data) for i in range(period)]
        new_y_values = [data[idx]["Metric"] for idx in next_indices]
        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        web_view.page().runJavaScript(f"updateData({js_array});")
        
    def open_edit_dialog(self, params, web_view, data):
        pass
    #     dialog = LayerEditDialog(params)
    #     if dialog.exec_():
    #         new_values = dialog.get_values()
    #         params["Fixed parameters"] = new_values
    #         print(new_values)
    #         params["Period"] = len(new_values)
    #         # run qaoa here
    #         # write values on file
    #         # create plot html
    #         updated_html = create_plot_html(
    #             data, params, "Metric",
    #             "Updated",  
    #             params["Period"], 0
    #         )
    #         web_view.setHtml(updated_html)
