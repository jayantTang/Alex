# 遗留问题
    1、ui卡顿 #已闭环
    2、单行输入框 # 已闭环
    3、代码段尾篇幅 #已闭环

# 本地模型改造计划(使用todo)
    先跳过代码高亮处理流程 # 已完成
    植入尽量自封闭的状态机管理函数
    通过状态限制各项响应逻辑
    AI改造为受ctrl+c限制的非阻塞流式响应 # 已完成
        2025020710:已实现非阻塞流式响应,但缺失ctrl+c待补充
        2025020710:已改为实现stop按钮限制响应
    使用并改造代码高亮处理流程
        2025020816:转子项目：TextToHtml.py

# 子项目：TextToHtml.py
    背景:
        兼容流式、非流式的代码高亮输出处理模块较复杂，需要独立重构
    设计思路:
        流式&非流式 调动示例:
            self.tth = TextToHtml()
            html_text = self.tth.deal(op_type, content)
            cursor.insertHtml(html_text)
        处理策略:
            零散或完整的语句通过队列方式进入缓冲区(屏蔽流式、非流式差异)
                2025020817:已实现
            通过有效的头优先识别出标识单元
                2025020818:改为按有效切片拆分,按指定切片模式进行识别,不匹配则输出,匹配则触发格式状态,遗留尾切片处理待设计
                标识单元匹配策略:均为结合存、增量状态格式html描述进行输出
                    前列分片不满足匹配,形成输出
                    从特定位置开始的分片组,满足标识单元,此时按格式状态形成输出
                    从特定位置的剩余分片组,满足部分匹配标识单元,此时取消动作,将剩余分片组进行遗留
                    Q1:怎么解决长度优先匹配的问题?
                        尝试人为规定匹配单元优先级,遇到问题再调整
                综合来说:
                    self.slice ==> +标识单元规则 ==> html文本(多段匹配分片 + 存/增量状态) + 剩余self.slice
            出队标识单元,结合存量、增量格式状态决定html格式描述
            重新组织语句文本后输出
                存量语句在队列中等待下次循环
        2025020922:
            以整行流式方案初步开发完成,剩余以下问题
            1、代码段空一行的位置会显示成空两行
            2、代码段的阴影收尾有问题
            3、缓存显示机制存在尾部遗留的问题待解决
            4、遗留了诊断日志待审视重构
        标识单元分析:
            1、<think>XXXXX</think>
            2、```pythonXXXX```      : 代码高亮区间
            3、中文字符
            4、英文字符
            5、空白字符
