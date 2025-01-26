# ui.py
import re
from html import escape, unescape
from time import sleep

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton)
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QMetaObject, Qt
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from api_client import ChatWorker


class ChatWindow(QMainWindow):
    preset_task_finish = pyqtSignal()
    def __init__(self, questions):
        def init_ui():
            self.setWindowTitle("DeepSeek-Alex")
            self.setGeometry(100, 100, 1000, 800)

            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            layout = QVBoxLayout(main_widget)

            # 对话显示区域
            self.output_area = QTextEdit()
            self.output_area.setReadOnly(True)
            self.output_area.setStyleSheet("""
                QTextEdit {
                    font-family: "Courier New", "微软雅黑";
                    font-size: 11pt;
                }
                pre {
                    margin: 4px 0;
                    padding: 8px;
                    background: #f0f0f0;
                    border-radius: 2px;
                    tab-size: 4;
                }
            """)
            layout.addWidget(self.output_area, 4)

            # 输入区域
            input_layout = QHBoxLayout()
            self.input_field = QLineEdit()
            self.input_field.setPlaceholderText("输入消息...")
            self.send_btn = QPushButton("Send")
            input_layout.addWidget(self.input_field, 4)
            input_layout.addWidget(self.send_btn, 1)
            layout.addLayout(input_layout)

            # 信号连接
            self.send_btn.clicked.connect(self.send_Button_submit)
            self.input_field.returnPressed.connect(self.send_Button_submit)

        super().__init__()
        self.send_btn = None
        self.input_field = None
        self.output_area = None
        init_ui()

        # 新增功能属性
        self.input_history = []  # 历史输入记录
        self.current_history_index = -1  # 当前历史索引
        self.current_editing_text = ""  # 临时保存编辑内容

        # 启动预设任务
        self.questions = questions
        self.preset_task_finish.connect(self.preset_task)
        QTimer.singleShot(300, self.preset_task)

    def preset_task(self):
        if self.send_btn.isEnabled() and len(self.questions) != 0:
            one = self.questions.pop(0)
            self.input_field.setText(one)
            self.send_Button_submit()

    def send_Button_submit(self):
        def send_Button_submit_respond(answer):
            """ 处理AI响应 """
            self.append_message("AI", answer)
            self.send_btn.setEnabled(True)
            self.preset_task_finish.emit()

        # 锁定按钮
        self.send_btn.setEnabled(False)

        # 输入处理
        user_input = self.input_field.text().strip()
        self.input_history.append(user_input)
        self.current_history_index = len(self.input_history)
        self.append_message("User", user_input)
        self.input_field.clear()

        # 发起AI访问
        self.chat_task = ChatWorker(user_input, send_Button_submit_respond)
        self.chat_task.start()

    def keyPressEvent(self, event):
        def navigate_history(direction):
            """历史记录导航逻辑"""
            if not self.input_history:
                return

            # 保存当前编辑内容
            if self.current_history_index == len(self.input_history):
                self.current_editing_text = self.input_field.text()

            new_index = self.current_history_index + direction
            new_index = max(0, min(new_index, len(self.input_history)))

            if new_index != self.current_history_index:
                self.current_history_index = new_index
                text = self.input_history[new_index] if new_index < len(
                    self.input_history) else self.current_editing_text
                self.input_field.setText(text)

        """处理上下键历史记录"""
        if event.key() == Qt.Key_Up:
            navigate_history(-1)
        elif event.key() == Qt.Key_Down:
            navigate_history(1)
        else:
            super().keyPressEvent(event)

    def append_message(self, role, content):
        """ 输出回答 """
        def text_to_html(text):
            """ 将语句转为带格式标识的html """

            def highlight_code(code, language="python"):
                try:
                    lexer = get_lexer_by_name(language.strip(), stripall=True)
                except:
                    lexer = PythonLexer()

                formatter = HtmlFormatter(
                    style="default",
                    noclasses=True,
                    prestyles="margin:0; padding:0.5em; background:#f0f0f0; border-radius:4px;",
                    cssstyles="background:#f0f0f0;"
                )
                return highlight(code, lexer, formatter)

            text = escape(text)
            code_blocks = re.findall(r"```(\w*?)\n(.*?)```", text, re.DOTALL)

            for lang, code in code_blocks:
                raw_code = unescape(code).replace("&lt;", "<").replace("&gt;", ">")
                highlighted = highlight_code(raw_code, lang)
                text = text.replace(f"```{lang}\n{code}```", highlighted)

            text = text.replace("\n", "<br>")
            text = re.sub(r" {2,}", lambda m: "&nbsp;" * len(m.group()), text)
            return text

        cursor = self.output_area.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(f"""
            <div style="margin-bottom:16px">
                <span style="color:#2c3e50;font-weight:bold">{role}:</span>
                <div style="margin-top:4px">{text_to_html(content)}<br><br></div>
            </div>
        """)
        self.output_area.ensureCursorVisible()
