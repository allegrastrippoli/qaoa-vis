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
        main_layout = QVBoxLayout(main)

        init_button = QPushButton("Init")
        init_button.clicked.connect(self.open_init_dialog)
        main_layout.addWidget(init_button)

        self.prob_layout, self.prob_view = self.setup_linecharts()
        self.phase_layout, self.phase_view = self.setup_linecharts()

        main_layout.addLayout(self.prob_layout)
        main_layout.addLayout(self.phase_layout)

        self.setCentralWidget(main)


    def setup_parent_children_layout(self, parent_layout, children_layout):
        for child in children_layout:
            parent_layout.addLayout(child)
        
    def setup_linecharts(self):
        layout = QVBoxLayout()
        web_view = QWebEngineView()
        web_view.setHtml(create_init_html())   
        layout.addWidget(web_view)
        return layout, web_view

    
    # write_values(path="resources/prova.json", n_snapshots=2, y_range=y_range, fixed_params=params, states=states, metric_dict=all_probs)
    def open_init_dialog(self):
        key_offset = 0
        all_probs, all_phases = {}, {}

        dialog = LayerInitDialog()
        dialog.add_layer_init_row()
        dialog.add_layer_row()

        if dialog.exec_() != QDialog.Accepted:
            return

        params = dialog.get_values()
        num_layers = dialog.get_number_of_layers()
        num_runs = len(params)

        for (gamma, beta) in params:
            same_param_for_each_layer = [[gamma] * num_layers, [beta] * num_layers]

            qaoa = QAOAMaxCut(
                graph=[(0,1),(1,2),(2,3),(3,0)],
                num_layers=num_layers,
                params=same_param_for_each_layer
            )
            snaps = qaoa.run()
            dp = DataProcessor(snaps)

            probs, phases = dp.get_values_from_snaps()
            n_snapshots = len(probs)

            for k, v in probs.items():
                all_probs[key_offset + k] = v
            for k, v in phases.items():
                all_phases[key_offset + k] = v

            key_offset += n_snapshots

        self.update_plot(
            metric_dict=all_probs,
            title="Probability",
            web_view=self.prob_view,
            layout=self.prob_layout,
            params=params,
            num_layers=num_layers
        )

        self.update_plot(
            metric_dict=all_phases,
            title="Phase",
            web_view=self.phase_view,
            layout=self.phase_layout,
            params=params,
            num_layers=num_layers
        )
        
        
    def update_plot(self, metric_dict, title, web_view, layout, params, num_layers):
        dp = DataProcessor({})  

        y_range = dp.get_y_range(metric_dict)
        data_per_layer = dp.get_data_per_layer(
            states=states,
            metric_dict=metric_dict,
            n_snapshots=num_layers * 2
        )

        html_content = create_plot_html(
            states=states,
            data=data_per_layer,
            params=params,
            y_range=y_range,
            num_runs=len(params),
            title=title
        )
        web_view.setHtml(html_content)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(num_layers * 2 - 1)

        label = QLabel(f"{title} Layer 0")

        h = QHBoxLayout()
        h.addWidget(label)
        h.addWidget(slider)
        layout.addLayout(h)

        slider.valueChanged.connect(
            partial(
                self.slider_update,
                data=data_per_layer,
                slider_label=label,
                web_view=web_view
            )
        )


    def slider_update(self, value, data, slider_label, web_view) -> None:
        slider_label.setText(f"Layer: {value}")
        new_y_values = data[value]
        js_array = "[" + ",".join(str(y) for y in new_y_values) + "]"
        web_view.page().runJavaScript(f"updateData({js_array});")
        
    # def open_edit_dialog(self, params, web_view, data):
    #     pass
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
