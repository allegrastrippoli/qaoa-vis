from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel

class LayerInitDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Init QAOA Run")
        self.num_layers = 0
        self.entries = []
        layout = QVBoxLayout()

        add_button = QPushButton("Add Run")
        add_button.clicked.connect(self.add_layer_row)
        layout.addWidget(add_button)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        layout.addWidget(save_button)

        self.setLayout(layout)
        
    def add_layer_init_row(self):
        row = QHBoxLayout()
        lEdit = QLineEdit("0")
        row.addWidget(QLabel("Number of layers:"))
        row.addWidget(lEdit)
        self.layout().insertLayout(self.layout().count() - 2, row)
        self.num_layers = lEdit
        
    def add_layer_row(self):
        row = QHBoxLayout()
        gEdit = QLineEdit("0.0")
        bEdit = QLineEdit("0.0")
        row.addWidget(QLabel("γ:"))
        row.addWidget(gEdit)
        row.addWidget(QLabel("β:"))
        row.addWidget(bEdit)
        self.layout().insertLayout(self.layout().count() - 2, row)
        self.entries.append((gEdit, bEdit))

    def get_values(self):
        return [(float(g.text()), float(b.text())) for g, b in self.entries]

    def get_number_of_layers(self):
        return int(self.num_layers.text())
