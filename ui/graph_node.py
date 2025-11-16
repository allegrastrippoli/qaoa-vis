from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import Qt

class GraphNode(QGraphicsEllipseItem):
    def __init__(self, node_id, x, y, r=20, color="white"):
        super().__init__(-r, -r, 2*r, 2*r)
        self.node_id = node_id
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.black, 2))
        self.setZValue(200)
        self.setFlag(self.ItemIsMovable)
        self.setFlag(self.ItemIsSelectable)
        self.label = QGraphicsTextItem(str(node_id), parent=self)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setPos(-r/2, -r/2)
        self.label.setZValue(300)
