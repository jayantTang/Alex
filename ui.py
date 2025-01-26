# ui.py
import re
from html import escape, unescape
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton)
from PyQt5.QtCore import Qt, QTimer
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from api_client import DeepSeekAPI


class ChatWindow(QMainWindow):
    def __init__(self, questions):
        super().__init__()
        self.send_btn = None
        self.input_field = None
        self.output_area = None
        self.init_ui()

        # 新增功能属性
        self.input_history = []  # 历史输入记录
        self.current_history_index = -1  # 当前历史索引
        self.current_editing_text = ""  # 临时保存编辑内容
        self.preset_questions = questions
        self.is_processing_preset = False  # 预置问题处理状态

        self.api = DeepSeekAPI()
        self.process_preset_questions()  # 启动预置处理

    def init_ui(self):
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
        self.send_btn.clicked.connect(self.send_message)
        self.input_field.returnPressed.connect(self.send_message)

    def send_message(self):
        self.send_btn.setEnabled(False)  # 锁定按钮
        user_input = self.input_field.text().strip()

        if not user_input:
            self.send_btn.setEnabled(True)
            return

        # 保存历史记录（非预置模式时）
        if not self.is_processing_preset:
            self.input_history.append(user_input)
            self.current_history_index = len(self.input_history)

        self.append_message("User", user_input)
        self.input_field.clear()

        try:
            response = self.api.get_response(user_input)
            self.append_message("AI", response)
        except Exception as e:
            self.append_message("System", f"Error: {str(e)}")
        finally:
            if not self.is_processing_preset:
                self.send_btn.setEnabled(True)

    def keyPressEvent(self, event):
        """处理上下键历史记录"""
        if event.key() == Qt.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key_Down:
            self.navigate_history(1)
        else:
            super().keyPressEvent(event)

    def navigate_history(self, direction):
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
            text = self.input_history[new_index] if new_index < len(self.input_history) else self.current_editing_text
            self.input_field.setText(text)

    def process_preset_questions(self):
        """处理预置问题队列"""
        if not self.preset_questions:
            return

        self.is_processing_preset = True
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        QTimer.singleShot(1000, self.send_next_preset_question)

    def send_next_preset_question(self):
        """发送下一个预置问题"""
        if not self.preset_questions:
            self.finish_preset_processing()
            return

        question = self.preset_questions.pop(0)
        self.input_field.setText(question)
        QTimer.singleShot(500, lambda: self.send_message())
        QTimer.singleShot(3000, self.send_next_preset_question)

    def finish_preset_processing(self):
        """完成预置处理"""
        self.is_processing_preset = False
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.clear()

    @staticmethod
    def text_to_html(text):
        """处理Markdown代码块"""

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

    def append_message(self, role, content):
        cursor = self.output_area.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(f"""
            <div style="margin-bottom:16px">
                <span style="color:#2c3e50;font-weight:bold">{role}:</span>
                <div style="margin-top:4px">{self.text_to_html(content)}<br><br></div>
            </div>
        """)
        self.output_area.ensureCursorVisible()
