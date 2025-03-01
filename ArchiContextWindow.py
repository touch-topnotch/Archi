import FreeCADGui
import FreeCAD
# For FreeCAD macros, normally you already have a QApplication running,
# so you often don't need to create another QApplication. 
# But for clarity, we include it here in case you're testing outside or as a snippet.
from PySide2.QtCore import Qt,  QTimer,  QThread, QMetaObject, Slot
from PySide2.QtGui import (QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                          QPushButton, QSlider, QLineEdit, QDoubleSpinBox,
                          QGroupBox, QFormLayout, QScrollArea, QApplication, QDockWidget,
                          QFileDialog, QPixmap, QPainter, QPainterPath, QGridLayout,
                          QSizePolicy)
from PySide2 import QtCore
from pivy.coin import SoSeparator
from pivy.coin import SoCube, SoTranslation, SoRenderManager, SoDB, SoInput
from pivy.quarter import QuarterWidget
# from OpenGL.GL import *
# from OpenGL.GLU import *

from collections import OrderedDict

# If running as a macro in FreeCAD, you can comment out the next lines:
# app = QApplication.instance()
# if not app:
#     app = QApplication(sys.argv)
print("start")
class ImageStyle:
    def __init__(self, number_of_cols, gap, QLabel, QWidget):
        self.number_of_cols = number_of_cols
        self.gap = gap
        self.main_layout = QLabel
        self.parent_class = QWidget

class ImageData:
    def __init__(self, label_text, button_text, imageStyle:ImageStyle, height=200):
        self.imageStyle = imageStyle
        self.heights = [0 for i in range(imageStyle.number_of_cols)]
        self.height_by_id = [0 for i in range(imageStyle.number_of_cols)]

          # --- Subheader: Sketches ---
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.imageStyle.main_layout.addWidget(label)
        content = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(content)
        scroll_area.setMaximumHeight(height)

        # Create a horizontal layout to hold the vertical layouts
        horizontal_layout = QHBoxLayout(content)
        horizontal_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(self.imageStyle.gap)
    
        self.vlayouts = []
        for _ in range(self.imageStyle.number_of_cols):
            vlayout = QVBoxLayout()
            vlayout.setAlignment(Qt.AlignTop)
            vlayout.setSpacing(self.imageStyle.gap)
            self.vlayouts.append(vlayout)
            horizontal_layout.addLayout(vlayout)

        horizontal_layout.setSpacing(self.imageStyle.gap)
        content.setLayout(horizontal_layout)
        self.imageStyle.main_layout.addWidget(scroll_area)
        
   
        add_button = QPushButton(button_text)
        add_button.clicked.connect(self.select_and_add_images)

        # Here you could dynamically add thumbnail widgets of sketches
        self.imageStyle.main_layout.addWidget(add_button)

    def select_and_add_images(self):
        """
        Open a file dialog to let the user pick one or more image files.
        Then create thumbnails and add them to the sketches_layout.
        """
        # Open file dialog. On macOS, this will use the native Finder dialog.
        file_names, _ = QFileDialog.getOpenFileNames(
            self.imageStyle.parent_class, 
            "Select one or more images", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not file_names:
            return  # user canceled
        images = []
        for file_name in file_names:
            # Create a label for the image
            img_label = QLabel()
            pixmap = QPixmap(file_name)
            # Enforce a fixed width of 120 px, keeping aspect ratio for optimal height
            target_width = 200
            scale_factor = target_width / pixmap.width()
            target_height = int(pixmap.height() * scale_factor)
            pixmap = pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Round corners by 5 px
            rounded = QPixmap(pixmap.size())
            rounded.fill(Qt.transparent)

            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            path = QPainterPath()
            path.addRoundedRect(0, 0, target_width, target_height, 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            pixmap = rounded
            img_label.setPixmap(pixmap)
            img_label.setToolTip(file_name)  # show path on hover (optional)

            images.append(img_label)
            print(self.heights)
            y = self.heights.index(min(self.heights))
            
            self.vlayouts[y].insertWidget(0, img_label)

    
            self.heights[y] += pixmap.height() + self.imageStyle.gap
        return images
    
class MdiQuarterWidget(QuarterWidget):
    def __init__(self, parent, sharewidget):
        QuarterWidget.__init__(self, parent=parent, sharewidget=sharewidget)
    
    def minimumSizeHint(self):
        return QtCore.QSize(640, 480)

class MiniView3D(QWidget):
    def __init__(self, parent=None):
        super(MiniView3D, self).__init__(parent)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Ensure scene is created in the correct thread using invokeMethod
        QTimer.singleShot(100, lambda: QMetaObject.invokeMethod(self, "init_scene", Qt.QueuedConnection))

    @Slot()  # This registers the function as a Qt slot
    def init_scene(self):
        print("Initializing 3D Scene...")

        if QThread.currentThread() != QApplication.instance().thread():
            print("ERROR: init_scene() is running in the wrong thread!")
            return

        from pivy.coin import SoSeparator, SoCube, SoTranslation
        from pivy.quarter import QuarterWidget

        self.scene_root = SoSeparator()  # Store reference
        trans = SoTranslation()
        trans.translation.setValue(0, 0, 0)
        self.scene_root.addChild(trans)

        cube = SoCube()
        self.scene_root.addChild(cube)

        self.quarter_widget = MdiQuarterWidget(self)  # Store reference

        layout = QVBoxLayout(self)
        layout.addWidget(self.quarter_widget)
        self.setLayout(layout)

        self.quarter_widget.setSceneGraph(self.scene_root)
        print("SceneGraph successfully attached to QuarterWidget!")
class ArchiContextWindow(QDockWidget):
    
    def __init__(self, parent=None):

        super(ArchiContextWindow, self).__init__(parent)
        self.setWindowTitle("Project Context")

        central_widget = QWidget()
        self.setWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        image_style = ImageStyle(
            3,
            10,
            main_layout,
            self
        )
        # --- Header ---
        header_label = QLabel("Project Context")
        header_label.setStyleSheet("font-size: 18pt; font-weight: bold;")

        main_layout.addWidget(header_label)
        self.sketches = ImageData("Sketches", "Add Sketches", image_style)
        self.environment = ImageData("AI Generations", "Generate More", image_style)

        # --- Subheader: Parameters ---
        params_label = QLabel("Parameters")
        params_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(params_label)

        params_group = QGroupBox()
        form_layout = QFormLayout(params_group)

        # 1) Height (editable float)
        height_spin = QDoubleSpinBox()
        height_spin.setRange(0.0, 10000.0)
        height_spin.setValue(1.5)  # example default
        form_layout.addRow("Height (m):", height_spin)

        # 2) Realism (slider from 0..100 to represent 0..1)
        realism_slider = QSlider(Qt.Horizontal)
        realism_slider.setRange(0, 100)
        realism_slider.setValue(50)  # mid
        form_layout.addRow("Realism:", realism_slider)

        # 3) Other (text field)
        other_edit = QLineEdit()
        form_layout.addRow("Other:", other_edit)

        main_layout.addWidget(params_group)

        # --- Subheader: Visualization ---
        viz_label = QLabel("Visualization")
        viz_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(viz_label)

        # Instead of a QGLWidget/QOpenGLWidget, just put a placeholder:
        self.vis = ImageData("AI 3D Concept", "Render", image_style, 400)
        # self.mini_view = MiniView3D(self)
        # main_layout.addWidget(self.mini_view)
        # self.resize(500, 600)


def run_archi_context():
    """
    In a FreeCAD macro, you can call this to show the custom window.
    """

    mw = FreeCADGui.getMainWindow()
    left_dock_widgets = mw.findChildren(QDockWidget)
    for widget in left_dock_widgets:
        if widget.windowTitle() == "Combo View":
            mw.tabifyDockWidget(widget, dock_widget)
            break
    dock_widget = ArchiContextWindow(mw)
    mw.addDockWidget(Qt.RightDockWidgetArea, dock_widget)
    dock_widget.show()
    return dock_widget  # Keep a reference so it's not garbage-collected

mw = FreeCADGui.getMainWindow()
dock_widgets = mw.findChildren(QDockWidget)
for widget in dock_widgets:
    if widget.windowTitle() == "Project Context":
        widget.close()
        break
ai_w = run_archi_context()
# For direct testing outside FreeCAD:
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     w = MainWindow()
#     w.show()
#     sys.exit(app.exec_())