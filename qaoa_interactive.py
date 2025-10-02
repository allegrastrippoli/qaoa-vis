import sys
import numpy as np
import plotly.graph_objects as go
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import Qt

# ---- Generate Plotly Figure ----
x = np.linspace(0, 10, 1000)
frequencies = [0.5, 1.0, 2.0, 3.0]

fig = go.Figure()
for freq in frequencies:
    fig.add_trace(go.Scatter(x=x, y=np.sin(freq * x), name=f'freq={freq}'))

fig.update_layout(title="Sine Waves with Different Frequencies")

# Convert to HTML for embedding
html = fig.to_html(include_plotlyjs='cdn')

# ---- PyQt Application ----
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive QAOA")
        self.setGeometry(100, 100, 1200, 600)

        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)

        # --- Left: Plotly Chart with Checkboxes ---
        chart_layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        self.web_view.setHtml(html)

        # Checkboxes for filtering traces
        # self.checkboxes = []
        # for i, freq in enumerate(frequencies):
        #     cb = QCheckBox(f"freq={freq}")
        #     cb.setChecked(True)
        #     cb.stateChanged.connect(self.update_chart)
        #     self.checkboxes.append(cb)
        #     chart_layout.addWidget(cb)

        chart_layout.addWidget(self.web_view)
        layout.addLayout(chart_layout)

        # --- Right: Canvas for Drawing ---
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(self.view.renderHints())

        # Draw some simple shapes
        # pen = QPen(Qt.black, 2)
        
        def add_node(scene, x, y, radius=10, color="black"):
            ellipse = scene.addEllipse(x-radius, y-radius, 2*radius, 2*radius)
            ellipse.setBrush(QBrush(QColor(color)))
            ellipse.setPen(QPen(Qt.black, 2))
            # ellipse.setFlag(ellipse.ItemIsMovable, True)
            # ellipse.setFlag(ellipse.ItemIsSelectable, True)
            scene.addItem(ellipse)
            return ellipse
        
        def add_edge(scene, node1, node2):
            x1 = node1.rect().x() + node1.rect().width()/2 + node1.pos().x()
            y1 = node1.rect().y() + node1.rect().height()/2 + node1.pos().y()
            x2 = node2.rect().x() + node2.rect().width()/2 + node2.pos().x()
            y2 = node2.rect().y() + node2.rect().height()/2 + node2.pos().y()

            line = scene.addLine(x1, y1, x2, y2)
            line.setPen(QPen(Qt.black, 2))
            scene.addItem(line)
            return line
        
        node1 = add_node(self.scene, 100, 100)
        node2 = add_node(self.scene, 300, 200)
        node3 = add_node(self.scene, 200, 300)

        edge1 = add_edge(self.scene, node1, node2)
        edge2 = add_edge(self.scene, node2, node3)
        edge3 = add_edge(self.scene, node3, node1)
        
        group = self.scene.createItemGroup([node1, node2, node3, edge1, edge2, edge3])
        group.setFlag(group.ItemIsMovable, True)

        
        # for item in self.scene.items():
        #     item.setFlag(item.ItemIsMovable, True)
        #     item.setFlag(item.ItemIsSelectable, True)
    
        # Mouse event tracking
        # self.view.setMouseTracking(True)
        # self.view.viewport().installEventFilter(self)

        layout.addWidget(self.view)

        self.setCentralWidget(main_widget)

    # def update_chart(self):
    #     """Update Plotly chart visibility based on checkboxes."""
    #     visibility = [cb.isChecked() for cb in self.checkboxes]
    #     new_fig = go.Figure()
    #     for i, freq in enumerate(frequencies):
    #         if visibility[i]:
    #             new_fig.add_trace(go.Scatter(x=x, y=np.sin(freq * x), name=f'freq={freq}'))
    #     new_fig.update_layout(title="Filtered Sine Waves")
    #     self.web_view.setHtml(new_fig.to_html(include_plotlyjs='cdn'))

    def eventFilter(self, source, event):
        if source is self.view.viewport() and event.type() == event.MouseButtonPress:
            pos = event.pos()
            self.scene.addEllipse(pos.x(), pos.y(), 5, 5, QPen(Qt.red), QBrush(Qt.red))
        return super().eventFilter(source, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
