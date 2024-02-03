from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QPixmap, QPainter, Qt, QPen
from PySide6.QtWidgets import QLabel
from filedialogs import open_file_dialog
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
import nibabel

from canvas import Canvas

class GUIWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.img = None
        self.drawingbox = None
        """Stały rozmiar tych Figure jest wazny, inaczej scrollowanie wyglada rough"""
        self.fig_left = Figure(figsize=(8, 6))
        self.fig_mid = Figure(figsize=(8, 6))
        self.fig_right = Figure(figsize=(8, 8))

        """Przyciski"""
        self.load = QtWidgets.QPushButton("Load Image")
        self.reset_left = QtWidgets.QPushButton('Reset')
        self.reset_mid = QtWidgets.QPushButton('Reset')
        self.reset_right = QtWidgets.QPushButton('Reset')
        self.draw_left = QtWidgets.QPushButton('Draw')
        self.draw_mid = QtWidgets.QPushButton('Draw')
        self.draw_right = QtWidgets.QPushButton('Draw')

        """Canvasy na których wyświetlany będzie skan"""
        self.canvas_left = Canvas(self.fig_left)
        self.canvas_mid = Canvas(self.fig_mid)
        self.canvas_right = Canvas(self.fig_right)
        self.toolbar_left = NavigationToolbar2QT(self.canvas_left, self)
        self.canvas_left.setToolbar(self.toolbar_left)
        self.toolbar_mid = NavigationToolbar2QT(self.canvas_mid, self)
        self.canvas_mid.setToolbar(self.toolbar_mid)
        self.toolbar_right = NavigationToolbar2QT(self.canvas_right, self)
        self.canvas_right.setToolbar(self.toolbar_right)


        """Slidery do przesuwania danej perspektywy skanu"""
        self.slider1 = QtWidgets.QSlider()
        self.slider1.setMinimum(0)
        self.slider1.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider1.valueChanged.connect(lambda: self.draw_plots(self.fig_left, "left"))
        self.slider2 = QtWidgets.QSlider()
        self.slider2.setMinimum(0)
        self.slider2.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider2.valueChanged.connect(lambda: self.draw_plots(self.fig_mid, "mid"))
        self.slider3 = QtWidgets.QSlider()
        self.slider3.setMinimum(0)
        self.slider3.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.slider3.valueChanged.connect(lambda: self.draw_plots(self.fig_right, "right"))

        """Layout w qt - doku jest spoko opisana taki trochę flexbox"""
        self.layout = QtWidgets.QVBoxLayout(self)
        self.buttons = QtWidgets.QHBoxLayout(self)
        self.buttons_left = QtWidgets.QHBoxLayout(self)
        self.buttons_left.addWidget(self.reset_left)
        self.buttons_left.addWidget(self.draw_left)
        self.buttons.addLayout(self.buttons_left)
        self.buttons_mid = QtWidgets.QHBoxLayout(self)
        self.buttons_mid.addWidget(self.reset_mid)
        self.buttons_mid.addWidget(self.draw_mid)
        self.buttons.addLayout(self.buttons_mid)
        self.buttons_right = QtWidgets.QHBoxLayout(self)
        self.buttons_right.addWidget(self.reset_right)
        self.buttons_right.addWidget(self.draw_right)
        self.buttons.addLayout(self.buttons_right)
        canvas_layout = QtWidgets.QHBoxLayout(self)
        canvas_layout.addWidget(self.canvas_left)
        canvas_layout.addWidget(self.canvas_mid)
        canvas_layout.addWidget(self.canvas_right)
        slider_layout = QtWidgets.QHBoxLayout(self)
        slider_layout.addWidget(self.slider1)
        slider_layout.addWidget(self.slider2)
        slider_layout.addWidget(self.slider3)
        self.layout.addWidget(self.load)
        self.layout.addLayout(self.buttons)
        self.layout.addLayout(canvas_layout)
        self.layout.addLayout(slider_layout)

        """Połączenia dla przycisków"""
        self.load.clicked.connect(self.load_scan)
        self.reset_left.clicked.connect(self.toolbar_left.home)
        self.reset_mid.clicked.connect(self.toolbar_mid.home)
        self.reset_right.clicked.connect(self.toolbar_right.home)
        self.draw_left.clicked.connect(self.canvas_left.drawToggle)
        self.draw_mid.clicked.connect(self.canvas_mid.drawToggle)
        self.draw_right.clicked.connect(self.canvas_right.drawToggle)


    """
    Ukradzione z dokumentacji nibabela
    """
    @QtCore.Slot()
    def draw_plots(self, fig: Figure, panel):
        if len(fig.axes) != 0:
            ax = fig.get_axes()[0]
            slice = None
            if panel == "left":
                slice = self.img[self.slider1.value(), :, :, 0]
            elif panel == "mid":
                slice = self.img[:, self.slider2.value(), :, 0]
            elif panel == "right":
                slice = self.img[:, :, self.slider3.value(), 0]
            ax.imshow(slice.T, cmap="gray", origin="lower")
            fig.canvas.draw()

    """
    Moim pomysłem było, żeby zrobić metodą zależną od self.canvas_left.drawing i tutaj rysować po czymś
    Problem polega na tym, że sposób w jaki ja to wywołuje wgl nic nie rysuje. Można by teoretycznie zrobić ten kod w tej metodzie
    Paint event i uzależnić ten kod od jakiś bool'i. ale i tak nie umiem dać do paintera czegoś na czym by mi to malował.
    Póki, co jak zerkniesz niżej do PaintEvent metody na dole to ona rysuje pod wszystkimi elementami, które się wyświetlają
    (guziki, canvasy etc.)
    """
    def draw_smthg(self):
        pen = QPen()
        pen.setWidth(777)

        painter = QPainter(self)
        painter.setPen(pen)
        painter.drawEllipse(15, 15, 200, 200)

    @QtCore.Slot()
    def load_scan(self):
        filepath = open_file_dialog()
        wrapped_img = nibabel.load(filepath)
        self.img = wrapped_img.get_fdata()
        self.drawingbox = QPixmap(filepath)
        self.fig_left.add_subplot(111)
        self.fig_mid.add_subplot(111)
        self.fig_right.add_subplot(111)
        self.slider1.setValue(int(self.img.shape[0] / 2))
        self.slider2.setValue(int(self.img.shape[1] / 2))
        self.slider3.setValue(int(self.img.shape[2] / 2))
        self.slider1.setMaximum(self.img.shape[0]-1)
        self.slider2.setMaximum(self.img.shape[1]-1)
        self.slider3.setMaximum(self.img.shape[2]-1)
        self.draw_plots(self.fig_left, "left")
        self.draw_plots(self.fig_mid, "mid")
        self.draw_plots(self.fig_right, "right")
        self.draw_smthg()


    """
    No to tak ta metoda na dole działała najlepiej, ale nwm czy można jej dać coś innego niż "self"
    https://doc.qt.io/qt-6/qpaintevent.html
    Tutaj niby można dać jej byle jaki "paintRegion", ale nwm jak się jak uzależnia od zmiennych, tak, żeby rysowanie np nie było
    cały czas włączone.
    Ale to jako jedyne mi cokolwiek narysowało.
    
    Edit:
    Uważam, że dobrym pomysłem byłoby nałożenie jakieś Pixmapy w miejsce w którym jest wyświetlane zdjęcie i rysowanie na niej
    Pozdrawiam, ja debil
    """
    def paintEvent(self, event):
        # drawing handling
        pen = QPen()
        pen.setWidth(7)

        # uploading img
        painter = QPainter(self) # jakbysmy wlozyli cos innego niz self tutaj to mogloby zadzialac, ale to cos musialoby byc przezroczyste i nad naszym skanem raka
        painter.setPen(pen)
        painter.drawLine(15, 15, 250, 0)
        self.canvas_left.paint()