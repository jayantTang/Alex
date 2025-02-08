# ui.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton)
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from api_client import ChatWorker
from TextToHtml import TextToHtml


class MultilineTextEdit(QTextEdit):
    enterPressed = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.textCursor().insertText("\n")
            else:
                self.enterPressed.emit()
                event.accept()
        elif event.key() == Qt.Key_Up:
            # 通过窗口引用访问方法
            self.window().navigate_history(-1)
            event.accept()
        elif event.key() == Qt.Key_Down:
            self.window().navigate_history(1)
            event.accept()
        else:
            super().keyPressEvent(event)


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
            self.input_field = MultilineTextEdit()
            self.input_field.setPlaceholderText("输入消息...")
            self.input_field.setStyleSheet("""
                            QTextEdit {
                                font-family: "微软雅黑";
                                font-size: 11pt;
                                padding: 4px;
                            }
                        """)
            self.input_field.setMaximumHeight(100)  # 限制输入框高度
            self.send_btn = QPushButton("Send")
            self.stop_btn = QPushButton("Stop")
            input_layout.addWidget(self.input_field, 4)
            input_layout.addWidget(self.send_btn, 1)
            input_layout.addWidget(self.stop_btn, 1)
            layout.addLayout(input_layout)

            # 信号连接
            self.send_btn.clicked.connect(self.send_Button_submit)
            self.stop_btn.clicked.connect(self.stop_Button_submit)
            self.input_field.enterPressed.connect(self.send_Button_submit)

        super().__init__()
        self.send_btn = None
        self.stop_btn = None
        self.input_field = None
        self.output_area = None
        self.tth = TextToHtml()
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
            self.input_field.setPlainText(one)
            self.send_Button_submit()

    def stop_Button_submit(self):
        self.chat_task.stop()
        self.send_btn.setEnabled(True)

    def send_Button_submit(self):
        def send_Button_submit_respond(finished, answer):
            """ 处理AI响应 """
            self.append_message("ai_words", answer)
            if finished is True:
                self.send_btn.setEnabled(True)
                self.preset_task_finish.emit()

        # 锁定按钮
        self.send_btn.setEnabled(False)

        # 输入处理
        user_input = self.input_field.toPlainText().strip()
        if not user_input:
            self.send_btn.setEnabled(True)
            return

        self.input_history.append(user_input)
        self.current_history_index = len(self.input_history)
        self.append_message("user_role", "User")
        self.append_message("user_words", user_input)
        self.input_field.clear()

        # 发起AI访问
        self.chat_task = ChatWorker(user_input, send_Button_submit_respond)
        self.chat_task.start()
        self.append_message("ai_role", "AI")

    def navigate_history(self, direction):  # 移动到类方法层级
        """历史记录导航逻辑"""
        if not self.input_history:
            return

        # 保存当前编辑内容
        if self.current_history_index == len(self.input_history):
            self.current_editing_text = self.input_field.toPlainText()

        new_index = self.current_history_index + direction
        new_index = max(0, min(new_index, len(self.input_history)))

        if new_index != self.current_history_index:
            self.current_history_index = new_index
            text = (self.input_history[new_index]
                    if new_index < len(self.input_history)
                    else self.current_editing_text)
            self.input_field.setPlainText(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key_Down:
            self.navigate_history(1)
        else:
            super().keyPressEvent(event)

    def append_message(self, op_type, content):
        """ 输出回答
            type:
                user_role
                ai_role
                user_words
                ai_words
        """
        cursor = self.output_area.textCursor()
        cursor.movePosition(cursor.End)
        html_text = self.tth.deal(op_type, content)

        # print(f"{content}|")
        # print(f"{html_text}|")
        cursor.insertHtml(html_text)
        self.output_area.ensureCursorVisible()

        # cursor.insertHtml(f"""
        #     <style>
        #         .code-block pre {{
        #             background: #f0f0f0 !important;
        #             border-radius: 4px !important;
        #             margin: 4px 0 !important;
        #             white-space: pre-wrap; /* 关键修改3：允许代码换行 */
        #         }}
        #     </style>
        #     <div style="margin-bottom:16px">
        #         <span style="color:#2c3e50;font-weight:bold"><br>{role}:</span>
        #         <div style="margin-top:4px">{text_to_html(content)}</div>
        #     </div>
        # """)
