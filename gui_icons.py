from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, QSize, QRect
import os
import base64

# Base64 encoded application icon - this is a simple database icon
ICON_DATA = """
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
AAAASUVORK5CYII=
"""

CHART_ICON_DATA = """
iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAD+ElEQVR4nO2bTUhUURTHf3f8
HMemUZNmcJQ+pAxatAgiaBE0QkaLFkGbi6BFbdoEQUSLNi2iCMIWfUBEixZBBC2CiAAX1aJVtChaVOJHpTM1czrunRbzZt6bN2/u
981E84fD3Lnn3Hve/55z33v33hkIBAIBAaBSKgKoAo4CZ4EjwF6gBagE0sAi8AV4DzwFHgOjwAKQAzK5XI5yuXyuH1ZJgGPADeAc
4C/wWA54BlwHnotsZXn4KpXKPqAbeAn8cgikFV+B+8BeIFxZWRkMVPATgK/Ai8LmLrAPmAIagRlgC5gFNoFV4E9em3xeR35rA+p1
vZrC5l7VnRaZT8BJYALwlUvrxccHwBJwBggVaQ+wDYwAzUAt0AL8Qb26qk8DcAiYBL6xtZZ4cQHoBaqllKSUaK2RUhYUAMkn8nml
lH6KKhMAaIpPcSI9rHXL+pNSqtSUNU8UEbFQDVw0xYyIKYzFYjiRSkrZCbQBM+l0Op9S7QE9PsZMsdlsllQqRTKZJJFIEI/HOdYe
55QvRTKZ5FH3MJ9nJmhpaeHO9ev0DA7Q29fH8toaHYeP0BwOoZSivr6efbEYBw8coL29HZ/Px/r6OhsbG/uBWS3EfSE2ORRdnEhP
TwT45Utz0t9PbzCIPxAgnU6zkkqxkUxydWKcloYow8PDvL3Xw81b/TQEg6yuruLz+YhEIrS1tbGwsMDm5ubfFNBKeaaBKRJ2yZ6u
kkqieCIRDvv9hOvqCIVChEIhwiLCi4YG1kVEIsJoPM6XxUWECBMKhYhGo0QiEaLRKMFgENvKcVyIPRdhynVzEQvFYjfaVuhJPq+1
9ryaWK+AnXIRLYRUitXVVeYXFhBCICIEAgH+/t5ie2aGN1NT15YTa1eTyZQSQmittUN6lO1iIURXLvcasEsBrZXWK7S2tvJxepq5
uTlCoRCdnZ0MDPTS0tRES1MT56+MbOs/0hsj5/OR9BWZAju2Pd6Dd214C7HbSCXdi9C7uQgXgjsxA+wWYsehTfljgN2Itou8BYQD
u4XYSbEEcPr0Xi7i5jHYhbRcRCNJJpNsba24f65d3L6E2M5FcmSzWZRSruQiHqtANpulmIuw2z7PPzDOlp9xLQ7k83mUUl4foLBI
u/lFymkhuRdzsJjsW0DY8K0GLrJ9kBI2nyfQWqOUKvVViE81MAXCwnoFnHSRUpuzugqUkoGS7QEopSi3PcBuD7BbhHY5Bjgd+Xo2
BrgRoWtNryvAzQlOKXJW3avnodB1F7GqiJ2JSx0D3IrQk0LstRBbVcSrM4FiVcQLIXbTRdyK0HUhLjUDnB6vToPdngi5GQOcCLGb
MaDcs0A3M8CtiLLHgGL/c5iYmBg1Xj+glDoFnACOo/825yjqb3NagR1/m7MJrACLiUTi1n+qDAzWjVd6qQAAAABJRU5ErkJggg==
"""

DATABASE_ICON_DATA = """
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
"""

def create_icon_from_base64(data, size=(32, 32)):
    """Create a QIcon from base64 encoded data"""
    pixmap = QPixmap()
    pixmap.loadFromData(base64.b64decode(data))
    if size != pixmap.size():
        pixmap = pixmap.scaled(QSize(*size), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return QIcon(pixmap)

def get_app_icon():
    """Get the main application icon"""
    return create_icon_from_base64(ICON_DATA)

def get_chart_icon():
    """Get the chart icon for visualization"""
    return create_icon_from_base64(CHART_ICON_DATA)

def get_database_icon():
    """Get the database icon for database connections"""
    return create_icon_from_base64(DATABASE_ICON_DATA)

def create_icon_file():
    """Create a temporary icon file and return the path"""
    temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_icon.png')
    try:
        with open(temp_path, 'wb') as f:
            f.write(base64.b64decode(ICON_DATA))
        return temp_path
    except:
        return None

def draw_index_icon(size=32, bg_color="#0078d7", fg_color="#ffffff", with_magnify=True):
    """Create a custom index icon"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw database cylinder
    painter.setBrush(QBrush(QColor(bg_color)))
    painter.setPen(QPen(QColor(fg_color), 1))
    
    # Draw cylinder body
    rect = QRect(size//8, size//4, size*6//8, size//2)
    painter.drawRect(rect)
    
    # Draw cylinder top
    top_rect = QRect(size//8, size//8, size*6//8, size//8)
    painter.drawEllipse(top_rect)
    
    # Draw cylinder bottom
    bottom_rect = QRect(size//8, size*5//8, size*6//8, size//8)
    painter.drawEllipse(bottom_rect)
    
    # Draw index lines
    line_color = QColor(fg_color)
    painter.setPen(QPen(line_color, 2))
    
    # Draw 3 lines representing an index
    line_y = size*3//8
    for i in range(3):
        painter.drawLine(size//4, line_y, size*3//4, line_y)
        line_y += size//8
    
    # Draw magnifying glass if requested
    if with_magnify:
        painter.setPen(QPen(QColor(fg_color), 2))
        painter.setBrush(Qt.NoBrush)
        glass_x = size*5//8
        glass_y = size*5//8
        glass_size = size//3
        painter.drawEllipse(QRect(glass_x, glass_y, glass_size, glass_size))
        
        # Handle
        handle_start_x = glass_x + glass_size*3//4
        handle_start_y = glass_y + glass_size*3//4
        handle_end_x = handle_start_x + size//6
        handle_end_y = handle_start_y + size//6
        painter.drawLine(handle_start_x, handle_start_y, handle_end_x, handle_end_y)
    
    painter.end()
    return QIcon(pixmap)