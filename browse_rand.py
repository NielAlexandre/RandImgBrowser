#!/usr/bin/python3

import sys, re, os
from glob import glob
from time import time
from copy import copy
from pathlib import Path

from random import *

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from browserbase import BrowserBase


def safe_move(orig, dest_path, copy=False):
    """
    Move orig file to dest_path directory
    File will be renamed with "_<nb>" whit nb incrementing
    until dest file doesn't already exists or dest file has the same md5sum
    If Copy = True, file won't be erased after copy
    """
    assert os.path.isfile(orig), f"first argument ({orig}) must be a file"
    assert os.path.isdir(dest_path), f"second argument ({dest_path}) must be a directory"
    fn = ofn = os.path.basename(orig)
    dest = os.path.join(dest_path, fn)
    ext = ""
    ffn = fn
    if '.' in fn:
        ext = '.' + fn.split('.')[-1]
        ffn = '.'.join(fn.split('.')[:-1])
    i = 0
    md5o = md5(orig)
    while os.path.exists(dest) and md5(dest) != md5o:
        i += 1
        fn = f"{ffn}_{i}{ext}"
        dest = os.path.join(dest_path, fn)
    if copy:
        shutil.copyfile(orig, dest)
    else:
        os.rename(orig, dest)
    return dest

class Hist:
    def __init__(self):
        self.hist = list()
        self.idx = -1

    @property
    def current(self):
        if self.idx < 0:
            self.idx = 0
            raise IndexError("Negative indexes not allowed")
        return self.hist[self.idx]

    def append(self, img):
        self.idx += 1
        self.hist.append(img)

    def next(self):
        if self.idx < len(self.hist)-1:
            self.idx += 1
        else:
            raise IndexError
        return self.current

    def prev(self):
        self.idx -= 1
        return self.current

    def delete(self, img):
        while img in self.hist:
            i = self.hist.index(img)
            self.hist.remove(img)
            if i <= self.idx:
                self.idx -= 1

    def replace(self, old, new):
        while old in self.hist:
            i = self.hist.index(old)
            self.hist[i] = new

class Bank:
    def __init__(self, paths, recursive=False):
        self.paths = paths
        self.recursive = recursive
        self.reload()

    def reload(self):
        f = list()
        for folder in self.paths:
            if os.path.isfile(folder):
                f.append(folder)
            else:
                f.extend(folder.rglob("*") if self.recursive else folder.glob("*"))
        self.imgs = list(filter(lambda p: p.is_file() and p.suffix in BrowserBase.EXTS,
                f))
        self._len = len(self.imgs)
        if '--norand' in sys.argv:
            print("sort")
            self.imgs = sorted(self.imgs)
        else:
            shuffle(self.imgs)
        self._imgs = iter(self.imgs)

    def delete_img(self):
        self._len -= 1

    def __iter__(self):
        return self

    def __next__(self):
        while 1:
            try:
                return next(self._imgs)
            except StopIteration:
                self.reload()
                print("reload")
                app.quit()
                if not self:
                    raise ValueError("No More Image to browse")

    def __len__(self):
        return self._len

class Main(BrowserBase):
    def __init__(self, recursive=False, paths=None):
        paths = paths or [os.getcwd()]


        self.hist = Hist()
        self.bank = Bank(paths, recursive=recursive)
        if not self.bank:
            raise IndexError

        self.img = None
        super().__init__()

        sg = QDesktopWidget().screenGeometry()

        self.r_w = QWidget()
        self.r_l = QHBoxLayout()
        self.r_w.setLayout(self.r_l)
        self.hl.addWidget(self.r_w)
        self.r_w.hide()
        self.r_le = QLineEdit()
        self.r_btn = QPushButton("Rename")
        self.r_le.returnPressed.connect(self.rename)
        self.r_btn.clicked.connect(self.rename)
        self.r_l.addWidget(self.r_le)
        self.r_l.addWidget(self.r_btn)

        self.s_w = QWidget()
        self.s_l = QHBoxLayout()
        self.s_w.setLayout(self.s_l)
        self.hl.addWidget(self.s_w)
        self.s_w.hide()
        self.s_cb = QComboBox()
        self.s_cb.setEditable(True)
        self.s_cb.lineEdit().returnPressed.connect(self.move_sort)
        self.s_a = QPushButton('+')
        self.s_a.clicked.connect(self.ask_path)
        self.s_btn = QPushButton("Move")
        self.s_btn.clicked.connect(self.move_sort)
        self.s_l.addWidget(self.s_cb)
        self.s_l.addWidget(self.s_btn)
        self.s_l.addWidget(self.s_a)
        self.pause = self.pp = True

    def move_sort(self):
        self.s_w.hide()

        try:
            nn = safe_move(str(self.img), os.path.expanduser(self.s_cb.currentText()))
        except AssertionError:
            return
        print("moved", self.img, "to", nn)

        self.bank.delete_img()
        self.hist.delete(self.img)
        self.nxt_img()

        self.lbl.setFocus()
        self.pause = self.pp

    @property
    def s_path(self):
        return self.img.parent

    def up_s_cb(self):
        self.s_cb.clear()
        print(self.s_path)
        if self.s_path == Path("~/Downloads").expanduser():
            g = glob(str(Path("~/Sorted").expanduser() / "*"))
        else:
            g = glob(os.path.join(self.s_path, "*"))
        self.s_cb.addItems(
                sorted(
                    [d for d in g
                        if os.path.isdir(d)],
                    key=lambda x: x.lower())
                + [os.path.realpath(self.s_path.parent), "~/Downloads"])

    def ask_path(self):
        name, v = QInputDialog.getText(self, "New Folder", "Name : ")
        if v:
            os.mkdir(os.path.join(self.s_path, name))
            self.up_s_cb()

    def rename(self):
        newname = self.img.parent / self.r_le.text()
        if self.img.suffix != newname.suffix:
            print(newname, "change exention ; expected", self.img.suffix)
            return
        self._rename(self.img, newname)
        self.r_w.hide()
        self.lbl.setFocus()
        self.pause = self.pp

    def _rename(self, old, new):
        os.rename(old, new)
        self.nxt_img()

    def timeout(self):
        self.nxt_img()
        self.timer.start(10000)

    def set_img(self, img):
        super().set_img(str(img))
        self.img = img

    def rand_img(self):
        img = next(self.bank)
        self.hist.append(img)
        self.set_img(img)

    def nxt_img(self):
        try:
            self.set_img(self.hist.next())
        except IndexError:
            try:
                self.rand_img()
            except ValueError as e:
                print(e)
                app.quit()

    def prv_img(self):
        try:
            i = self.hist.prev()
        except IndexError:
            return
        self.set_img(i)

    def update_title(self):
        try:
            self.title = f"{self.img} {(1+self.hist.idx)%(len(self.bank)+1)}/{len(self.bank)+1}"
        except ZeroDivisionError:
            self.title = "GenNameError"
        super().update_title()

    def ren_img(self):
        if self.r_w.isVisible():
            self.pause = self.pp
            self.r_w.hide()
        else:
            self.r_le.setFocus()
            self.r_le.setText('_' + self.img.name.replace(' ', '-'))
            self.r_le.setCursorPosition(0)
            self.pp = self.pause
            self.pause=True
            self.r_w.show()

    def srt_img(self):
        if self.s_w.isVisible():
            self.pause=self.pp
            self.s_w.hide()
        else:
            self.up_s_cb()
            self.s_cb.setFocus()
            self.pp = self.pause
            self.pause=True
            self.s_w.show()

    def del_img(self):
        self.pp = self.pause
        self.pause = True
        ok = QMessageBox.question(self, "Delete IMG",
                f"Are you sure you want to delete {self.img} ?",
                QMessageBox.Yes | QMessageBox.No)
        if ok == QMessageBox.Yes:
            print("deleting", self.img)
            os.remove(self.img)

            self.bank.delete_img()
            self.hist.delete(self.img)
            self.nxt_img()
        self.pause = self.pp

    def save_img(self):
        save_rep = Path("~/Images/Real/00_NewElite").expanduser()
        nimg = save_rep / Path(self.img).name
        self._rename(self.img, nimg)

    def escape_focus(self):
        self.lbl.setFocus()
        self.pause = self.pp
        self.r_w.hide()
        self.s_w.hide()

    def keyPressEvent(self, event):
        menu = {Qt.Key_Escape: self.escape_focus,
                Qt.Key_N: self.ren_img,
                Qt.Key_E: self.save_img}
        super().keyPressEvent(event, menu)


def tst_hist():
    hist = Hist()
    for i in range(5):
        hist.append(i)

    for i in range(3):
        print(hist.prev())

    print(hist.next())
    for i in range(3):
        print(hist.prev())

    print(hist.prev())
    exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if os.path.isfile("def.css"):
        with open("def.css", 'r') as f:
            app.setStyleSheet(f.read())
    path = Path(os.environ["HOME"], "Downloads")
    rec = 1
    args = copy(sys.argv)
    paths = list()
    for a in args:
        if os.path.isdir(a) or os.path.isfile(a):
            paths.append(Path(a).absolute())
            sys.argv.remove(a)
        elif a.isdigit() or (a.startswith('-') and a[1:].isdigit()):
            rec = int(a)
    Main(rec<0, paths).show()
    sys.exit(app.exec_())
