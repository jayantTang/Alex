# TextToHtml.py
import html
import re
from html import escape, unescape
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter


class TextToHtml:
    def __init__(self):
        self.buffer = ""    # 缓存未接收完成的语句
        self.slice = []     # 缓存未处理完的分片组
        self.section = ""   # 表示当前处理区间是否为代码段
        self.code_text = ""   # 表示当前处理区间是否为代码段

    @staticmethod
    def bufferToSlice(s):
        slices = []
        remaining = ""
        i = 0
        while i < len(s):
            # 检查是否为合法名称的起始
            if re.match(r'[a-zA-Z0-9_]', s[i]):
                j = i + 1
                while j < len(s) and re.match(r'[a-zA-Z0-9_]', s[j]):
                    j += 1
                if j == len(s):
                    # 如果这个合法名称片段到字符串末尾了，将其作为 remaining
                    remaining = s[i:j]
                else:
                    # 否则将其作为一个分片添加到 slices 中
                    slices.append(s[i:j])
                i = j
            # 处理中文字符、空白符和特殊符号
            else:
                if remaining:
                    # 如果之前有 remaining，将其添加到 slices 中并清空 remaining
                    slices.append(remaining)
                    remaining = ""
                slices.append(s[i])
                i += 1

        return slices, remaining

    @staticmethod
    def parse_slices(slices, identification):
        output = []
        other_slice = []
        i = 0
        current_text = ""

        while i < len(slices):
            found = False
            for idx, ident in enumerate(identification):
                if i + len(ident) <= len(slices) and slices[i:i + len(ident)] == ident:
                    # 如果当前有累积的普通文本，将其添加到 output 中
                    if current_text:
                        output.append([current_text, True])
                        current_text = ""
                    # 添加标识单元及其在 identification 列表中的索引
                    output.append([''.join(ident), idx])
                    i += len(ident)
                    found = True
                    break

            if not found:
                # 未找到标识单元，累积普通文本
                current_text += slices[i]
                i += 1

        # 如果最后有累积的普通文本，将其添加到 output 中
        if current_text:
            output.append([current_text, True])

        # 检查末尾未闭合的情况
        for ident in identification:
            for j in range(len(ident) - 1, 0, -1):
                if output and output[-1][0].endswith(''.join(ident[:j])):
                    # 移除可能是标识单元一部分的文本并添加到 other_slice
                    start_index = len(output[-1][0]) - len(''.join(ident[:j]))
                    other_slice = list(output[-1][0][start_index:]) + other_slice
                    output[-1][0] = output[-1][0][:start_index]
                    if not output[-1][0]:
                        output.pop()
                    break

        return output, other_slice

    def slice_match(self, slices):
        identification = [
            ["<", "think", ">"],            # 深度思考段开标识
            ["<", "/", "think", ">"],       # 深度思考段闭标识
            ["`", "`", "`", "python"],      # python代码段开标识
            ["`", "`", "`"],                # 代码段闭标识
            ["\n"],                         # 换行符
        ]

        (output, other_slice) = self.parse_slices(slices, identification)
        output_html = ""
        for [pic, type] in output:
            if type is True:
                if self.section == "python":
                    self.code_text += pic
                else:
                    # HTML 转义
                    pic = html.escape(pic)
                    pic = pic.replace(' ', '&nbsp;')
                    pic = pic.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')

                    output_html += pic

                # code_content = unescape(match.group(2).strip())
                # # 关键修改2：保留原始代码的换行符
                # highlighted = highlight_code(code_content, lang)
                # # 用div包裹保持块级特性
                # return f'<div class="code-block">{highlighted}</div>'

            else:
                if type == 2:
                    self.section = "python"
                    output_html += f'<div class="code-block">'
                    output_html += f"[{type}]"
                    output_html += pic
                elif type == 3:
                    self.section = ""
                    output_html += f'</div>'
                    output_html += f"[{type}]"
                    output_html += pic
                elif type == 4: # \n
                    if self.section == "python":
                        temp = self.highlight_code(self.code_text + pic, language="python")
                        print(f"0:[{self.code_text + pic}]")
                        print(f"1:[{temp}]")
                        output_html += temp
                        self.code_text = ""
                    else:
                        pic = pic.replace('\n', '<br>')
                        output_html += pic

        return output_html, other_slice

    @staticmethod
    def highlight_code(code, language="python"):
        try:
            lexer = get_lexer_by_name(language.strip(), stripall=False)
        except:
            lexer = PythonLexer()

        formatter = HtmlFormatter(
            style="default",
            noclasses=True,
            prestyles="margin:0; padding:0; white-space: pre;",
            cssstyles="background:#f0f0f0; margin:0; padding:0.5em;",
            lineseparator=""  # 直接设置行分隔符为<br>
        )


        output = code.replace('\n', '<br>')
        output = output.replace('\t', '    ')
        output = highlight(output, lexer, formatter)

        output = output.replace('<span style="color: #666">&lt;</span>br<span style="color: #666">&gt;</span>', '<br>')
        output = output.replace('<span style="color: #666">&lt;</span>br<span style="color: #666">&gt;&lt;</span>br<span style="color: #666">&gt;</span>', '<br><br>')
        output = output.replace('&lt;br&gt;', '<br>')
        return output

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

        # print(f"---------")
        # print(f"原有:{self.buffer}|")

        self.buffer += content
        # print(f"现有:{self.buffer}|")

        [this_slices, self.buffer] = self.bufferToSlice(self.buffer)
        self.slice += this_slices
        # print(self.slice)
        output, other_slice = self.slice_match(self.slice)
        # print(f"[{content}] + [{self.slice}]  ===>  [{self.buffer}] + [{output}] + [{other_slice}]")
        self.slice = other_slice




        # 添加代码高亮


        return output

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
