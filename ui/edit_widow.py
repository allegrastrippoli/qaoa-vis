from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel

class LayerEditDialog(QDialog):
    def __init__(self, params):
        super().__init__()
        self.setWindowTitle("Edit γ and β")
        self.params = params
        self.entries = []
        layout = QVBoxLayout()

        for param in params["Fixed parameters"]:
            row = QHBoxLayout()
            gEdit = QLineEdit(str(param))
            bEdit = QLineEdit(str(param))
            row.addWidget(QLabel("γ:"))
            row.addWidget(gEdit)
            row.addWidget(QLabel("β:"))
            row.addWidget(bEdit)
            layout.addLayout(row)
            self.entries.append((gEdit, bEdit))

        add_button = QPushButton("Add Run")
        add_button.clicked.connect(self.add_layer_row)
        layout.addWidget(add_button)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        layout.addWidget(save_button)

        self.setLayout(layout)

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
