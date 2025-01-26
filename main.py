import sys
from PyQt5.QtWidgets import QApplication
from ui import ChatWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    questions = [
        "提供简易的python代码实例",
        # "解释装饰器的作用",
        # "写一个计算斐波那契数列的函数"
    ]
    window = ChatWindow(questions)
    window.show()
    sys.exit(app.exec_())
