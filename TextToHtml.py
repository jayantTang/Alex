# TextToHtml.py
import re
from html import escape, unescape
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter


class TextToHtml:
    def __init__(self):
        self.buffer = ""
        self.slice = []

    @staticmethod
    def bufferToSlice(s):
        slices = []
        i = 0
        while i < len(s):
            # 检查是否为合法名称的起始
            if re.match(r'[a-zA-Z0-9_]', s[i]):
                j = i + 1
                while j < len(s) and re.match(r'[a-zA-Z0-9_]', s[j]):
                    j += 1
                # 如果不是字符串结尾，则将其作为合法分片添加
                if j < len(s):
                    slices.append(s[i:j])
                i = j
            # 处理中文字符、空白符和特殊符号
            else:
                slices.append(s[i])
                i += 1
        # 处理剩余字符串，如果最后一个是合法名称，则将其作为剩余字符串
        if slices and re.match(r'[a-zA-Z0-9_]', slices[-1][0]):
            remaining = slices.pop()
        else:
            remaining = ""
        return slices, remaining

    def deal(self, op_type, content):
        if op_type == "user_role":
            return f"""<br>{content}:"""
        elif op_type == "ai_role":
            return f"""<br>{content}:"""
        elif op_type == "user_words":
            return f"""{content}"""
        elif op_type != "ai_words":
            raise Exception("TextToHtml:deal:op_type error")

        # return f"""
        #     <div style="margin-top:4px">{self.text_to_html(content)}</div>

        print(f"---------")
        print(f"原有:{self.buffer}|")

        self.buffer += content
        print(f"现有:{self.buffer}|")

        [this_slices, self.buffer] = self.bufferToSlice(self.buffer)
        self.slice += this_slices

        print(f"处理后:{self.buffer}|")
        print(f"发出:{this_slices}|")

        return ""

    def text_to_html(self, text):
        # return text # todo:先跳过代码高亮处理流程,重构后调整
        """ 将语句转为带格式标识的html """

        def highlight_code(code, language="python"):
            try:
                lexer = get_lexer_by_name(language.strip(), stripall=True)
            except:
                lexer = PythonLexer()

            formatter = HtmlFormatter(
                style="default",
                noclasses=True,
                # 关键修改1：保留pre的默认换行特性
                prestyles="margin:0; padding:0; white-space: pre-wrap;",
                cssstyles="background:#f0f0f0; margin:0; padding:0.5em;"
            )
            return highlight(code, lexer, formatter)

        text = escape(text)

        def replace_code_blocks(match):
            lang = match.group(1).strip()
            code_content = unescape(match.group(2).strip())
            # 关键修改2：保留原始代码的换行符
            highlighted = highlight_code(code_content, lang)
            # 用div包裹保持块级特性
            return f'<div class="code-block">{highlighted}</div>'

        text = re.sub(
            r'```(\w*?)\n(.*?)```',
            replace_code_blocks,
            text,
            flags=re.DOTALL
        )

        # 转换非代码区域的换行
        text = re.sub(r'\n', '<br>', text)
        return text
