import tkinter as tk
from tkinter import ttk
from utils import UI_FONT


class AboutPanel:
    def __init__(self, parent):
        self.parent = parent
        self._build()

    def _build(self):
        container = ttk.Frame(self.parent)
        container.pack(fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        about_frame = ttk.Frame(container)
        about_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=8)

        ttk.Label(about_frame, text="SGCC_Fj 试卷生成器", font=(UI_FONT, 14, 'bold'), foreground='#1a73e8').pack(pady=(0, 2))
        ttk.Label(about_frame, text="版本: v2.0.0", font=(UI_FONT, 9)).pack(pady=0)
        ttk.Label(about_frame, text="问题反馈: 如使用过程中遇到问题和建议，请写在issue中",
                 font=(UI_FONT, 8), foreground='#666').pack(pady=0)
        ttk.Separator(about_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)
        info_text = (
            "功能说明:\n\n"
            "• 基本设置: 配置题库文件、TeX输出路径、试卷名称与时长\n"
            "• 题型设置: 管理题型列表，支持自动按权重分配每题分值\n"
            "• 题型映射: 设置试卷题型与题库题型名称的对应关系\n"
            "• 答题说明: 为每种题型编辑考试时的答题要求说明\n"
            "• 模板设计: 可视化编辑密封线、评分表、页眉页脚、页面布局\n\n"
            "数据格式: Excel(.xls/.xlsx) / CSV\n"
            "权重规则: 简答题(5) > 多选题(4) > 单选题(3) > 判断题(1)\n"
            "支持配置保存与加载，方便重复使用相同模板。"
        )
        info_label = tk.Label(about_frame, text=info_text, font=(UI_FONT, 8), justify=tk.LEFT, anchor=tk.W)
        info_label.pack(fill=tk.X, pady=2)
        ttk.Separator(about_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)
        ttk.Label(about_frame, text="© 2026 shuilin. All rights reserved.", font=(UI_FONT, 8), foreground='#888888').pack(pady=(0, 0))
