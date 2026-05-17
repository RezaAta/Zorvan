import qtawesome as qta
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
names = [
    "fa.play",
    "fa.pause",
    "fa.undo",
    "fa.stop",
    "fa.sync",
    "fa.plus",
    "fa.trash",
    "fa.eraser",
    "fa.folder-open",
    "fa.check",
    "fa.step-forward",
]
for n in names:
    try:
        ic = qta.icon(n, color="#00ff00")
        pm = ic.pixmap(16, 16)
        img = pm.toImage()
        w, h = img.width(), img.height()
        tot = [0, 0, 0]
        cnt = 0
        for x in range(w):
            for y in range(h):
                col = QColor(img.pixel(x, y))
                a = col.alpha()
                if a > 10:
                    tot[0] += col.red()
                    tot[1] += col.green()
                    tot[2] += col.blue()
                    cnt += 1
        if cnt > 0:
            avg = [tot[0] // cnt, tot[1] // cnt, tot[2] // cnt]
            print(n, "avg", avg)
        else:
            print(n, "empty")
    except Exception as e:
        print(n, "error", e)
