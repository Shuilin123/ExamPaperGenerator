import tkinter as tk
from tkinter import ttk
from utils import UI_FONT


class ItemSettingsPanel:
    SELECT_COLOR = '#d0e4f7'

    def __init__(self, parent, item_rows, add_item_row_data, on_change_callback=None, on_generate=None, on_save_config=None, on_load_config=None):
        self.parent = parent
        self.item_rows = item_rows
        self.add_item_row_data = add_item_row_data
        self.on_change_callback = on_change_callback
        self.on_generate = on_generate
        self.on_save_config = on_save_config
        self.on_load_config = on_load_config
        self.subtotal_labels = []
        self.header_total_label = None
        self.item_container = None
        self.selected_index = None
        self.row_frames = []
        self.bank_type_frame = None
        self.bank_canvas = None
        self.bank_scroll_frame = None
        self.bank_type_labels = []
        self._build()

    def _build(self):
        self.header_total_label = ttk.Label(self.parent, text="题型配置（可直接编辑）", style='Header.TLabel')
        self.header_total_label.pack(anchor=tk.W, pady=(0, 2))
        header = ttk.Frame(self.parent)
        header.pack(fill=tk.X, padx=1, pady=(0, 2))
        ttk.Label(header, text="题型名称", font=(UI_FONT, 9, 'bold'), width=14).pack(side=tk.LEFT, padx=1)
        ttk.Label(header, text="题量", font=(UI_FONT, 9, 'bold'), width=6, anchor=tk.CENTER).pack(side=tk.LEFT, padx=1)
        ttk.Label(header, text="每题分值", font=(UI_FONT, 9, 'bold'), width=8, anchor=tk.CENTER).pack(side=tk.LEFT, padx=1)
        ttk.Label(header, text="题型总分", font=(UI_FONT, 9, 'bold'), width=8, anchor=tk.CENTER).pack(side=tk.LEFT, padx=1)
        ttk.Label(header, text="题库题型", font=(UI_FONT, 9, 'bold'), width=14).pack(side=tk.LEFT, padx=1)
        list_frame = ttk.Frame(self.parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.item_container = ttk.Frame(canvas)
        self.item_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.item_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas = canvas
        self.parent.update_idletasks()
        self._limit_canvas_height()
        self._refresh_item_widgets()
        ttk.Separator(self.parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(3, 2))
        bank_header = ttk.Label(self.parent, text="题库题型统计（导入题库后自动显示）", style='Header.TLabel')
        bank_header.pack(anchor=tk.W, pady=(0, 2))
        bank_container = ttk.Frame(self.parent)
        bank_container.pack(fill=tk.X, padx=1, pady=(0, 2))
        self.bank_canvas = tk.Canvas(bank_container, highlightthickness=0, height=40)
        bank_scroll = ttk.Scrollbar(bank_container, orient="vertical", command=self.bank_canvas.yview)
        self.bank_scroll_frame = ttk.Frame(self.bank_canvas)
        self.bank_scroll_frame.bind("<Configure>", lambda e: self.bank_canvas.configure(scrollregion=self.bank_canvas.bbox("all")))
        self.bank_canvas.create_window((0, 0), window=self.bank_scroll_frame, anchor="nw")
        self.bank_canvas.configure(yscrollcommand=bank_scroll.set)
        self.bank_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        bank_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.bank_type_labels = []
        self.bank_type_counts = None
        self.bank_canvas.bind("<Configure>", lambda e: self._refresh_bank_layout())
        btn_f = ttk.Frame(self.parent)
        btn_f.pack(fill=tk.X)
        btn_f.columnconfigure(0, weight=1)
        btn_f.columnconfigure(1, weight=1)
        ttk.Button(btn_f, text="添加题型", command=self._add_item).grid(row=0, column=0, padx=(0, 3), sticky=tk.E)
        ttk.Button(btn_f, text="删除选中", command=self._del_selected).grid(row=0, column=1, padx=(3, 0), sticky=tk.W)

        ttk.Separator(self.parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(4, 4))
        action_frame = ttk.Frame(self.parent)
        action_frame.pack(fill=tk.X)
        self.gen_status = ttk.Label(action_frame, text="", foreground='#555')
        self.gen_status.pack(side=tk.LEFT)
        self.gen_progress = ttk.Progressbar(action_frame, mode='indeterminate', length=120)
        self.gen_progress.pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(action_frame, text="  保存配置  ", command=self.on_save_config).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(action_frame, text="  加载配置  ", command=self.on_load_config).pack(side=tk.RIGHT, padx=4)
        self.gen_btn = ttk.Button(action_frame, text="  生成试卷  ", command=self.on_generate)
        self.gen_btn.pack(side=tk.RIGHT, padx=(0, 4))

    def _limit_canvas_height(self):
        parent_height = self.parent.winfo_height()
        if parent_height > 0:
            other_widgets_height = 200
            max_canvas_height = parent_height - other_widgets_height
            if max_canvas_height > 100:
                self._canvas.configure(height=max_canvas_height)

    def _select_row(self, idx):
        self.selected_index = idx
        for i, f in enumerate(self.row_frames):
            bg = self.SELECT_COLOR if i == idx else 'white'
            f.configure(bg=bg)

    def _on_field_change(self, *args):
        self._update_all_subtotals()
        self._update_all_totals()
        if self.on_change_callback:
            self.on_change_callback()

    def _setup_row_traces(self):
        for row in self.item_rows:
            if '_trace_ids' not in row:
                row['_trace_ids'] = {}
            for key in ('item_type', 'item_count', 'item_score'):
                old = row['_trace_ids'].get(key)
                if old:
                    row[key].trace_remove('write', old)
                cb = row[key].trace_add('write', self._on_field_change)
                row['_trace_ids'][key] = cb

    def _refresh_item_widgets(self):
        for w in self.item_container.winfo_children():
            w.destroy()
        self.subtotal_labels = []
        self.row_frames = []
        self.selected_index = None
        self._setup_row_traces()
        for i, row in enumerate(self.item_rows):
            f = tk.Frame(self.item_container, bg='white')
            f.pack(fill=tk.X, padx=1, pady=0)
            entries = []
            for var, w in [(row['item_type'], 14), (row['item_count'], 6), (row['item_score'], 8)]:
                e = ttk.Entry(f, textvariable=var, width=w, justify=tk.CENTER if w < 12 else tk.LEFT)
                e.pack(side=tk.LEFT, padx=1)
                entries.append(e)
            sub = ttk.Label(f, width=8, anchor=tk.CENTER, foreground='#1a73e8')
            sub.pack(side=tk.LEFT, padx=1)
            self.subtotal_labels.append(sub)
            bank_e = ttk.Entry(f, textvariable=row['bank_type'], width=14)
            bank_e.pack(side=tk.LEFT, padx=1)
            self.row_frames.append(f)
            idx = i
            f.bind("<Button-1>", lambda e, idx=idx: self._select_row(idx))
            for child in [e for e in entries] + [sub, bank_e]:
                child.bind("<Button-1>", lambda e, idx=idx: self._select_row(idx))
        self._update_all_subtotals()
        self._update_all_totals()

    def _update_subtotal(self, idx, row, label):
        try:
            count = int(row['item_count'].get())
            score = float(row['item_score'].get())
            label.config(text=f"{count * score:.1f}")
        except ValueError:
            label.config(text="-")

    def _update_all_subtotals(self):
        for i, row in enumerate(self.item_rows):
            if i < len(self.subtotal_labels):
                self._update_subtotal(i, row, self.subtotal_labels[i])

    def _update_all_totals(self):
        total = 0.0
        for row in self.item_rows:
            try:
                count = int(row['item_count'].get())
                score = float(row['item_score'].get())
                total += count * score
            except ValueError:
                pass
        self.header_total_label.config(text=f"第二步:题型配置（试卷总分: {total:.1f}）")

    def _add_item(self):
        self.add_item_row_data("新题型", "1", "1", "新题型")
        self._refresh_item_widgets()
        if self.on_change_callback:
            self.on_change_callback()

    def _del_selected(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.item_rows):
            self.item_rows.pop(self.selected_index)
            self._refresh_item_widgets()
            if self.on_change_callback:
                self.on_change_callback()

    def refresh_item_tree(self):
        self._update_all_subtotals()
        self._update_all_totals()

    def update_bank_types(self, type_counts):
        self.bank_type_counts = type_counts
        self.parent.after_idle(self._refresh_bank_layout)

    def _refresh_bank_layout(self):
        for w in self.bank_scroll_frame.winfo_children():
            w.destroy()
        self.bank_type_labels = []
        type_counts = self.bank_type_counts
        if not type_counts:
            ttk.Label(self.bank_scroll_frame, text="暂无数据，请导入题库文件", foreground='#999').pack(anchor=tk.W)
            self.bank_canvas.configure(height=40)
            return
        total = sum(type_counts.values())
        total_lbl = ttk.Label(self.bank_scroll_frame, text=f"题库总题数: {total}", foreground='#1a73e8', font=(UI_FONT, 9, 'bold'))
        total_lbl.grid(row=0, column=0, columnspan=999, sticky=tk.W, pady=(0, 2))
        items = list(type_counts.items())
        items_per_row = 3
        col = 0
        row = 1
        for qtype, count in items:
            if col >= items_per_row:
                col = 0
                row += 1
            lbl = ttk.Label(self.bank_scroll_frame, text=f"• {qtype}: {count}题")
            lbl.grid(row=row, column=col, sticky=tk.W, padx=2, pady=1)
            self.bank_type_labels.append(lbl)
            col += 1
        num_rows = row + 1
        canvas_height = min(num_rows * 25, 80)
        self.bank_canvas.configure(height=canvas_height)
