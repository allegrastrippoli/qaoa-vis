from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtCore import Qt

class QAOALayerCanvas:
    def __init__(self, scene):
        self.canvas_scene = scene
        self.squares = []
        self.arrow_line = None
        self.arrow_head = None

    def draw_layers(self, num_layers):
        self.canvas_scene.clear()
        square_size = 80
        spacing = 30
        start_x = 50
        y = 100

        self.squares = []  
        
        cost_mixer_labels = ['C', 'M']
        gamma_beta = ['γ', 'β']
        idx = -1

        total_width = num_layers * square_size + (num_layers - 1) * spacing
        line_y = y + square_size / 2  
        line_start_x = start_x - spacing / 2
        line_end_x = start_x + total_width - square_size + spacing / 2

        base_line = self.canvas_scene.addLine(
            line_start_x, line_y, line_end_x, line_y,
            QPen(Qt.darkGray, 2, Qt.SolidLine)
        )
        base_line.setZValue(50)  

        for i in range(num_layers):
            x = start_x + i * (square_size + spacing)
            rect_item = self.canvas_scene.addRect(
                x, y, square_size, square_size,
                QPen(Qt.black, 2),
                QBrush(Qt.lightGray)
            )
            rect_item.setZValue(100) 

            if i % 2 == 0:
                idx += 1

            label_html = (
                f"<span style='font-size:16px;'>&#770;U<sub>{cost_mixer_labels[i%2]}</sub>"
                f"({gamma_beta[i%2]}<sub>{idx}</sub>)</span>"
            )
            label = self.canvas_scene.addText("")
            label.setHtml(label_html)
            label.setDefaultTextColor(Qt.black)

            text_rect = label.boundingRect()
            label.setPos(
                x + (square_size - text_rect.width()) / 2,
                y + (square_size - text_rect.height()) / 2
            )
            label.setZValue(150)

            self.squares.append(rect_item)

        self.arrow_line = self.canvas_scene.addLine(0, 0, 0, 0, QPen(Qt.red, 3))
        self.arrow_line.setZValue(200)

        self.arrow_head = self.canvas_scene.addPolygon(
            QtGui.QPolygonF(),
            QPen(Qt.red, 3),
            QBrush(Qt.red)
        )
        self.arrow_head.setZValue(200)

        self.update_arrow(0)

    def update_arrow(self, layer_index):
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
        # self.canvas_view.viewport().update()
