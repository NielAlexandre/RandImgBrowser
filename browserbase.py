#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

from pathlib import Path

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class QImg(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setMinimumHeight(1)
        self.setMinimumWidth(1)
        self.resizeEvent = self.onResize
        self.unsort_zone = os.path.expanduser('~/Images')

    def onResize(self, event):
        if not hasattr(self, "pxm"):
            return
        self.set_img(self.img)

    def set_img(self, img):
        self.img = img
        self.pxm = QPixmap(img)
        self.setPixmap(self.pxm.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:

            #Adaptation of coordinate
            #self.pxm is the original image
            #self.lbl.pixmap() is the scaled image
            y_ratio = self.pixmap().height() / self.pxm.height()
            x_ratio = self.pixmap().width() / self.pxm.width()
            xoffset = (self.width() - self.pixmap().width()) / 2
            yoffset = (self.height() - self.pixmap().height()) / 2
            x1, y1 = (self.croping.x()-xoffset)//x_ratio, (self.croping.y()-yoffset)//y_ratio
            x2, y2 = (event.pos().x()-xoffset)//x_ratio, (event.pos().y()-yoffset)//y_ratio

            x, tx = (x1, x2) if x1 < x2 else (x2, x1)
            y, ty = (y1, y2) if y1 < y2 else (y2, y1)
            w = tx - x
            h = ty - y

            nimg = self.pxm.copy(x, y, w, h)

            oname = Path(self.img)
            nname = Path(self.unsort_zone, oname.stem + f"_{int(x)}-{int(y)}-{int(x+w)}-{int(y+h)}_cropped" + oname.suffix)
            nimg.save(str(nname))
            print("new file", nname)
            self.croping = None
            self.pause = False

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.pause = True
            self.croping = event.pos()

class BrowserBase(QMainWindow):
    EXTS = [".jpg", ".webp", ".jpeg", ".png", ".JPG", ".PNG", ".gif", ".jfif"]
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowState(Qt.WindowMaximized)
        self.setStyleSheet("background-color: #14191B;color: #F5E9E0")
        self.croping = None
        self.nxt_to = 10_000
        self.unsort_zone = os.path.expanduser('~/Images')
        self.title = list('.')

        #INIT IHM
        self.lbl = QImg()

        hl = self.hl = QVBoxLayout()
        hl.setSpacing(0)
        hl.setContentsMargins(0, 0, 0, 0)
        widget = QWidget()
        widget.setLayout(hl)
        self.setCentralWidget(widget)
        hl.addWidget(self.lbl)

        #Init Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.time_to_next)
        self.pause = False
        self.time_to_next()
        self.resizeEvent = self.onResize

    def onResize(self, event):
        pass

    def time_to_next(self):
        self.nxt_img()
        self.timer.start(self.nxt_to)

    def set_img(self, img):
        self.img = img
        self.lbl.set_img(self.img)
        self.update_title()

    def update_title(self):
        title = list('.') #Start title with a point to keep the process sitting in the task bar
        if self.pause:
            title.append("[P]")

        title.append(self.title)
        self.setWindowTitle(' '.join(title))

    @property
    def pause(self):
        return not self.timer.isActive()

    @pause.setter
    def pause(self, v):
        if v:
            self.timer.stop()
        else:
            self.timer.start(self.nxt_to)

    def nxt_img(self):
        raise NotImplemented

    def prv_img(self):
        raise NotImplemented

    def del_img(self):
        raise NotImplemented

    def srt_img(self):
        raise NotImplemented

    def inv_pause(self):
        self.pause = not self.pause

    def keyPressEvent(self, event, menu={}):
        _menu = {Qt.Key_Right: self.nxt_img,
                Qt.Key_Left: self.prv_img,
                Qt.Key_Space: self.inv_pause,
                Qt.Key_Delete: self.del_img,
                Qt.Key_S: self.srt_img}
        _menu.update(menu)
        try:
            _menu[event.key()]()
        except KeyError:
            pass
        self.update_title()

