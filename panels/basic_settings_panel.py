import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from utils import UI_FONT
import pandas as pd


class BasicSettingsPanel:
    def __init__(self, parent, data_file, tex_path, paper_template_path, option_separator, exam_main, exam_sub, exam_time, on_data_file_change=None):
        self.parent = parent
        self.data_file = data_file
        self.tex_path = tex_path
        self.paper_template_path = paper_template_path
        self.option_separator = option_separator
        self.exam_main = exam_main
        self.exam_sub = exam_sub
        self.exam_time = exam_time
        self.on_data_file_change = on_data_file_change
        self._build()

    def _build(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)

        left_frame = ttk.Frame(self.parent)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 3), pady=1)
        left_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(left_frame, text="第一步:数据与输出设置", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 2))

        f1 = ttk.LabelFrame(left_frame, text="文件路径", padding=4)
        f1.pack(fill=tk.X, pady=(0, 4))
        f1.grid_columnconfigure(1, weight=1)

        ttk.Label(f1, text="题库文件:").grid(row=0, column=0, sticky=tk.W, pady=1)
        ttk.Entry(f1, textvariable=self.data_file).grid(row=0, column=1, padx=(3, 3), pady=1, sticky=tk.EW)
        ttk.Button(f1, text="浏览", command=self._browse_data).grid(row=0, column=2, padx=(3, 0), pady=1)

        ttk.Label(f1, text="TeX输出:").grid(row=1, column=0, sticky=tk.W, pady=1)
        ttk.Entry(f1, textvariable=self.tex_path).grid(row=1, column=1, padx=(3, 3), pady=1, sticky=tk.EW)
        ttk.Button(f1, text="浏览", command=self._browse_tex).grid(row=1, column=2, padx=(3, 0), pady=1)

        ttk.Label(f1, text="试卷模板:").grid(row=2, column=0, sticky=tk.W, pady=1)
        ttk.Entry(f1, textvariable=self.paper_template_path).grid(row=2, column=1, padx=(3, 3), pady=1, sticky=tk.EW)
        ttk.Button(f1, text="浏览", command=self._browse_template).grid(row=2, column=2, padx=(3, 0), pady=1)

        right_frame = ttk.Frame(self.parent)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0), pady=1)
        right_frame.grid_columnconfigure(0, weight=1)

        f2 = ttk.LabelFrame(right_frame, text="试卷信息", padding=4)
        f2.pack(fill=tk.BOTH, expand=True)
        f2.grid_columnconfigure(1, weight=1)

        r = 0
        ttk.Label(f2, text="选项分割符:").grid(row=r, column=0, sticky=tk.W, pady=1)
        ttk.Entry(f2, textvariable=self.option_separator, width=8).grid(row=r, column=1, sticky=tk.W, padx=3, pady=1)
        ttk.Label(f2, text="考试时长:").grid(row=r, column=2, sticky=tk.W, pady=1, padx=(8, 0))
        dur_f = ttk.Frame(f2)
        dur_f.grid(row=r, column=3, sticky=tk.W, padx=2)
        ttk.Entry(dur_f, textvariable=self.exam_time, width=5).pack(side=tk.LEFT)
        ttk.Label(dur_f, text="分钟").pack(side=tk.LEFT, padx=(1, 0))
        r += 1

        ttk.Separator(f2, orient=tk.HORIZONTAL).grid(row=r, column=0, columnspan=4, sticky=tk.EW, pady=4)
        r += 1

        ttk.Label(f2, text="考试名称:").grid(row=r, column=0, sticky=tk.NW, pady=1)
        ttk.Entry(f2, textvariable=self.exam_main).grid(row=r, column=1, columnspan=3, sticky=tk.EW, padx=3, pady=1)
        r += 1

        ttk.Label(f2, text="副标题:").grid(row=r, column=0, sticky=tk.NW, pady=1)
        ttk.Entry(f2, textvariable=self.exam_sub).grid(row=r, column=1, columnspan=3, sticky=tk.EW, padx=3, pady=1)

    def _browse_data(self):
        path = filedialog.askopenfilename(title="选择题库文件", filetypes=[("Excel文件", "*.xls *.xlsx")],initialdir="./data/")
        if path:
            self.data_file.set(path)
            self._detect_question_types(path)

    def _detect_question_types(self, file_path):
        try:
            data = pd.read_excel(file_path, skiprows=1)
            data.columns = data.columns.str.strip()
            if '题型' not in data.columns:
                messagebox.showwarning("提示", "题库文件中未找到'题型'列")
                return
            type_counts = data['题型'].astype(str).str.strip().value_counts()
            if self.on_data_file_change:
                self.on_data_file_change(type_counts.to_dict())
        except Exception as e:
            messagebox.showerror("错误", f"读取题库文件失败：{e}")

    def _browse_tex(self):
        path = filedialog.asksaveasfilename(title="保存TeX文件", defaultextension=".tex", filetypes=[("TeX文件", "*.tex")])
        if path:
            self.tex_path.set(path)

    def _browse_template(self):
        path = filedialog.askopenfilename(title="选择试卷模板", filetypes=[("TeX文件", "*.tex")],initialdir='./template/item_type/')
        if path:
            self.paper_template_path.set(path)
