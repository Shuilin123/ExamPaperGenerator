import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from utils import UI_FONT, TEMPLATE_DIR, TEMP_DIR, LATEX_PATH, RESOURCE_DIR, SCRIPT_DIR, TemplateBuilder


class TemplateDesignPanel:
    def __init__(self, parent, item_rows, exam_main=None, exam_sub=None, exam_time=None):
        self.parent = parent
        self.item_rows = item_rows
        self.exam_main = exam_main
        self.exam_sub = exam_sub
        self.exam_time = exam_time
        self._raw_latex=None
        self._build()

    def _build(self):
        notebook = ttk.Notebook(self.parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        seal_frame = ttk.Frame(notebook, padding=8)
        score_frame = ttk.Frame(notebook, padding=8)
        hf_frame = ttk.Frame(notebook, padding=8)
        page_frame = ttk.Frame(notebook, padding=8)
        preview_frame = ttk.Frame(notebook, padding=8)

        notebook.add(seal_frame, text="  密封线设计  ")
        notebook.add(score_frame, text="  评分表设计  ")
        notebook.add(hf_frame, text="  页眉页脚设计  ")
        notebook.add(page_frame, text="  页面设计  ")
        notebook.add(preview_frame, text="  预览与保存  ")

        self._build_seal_tab(seal_frame)
        self._build_score_tab(score_frame)
        self._build_header_footer_tab(hf_frame)
        self._build_page_design_tab(page_frame)
        self._build_preview_tab(preview_frame)

    # ──────────────────────────────────────────────
    # 1. 密封线设计（图形化预览 + 可拖拽）
    # ──────────────────────────────────────────────
    def _build_seal_tab(self, parent):
        self.seal_left_offset = tk.DoubleVar(value=2.2)
        self.seal_bind_offset = tk.DoubleVar(value=1.5)
        self.seal_info_offset = tk.DoubleVar(value=1.0)
        self.seal_line_width = tk.DoubleVar(value=0.8)
        self.seal_dash_on = tk.IntVar(value=4)
        self.seal_dash_off = tk.IntVar(value=2)
        self.seal_warning_text = tk.StringVar(value="密封线内不准答题")
        self.seal_show_info = tk.BooleanVar(value=True)
        self.seal_info_text = tk.StringVar(value="单位 \\underline{\\hspace{3cm}} \\quad 岗位 \\underline{\\hspace{3cm}} \\quad 准考证号 \\underline{\\hspace{3cm}}")
        self.seal_show_binding = tk.BooleanVar(value=True)
        self.seal_line_type = tk.StringVar(value="dashed")
        self.seal_symbol = tk.StringVar(value="none")
        self.seal_symbol_interval = tk.DoubleVar(value=2.0)

        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        cv_frame = ttk.LabelFrame(paned, text="密封线预览（拖拽虚线调整位置）", padding=2)
        paned.add(cv_frame, weight=2)

        self.seal_canvas = tk.Canvas(cv_frame, bg='#fafafa', width=320, height=380,
                                     highlightthickness=1, highlightbackground='#ccc')
        self.seal_canvas.pack(fill=tk.BOTH, expand=True)

        ctrl_frame = ttk.LabelFrame(paned, text="参数设置", padding=4)
        paned.add(ctrl_frame, weight=1)

        self._seal_drag_item = None
        self._seal_drag_start_x = 0
        self.seal_canvas.bind("<Button-1>", self._seal_canvas_click)
        self.seal_canvas.bind("<B1-Motion>", self._seal_canvas_drag)
        self.seal_canvas.bind("<ButtonRelease-1>", self._seal_canvas_release)
        self.seal_canvas.bind("<Configure>", lambda e: self._redraw_seal_preview())

        row = 0
        ttk.Label(ctrl_frame, text="密封线位置 (cm):", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(ctrl_frame, from_=0.5, to=5.0, increment=0.1,
                    textvariable=self.seal_left_offset, width=6,
                    command=self._redraw_seal_preview).grid(row=row, column=1, sticky=tk.W, padx=2)
        row += 1

        ttk.Label(ctrl_frame, text="装订线偏移 (cm):", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(ctrl_frame, from_=0.3, to=4.0, increment=0.1,
                    textvariable=self.seal_bind_offset, width=6,
                    command=self._redraw_seal_preview).grid(row=row, column=1, sticky=tk.W, padx=2)
        row += 1

        ttk.Label(ctrl_frame, text="信息区偏移 (cm):", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(ctrl_frame, from_=0.3, to=3.0, increment=0.1,
                    textvariable=self.seal_info_offset, width=6,
                    command=self._redraw_seal_preview).grid(row=row, column=1, sticky=tk.W, padx=2)
        row += 1

        ttk.Separator(ctrl_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=2)
        row += 1

        ttk.Label(ctrl_frame, text="线宽 (pt):", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(ctrl_frame, from_=0.2, to=2.0, increment=0.1,
                    textvariable=self.seal_line_width, width=6,
                    command=self._redraw_seal_preview).grid(row=row, column=1, sticky=tk.W, padx=2)
        row += 1

        ttk.Label(ctrl_frame, text="线条样式:", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        line_type_cb = ttk.Combobox(ctrl_frame, textvariable=self.seal_line_type,
                                    values=["solid", "dashed", "dotted", "dashdot"],
                                    width=8, state="readonly")
        line_type_cb.grid(row=row, column=1, sticky=tk.W, padx=2)
        line_type_cb.bind("<<ComboboxSelected>>", lambda e: self._redraw_seal_preview())
        row += 1

        ttk.Label(ctrl_frame, text="虚线 (on/off):", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        df = ttk.Frame(ctrl_frame)
        df.grid(row=row, column=1, sticky=tk.W, padx=2)
        s1 = ttk.Spinbox(df, from_=1, to=20, width=3, textvariable=self.seal_dash_on, command=self._redraw_seal_preview)
        s1.pack(side=tk.LEFT)
        ttk.Label(df, text="/", font=(UI_FONT, 9)).pack(side=tk.LEFT, padx=1)
        s2 = ttk.Spinbox(df, from_=1, to=20, width=3, textvariable=self.seal_dash_off, command=self._redraw_seal_preview)
        s2.pack(side=tk.LEFT)
        row += 1

        ttk.Label(ctrl_frame, text="装饰符号:", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        sym_cb = ttk.Combobox(ctrl_frame, textvariable=self.seal_symbol,
                              values=["none", "cross", "diamond", "star"],
                              width=8, state="readonly")
        sym_cb.grid(row=row, column=1, sticky=tk.W, padx=2)
        sym_cb.bind("<<ComboboxSelected>>", lambda e: self._redraw_seal_preview())
        row += 1

        ttk.Label(ctrl_frame, text="符号间隔 (cm):", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        ttk.Spinbox(ctrl_frame, from_=0.5, to=5.0, increment=0.5,
                    textvariable=self.seal_symbol_interval, width=6,
                    command=self._redraw_seal_preview).grid(row=row, column=1, sticky=tk.W, padx=2)
        row += 1

        ttk.Separator(ctrl_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=2)
        row += 1

        ttk.Label(ctrl_frame, text="警告文字:", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.W, pady=1)
        warn_e = ttk.Entry(ctrl_frame, textvariable=self.seal_warning_text, width=18)
        warn_e.grid(row=row, column=1, sticky=tk.W, padx=2)
        warn_e.bind("<KeyRelease>", lambda e: self._redraw_seal_preview())
        row += 1

        ttk.Checkbutton(ctrl_frame, text="显示信息区", variable=self.seal_show_info,
                        command=self._redraw_seal_preview).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=0)
        row += 1

        ttk.Label(ctrl_frame, text="信息 LaTeX:", font=(UI_FONT, 9)).grid(row=row, column=0, sticky=tk.NW, pady=1)
        self.seal_info_text_w = tk.Text(ctrl_frame, height=2, width=20, font=(UI_FONT, 8), wrap=tk.WORD)
        self.seal_info_text_w.grid(row=row, column=1, sticky=tk.W, padx=2, pady=1)
        self.seal_info_text_w.insert(tk.END, self.seal_info_text.get())
        self.seal_info_text_w.bind("<KeyRelease>", lambda e: self._redraw_seal_preview())
        row += 1

        ttk.Checkbutton(ctrl_frame, text="显示装订线", variable=self.seal_show_binding,
                        command=self._redraw_seal_preview).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)

        self._redraw_seal_preview()

    def _seal_canvas_click(self, event):
        self._seal_drag_item = None
        cw = self.seal_canvas.winfo_width()
        ch = self.seal_canvas.winfo_height()
        margin = 40
        draw_w = cw - margin * 2
        scale = draw_w / 5.5

        for tag, key in [('line_main', self.seal_left_offset),
                         ('line_bind', self.seal_bind_offset),
                         ('line_info', self.seal_info_offset)]:
            x = margin + key.get() * scale
            if abs(event.x - x) < 12:
                self._seal_drag_item = tag
                self._seal_drag_start_x = event.x
                self.seal_canvas.config(cursor='sb_h_double_arrow')
                break

    def _seal_canvas_drag(self, event):
        if not self._seal_drag_item:
            return
        cw = self.seal_canvas.winfo_width()
        margin = 40
        draw_w = cw - margin * 2
        scale = draw_w / 5.5
        dx = (event.x - self._seal_drag_start_x) / scale
        self._seal_drag_start_x = event.x

        var_map = {
            'line_main': (self.seal_left_offset, 0.3, 5.0),
            'line_bind': (self.seal_bind_offset, 0.3, 4.0),
            'line_info': (self.seal_info_offset, 0.3, 3.0),
        }
        var, lo, hi = var_map[self._seal_drag_item]
        new_val = round(min(hi, max(lo, var.get() + dx)), 1)
        var.set(new_val)
        self._redraw_seal_preview()

    def _seal_canvas_release(self, event):
        self._seal_drag_item = None
        self.seal_canvas.config(cursor='')

    def _redraw_seal_preview(self, event=None):
        c = self.seal_canvas
        c.delete("all")
        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw < 50:
            return

        margin = 40
        top_margin = 25
        draw_w = cw - margin * 2
        draw_h = ch - top_margin - 20
        scale = draw_w / 5.5

        lw = self.seal_line_width.get()
        don = self.seal_dash_on.get()
        doff = self.seal_dash_off.get()
        warn = self.seal_warning_text.get()
        show_info = self.seal_show_info.get()
        show_binding = self.seal_show_binding.get()
        left = self.seal_left_offset.get()
        bind_off = self.seal_bind_offset.get()
        info_off = self.seal_info_offset.get()
        line_type = self.seal_line_type.get()
        symbol = self.seal_symbol.get()
        sym_interval = self.seal_symbol_interval.get()

        # map line type to canvas dash tuple
        if line_type == 'solid':
            dash_px = ()
        elif line_type == 'dashed':
            dash_px = (don * 2, doff * 2)
        elif line_type == 'dotted':
            dash_px = (1, 3)
        elif line_type == 'dashdot':
            dash_px = (4, 2, 1, 2)
        else:
            dash_px = ()

        line_color = '#2b5797'
        bind_color = '#8ab4f8'
        info_color = '#2e7d32'

        c.create_rectangle(margin, top_margin, margin + draw_w, top_margin + draw_h,
                           fill='white', outline='#ddd', width=1)

        c.create_line(margin, top_margin + 10, margin, top_margin + draw_h - 10,
                      fill='#ddd', width=1, dash=(2, 4))
        # vertical text via char-by-char stacking
        vert_label = "页面左边"
        ch_h = 12
        for i, ch in enumerate(vert_label):
            c.create_text(margin - 4, top_margin + 12 + i * ch_h,
                          text=ch, anchor=tk.E, font=(UI_FONT, 8), fill='#999')

        def draw_symbols(x_px, y_top, y_bot, color):
            if symbol == 'none':
                return
            sym_ch = {'cross': '×', 'diamond': '◆', 'star': '★'}.get(symbol, '')
            if not sym_ch:
                return
            interval_px = sym_interval * scale
            if interval_px < 8:
                return
            y = y_top + interval_px
            while y < y_bot:
                c.create_text(x_px, y, text=sym_ch,
                              font=(UI_FONT, 9), fill=color, anchor=tk.CENTER)
                y += interval_px

        def draw_vert_line(x, color, label, draggable=True):
            x_px = margin + x * scale
            y_top = top_margin + 10
            y_bot = top_margin + draw_h - 10
            c.create_line(x_px, y_top, x_px, y_bot,
                          fill=color, width=lw * 4 + 1, dash=dash_px,
                          tags=('line', f'line_{label}') if draggable else ())
            c.create_text(x_px, top_margin + draw_h - 4, text=f"{x:.1f}cm",
                          anchor=tk.N, font=(UI_FONT, 7), fill=color)
            draw_symbols(x_px, y_top, y_bot, color)
            if draggable:
                handle_h = 14
                c.create_rectangle(x_px - 6, top_margin + 8, x_px + 6, top_margin + 8 + handle_h,
                                   fill=color, outline='white', width=1,
                                   tags=('drag_handle', f'line_{label}'))
                c.create_text(x_px, top_margin + 8 + handle_h // 2,
                              text="⇔", font=(UI_FONT, 7), fill='white',
                              tags=('drag_handle', f'line_{label}'))

        draw_vert_line(left, line_color, 'main', True)
        if show_binding:
            draw_vert_line(bind_off, bind_color, 'bind', True)

        ch_h = 12

        if show_info:
            ix = margin + info_off * scale
            y_top = top_margin + 30
            y_bot = top_margin + draw_h - 30
            c.create_line(ix, y_top, ix, y_bot,
                          fill=info_color, width=lw * 3 + 1, dash=(2, 4),
                          tags=('line', 'line_info'))
            c.create_text(ix, top_margin + draw_h - 4, text=f"{info_off:.1f}cm",
                          anchor=tk.N, font=(UI_FONT, 7), fill=info_color)
            c.create_rectangle(ix - 6, top_margin + 8, ix + 6, top_margin + 8 + 14,
                               fill=info_color, outline='white',
                               tags=('drag_handle', 'line_info'))
            c.create_text(ix, top_margin + 8 + 7, text="⇔",
                          font=(UI_FONT, 7), fill='white',
                          tags=('drag_handle', 'line_info'))

            # info text rendered as vertical character stack
            info_chars = list("学院  专业  考生号")
            total_info_h = len(info_chars) * ch_h
            info_start_y = top_margin + draw_h // 2 - total_info_h // 2 - 40
            for i, ch in enumerate(info_chars):
                c.create_text(margin + draw_w // 2, info_start_y + i * ch_h,
                              text=ch, anchor=tk.CENTER,
                              font=(UI_FONT, 8, 'bold'), fill=info_color)
        else:
            info_start_y = top_margin + draw_h // 2
            total_info_h = 0

        # warning text below info text
        short_warn = warn if len(warn) <= 15 else warn[:12] + ".."
        warn_chars = list(f"※※ {short_warn} ※※")
        total_warn_h = len(warn_chars) * ch_h
        warn_start_y = info_start_y + total_info_h + 15
        for i, ch in enumerate(warn_chars):
            c.create_text(margin + draw_w // 2, warn_start_y + i * ch_h,
                          text=ch, anchor=tk.CENTER,
                          font=(UI_FONT, 8, 'bold'), fill='#c33')

        c.create_text(margin + draw_w // 2, top_margin + 8,
                      text="← 左侧页面区域 →", anchor=tk.S,
                      font=(UI_FONT, 8), fill='#aaa')

    # ──────────────────────────────────────────────
    # 2. 评分表设计
    # ──────────────────────────────────────────────
    def _build_score_tab(self, parent):
        self.score_show_total = tk.BooleanVar(value=True)
        self.score_show_per_type = tk.BooleanVar(value=True)
        self.score_table_style = tk.StringVar(value="tabular")
        self.score_include_reviewer = tk.BooleanVar(value=True)

        f = ttk.LabelFrame(parent, text="评分表设置", padding=4)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Checkbutton(f, text="生成总评分表", variable=self.score_show_total).pack(anchor=tk.W, pady=1)
        ttk.Checkbutton(f, text="各题型单独评分表", variable=self.score_show_per_type).pack(anchor=tk.W, pady=1)
        ttk.Checkbutton(f, text="包含阅卷人/复核人列", variable=self.score_include_reviewer).pack(anchor=tk.W, pady=1)

        style_f = ttk.Frame(f)
        style_f.pack(fill=tk.X, pady=2)
        ttk.Label(style_f, text="表格样式:").pack(side=tk.LEFT)
        ttk.Combobox(style_f, textvariable=self.score_table_style, values=["tabular", "tabularx", "longtable"], width=10, state="readonly").pack(side=tk.LEFT, padx=2)

        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
        ttk.Label(f, text="评分表预览:", font=(UI_FONT, 9, 'bold')).pack(anchor=tk.W, pady=1)

        preview_frame = ttk.Frame(f)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=1)
        self.score_preview_canvas = tk.Canvas(preview_frame, bg='white', highlightthickness=0)
        vsb = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.score_preview_canvas.yview)
        hsb = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.score_preview_canvas.xview)
        self.score_preview_canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.score_preview_canvas.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        self.score_preview_canvas.bind('<Configure>', lambda e: self._refresh_score_preview())

        self.score_show_total.trace_add('write', lambda *_: self._refresh_score_preview())
        self.score_show_per_type.trace_add('write', lambda *_: self._refresh_score_preview())
        self.score_include_reviewer.trace_add('write', lambda *_: self._refresh_score_preview())
        self.score_table_style.trace_add('write', lambda *_: self._refresh_score_preview())

        self._refresh_score_preview()

    def _refresh_score_preview(self, event=None):
        cw = self.score_preview_canvas.winfo_width()
        ch = self.score_preview_canvas.winfo_height()
        if cw < 20:
            cw = 400
        if ch < 20:
            ch = 150
        self.score_preview_canvas.delete('all')

        items = self._get_item_types_from_rows()
        if not items:
            self.score_preview_canvas.create_text(cw / 2, ch / 2, text='请先在「题型设置」中添加题型', fill='#888', font=(UI_FONT, 9))
            return

        has_reviewer = self.score_include_reviewer.get()
        n = len(items)

        # compute scores
        scores = []
        total = 0
        for row in self.item_rows:
            count = int(row['item_count'].get() or 0)
            score = float(row['item_score'].get() or 0)
            type_total = count * score
            scores.append(f"{type_total:.1f}分" if type_total != int(type_total) else f"{int(type_total)}分")
            total += type_total
        total_str = f"{total:.1f}分" if total != int(total) else f"{int(total)}分"

        # determine column layout with wrapping
        label_w = 55
        total_w_col = 55
        reviewer_w = 65 if has_reviewer else 0
        item_min_w = 70
        available = cw - 20
        cols_per_row = max(1, int((available - label_w - total_w_col - reviewer_w) / item_min_w))

        # split items into chunks
        chunks = []
        for i in range(0, n, cols_per_row):
            chunks.append(list(range(i, min(i + cols_per_row, n))))

        row_h = 26
        header_h = 30
        data_rows = 3 if has_reviewer else 2
        gap = 8

        total_h = 0
        table_layouts = []
        for chunk in chunks:
            col_widths = [label_w]
            for _ in chunk:
                col_widths.append(item_min_w)
            col_widths.append(total_w_col)
            if has_reviewer:
                col_widths.append(reviewer_w)
            tw = sum(col_widths) + len(col_widths) + 1
            th = header_h + data_rows * row_h + (data_rows + 1) + 1
            table_layouts.append((col_widths, tw, th))
            total_h += th + gap
        total_h = max(total_h - gap, th)

        self.score_preview_canvas.config(scrollregion=(0, 0, max(cw, max(t[1] for t in table_layouts) + 10), total_h))

        font = (UI_FONT, 9)
        bold_font = (UI_FONT, 9, 'bold')
        line_color = '#888'

        y_offset = 0
        for ci_idx, chunk in enumerate(chunks):
            col_widths, tw, th = table_layouts[ci_idx]

            # build headers and data for this chunk
            chunk_headers = ['题型'] + [items[i] for i in chunk] + ['总分']
            if has_reviewer:
                chunk_headers.append('总分复核人')

            chunk_scores = [scores[i] for i in chunk]
            chunk_data = [
                ['满分值'] + chunk_scores + [total_str] + ([''] if has_reviewer else []),
                ['实得分'] + [''] * (len(chunk) + 1) + ([''] if has_reviewer else []),
            ]
            if has_reviewer:
                chunk_data.append(['阅卷人'] + [''] * (len(chunk) + 2))

            # ── cell backgrounds ──
            y0 = y_offset + header_h + 1
            for ri, row_data in enumerate(chunk_data):
                x = 1
                for cc in range(len(row_data)):
                    bg = '#f0f2f5' if ri == 0 else '#f8f8f8' if ri % 2 == 0 else 'white'
                    self.score_preview_canvas.create_rectangle(
                        x, y0 + ri * row_h, x + col_widths[cc], y0 + ri * row_h + row_h,
                        fill=bg, outline='')
                    x += col_widths[cc] + 1

            # ── grid lines ──
            def vline(x, y_top=0, y_bot=y_offset + th):
                self.score_preview_canvas.create_line(x, y_top, x, y_bot, fill=line_color, width=1)
            def hline(y, x_left=0, x_right=tw):
                self.score_preview_canvas.create_line(x_left, y, x_right, y, fill=line_color, width=1)

            acc = 0
            for cc in range(len(col_widths) + 1):
                vline(acc)
                if cc < len(col_widths):
                    acc += col_widths[cc] + 1

            acc = y_offset
            hline(acc)
            acc += header_h
            hline(acc)
            for _ in range(data_rows):
                acc += row_h
                hline(acc)

            # ── header text ──
            acc = 1
            for i, h in enumerate(chunk_headers):
                self.score_preview_canvas.create_text(acc + col_widths[i] / 2, y_offset + header_h / 2,
                    text=h, fill='#111', font=bold_font, anchor='center')
                acc += col_widths[i] + 1

            # ── data cell text ──
            for ri, row_data in enumerate(chunk_data):
                acc = 1
                for cc, val in enumerate(row_data):
                    cx = acc + col_widths[cc] / 2
                    cy = y0 + ri * row_h + row_h / 2
                    self.score_preview_canvas.create_text(cx, cy, text=val, fill='#333', font=font, anchor='center')
                    acc += col_widths[cc] + 1

            y_offset += th + gap

    # ──────────────────────────────────────────────
    # 3. 页眉页脚设计
    # ──────────────────────────────────────────────
    def _build_header_footer_tab(self, parent):
        self.hf_left_header = tk.StringVar(value="\\miji \\quad 启用前")
        self.hf_center_header = tk.StringVar(value="")
        self.hf_right_header = tk.StringVar(value="第 \\thepage 页 / 共 \\pageref{LastPage} 页")
        self.hf_header_rule = tk.BooleanVar(value=True)
        self.hf_header_rule_width = tk.DoubleVar(value=0.5)
        self.hf_left_footer = tk.StringVar(value="")
        self.hf_center_footer = tk.StringVar(value="")
        self.hf_right_footer = tk.StringVar(value="")
        self.hf_footer_rule = tk.BooleanVar(value=False)
        self.hf_footer_rule_width = tk.DoubleVar(value=0.5)

        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # ── Top area: Header + Footer side by side ──
        top_frame = ttk.Frame(parent)
        top_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 3))
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)

        # ── Header (left) ──
        hf = ttk.LabelFrame(top_frame, text="页眉设置", padding=4)
        hf.grid(row=0, column=0, sticky='ew', padx=(0, 3))
        hf.grid_columnconfigure(1, weight=1)

        ttk.Label(hf, text="左:").grid(row=0, column=0, sticky=tk.W, pady=1)
        ttk.Entry(hf, textvariable=self.hf_left_header).grid(row=0, column=1, sticky=tk.EW, padx=3, pady=1)
        ttk.Label(hf, text="中:").grid(row=1, column=0, sticky=tk.W, pady=1)
        ttk.Entry(hf, textvariable=self.hf_center_header).grid(row=1, column=1, sticky=tk.EW, padx=3, pady=1)
        ttk.Label(hf, text="右:").grid(row=2, column=0, sticky=tk.W, pady=1)
        ttk.Entry(hf, textvariable=self.hf_right_header).grid(row=2, column=1, sticky=tk.EW, padx=3, pady=1)

        rf = ttk.Frame(hf)
        rf.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        ttk.Checkbutton(rf, text="分隔线", variable=self.hf_header_rule).pack(side=tk.LEFT)
        ttk.Label(rf, text=" 线宽:").pack(side=tk.LEFT)
        ttk.Spinbox(rf, from_=0, to=3, increment=0.1, textvariable=self.hf_header_rule_width, width=4).pack(side=tk.LEFT)

        # ── Footer (right) ──
        ff = ttk.LabelFrame(top_frame, text="页脚设置", padding=4)
        ff.grid(row=0, column=1, sticky='ew', padx=(3, 0))
        ff.grid_columnconfigure(1, weight=1)

        ttk.Label(ff, text="左:").grid(row=0, column=0, sticky=tk.W, pady=1)
        ttk.Entry(ff, textvariable=self.hf_left_footer).grid(row=0, column=1, sticky=tk.EW, padx=3, pady=1)
        ttk.Label(ff, text="中:").grid(row=1, column=0, sticky=tk.W, pady=1)
        ttk.Entry(ff, textvariable=self.hf_center_footer).grid(row=1, column=1, sticky=tk.EW, padx=3, pady=1)
        ttk.Label(ff, text="右:").grid(row=2, column=0, sticky=tk.W, pady=1)
        ttk.Entry(ff, textvariable=self.hf_right_footer).grid(row=2, column=1, sticky=tk.EW, padx=3, pady=1)

        rf2 = ttk.Frame(ff)
        rf2.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        ttk.Checkbutton(rf2, text="分隔线", variable=self.hf_footer_rule).pack(side=tk.LEFT)
        ttk.Label(rf2, text=" 线宽:").pack(side=tk.LEFT)
        ttk.Spinbox(rf2, from_=0, to=3, increment=0.1, textvariable=self.hf_footer_rule_width, width=4).pack(side=tk.LEFT)

        # ── Preview area (bottom, fills remaining space) ──
        prev_f = ttk.LabelFrame(parent, text="页眉页脚预览", padding=3)
        prev_f.grid(row=1, column=0, columnspan=2, sticky='nsew')
        prev_f.grid_columnconfigure(0, weight=1)
        prev_f.grid_rowconfigure(0, weight=1)

        self.hf_preview_canvas = tk.Canvas(prev_f, bg='white', highlightthickness=0)
        self.hf_preview_canvas.grid(row=0, column=0, sticky='nsew')
        self.hf_preview_canvas.bind('<Configure>', lambda e: self._refresh_hf_preview())

        for var in (self.hf_left_header, self.hf_center_header, self.hf_right_header,
                    self.hf_left_footer, self.hf_center_footer, self.hf_right_footer,
                    self.hf_header_rule, self.hf_header_rule_width,
                    self.hf_footer_rule, self.hf_footer_rule_width):
            var.trace_add('write', lambda *_: self._refresh_hf_preview())
        self._refresh_hf_preview()

    def _refresh_hf_preview(self, event=None):
        c = self.hf_preview_canvas
        c.delete('all')
        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw < 20:
            cw = 400
        if ch < 20:
            ch = 120

        margin = 20
        header_h = 30
        footer_h = 30
        page_h = ch - margin * 2

        # Page border
        c.create_rectangle(margin, margin, cw - margin, margin + page_h, outline='#ccc', width=1)

        # Header line
        if self.hf_header_rule.get():
            lw = max(0.5, self.hf_header_rule_width.get())
            c.create_line(margin, margin + header_h, cw - margin, margin + header_h, fill='#333', width=lw)

        # Footer line
        if self.hf_footer_rule.get():
            lw = max(0.5, self.hf_footer_rule_width.get())
            c.create_line(margin, margin + page_h - footer_h, cw - margin, margin + page_h - footer_h, fill='#333', width=lw)

        font = (UI_FONT, 8)
        # Header text
        lh = self.hf_left_header.get().strip()
        ch_text = self.hf_center_header.get().strip()
        rh = self.hf_right_header.get().strip()
        if lh:
            c.create_text(margin + 4, margin + header_h / 2, text=lh[:30], anchor=tk.W, font=font, fill='#333')
        if ch_text:
            c.create_text(cw / 2, margin + header_h / 2, text=ch_text[:30], anchor=tk.CENTER, font=font, fill='#333')
        if rh:
            c.create_text(cw - margin - 4, margin + header_h / 2, text=rh[:30], anchor=tk.E, font=font, fill='#333')

        # Footer text
        lf = self.hf_left_footer.get().strip()
        cf = self.hf_center_footer.get().strip()
        rf = self.hf_right_footer.get().strip()
        fy = margin + page_h - footer_h / 2
        if lf:
            c.create_text(margin + 4, fy, text=lf[:30], anchor=tk.W, font=font, fill='#333')
        if cf:
            c.create_text(cw / 2, fy, text=cf[:30], anchor=tk.CENTER, font=font, fill='#333')
        if rf:
            c.create_text(cw - margin - 4, fy, text=rf[:30], anchor=tk.E, font=font, fill='#333')

        # Labels
        c.create_text(cw / 2, margin + 4, text="← 页眉区域 →", anchor=tk.N, font=(UI_FONT, 7), fill='#aaa')
        c.create_text(cw / 2, margin + page_h - 4, text="← 页脚区域 →", anchor=tk.S, font=(UI_FONT, 7), fill='#aaa')

    # ──────────────────────────────────────────────
    # 4. 页面设计（纸张、方向、双栏、密封线/评分表/页眉页脚位置）
    # ──────────────────────────────────────────────
    def _build_page_design_tab(self, parent):
        self.page_paper_size = tk.StringVar(value="a3paper")
        self.page_orientation = tk.StringVar(value="landscape")
        self.page_twocolumn = tk.BooleanVar(value=True)
        self.page_seal_side = tk.StringVar(value="left")
        self.page_seal_display = tk.StringVar(value="side")
        self.page_score_position = tk.StringVar(value="start")
        self.page_hf_display = tk.StringVar(value="all")

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        left_frame = ttk.Frame(parent)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 3), pady=1)
        left_frame.grid_columnconfigure(0, weight=1)

        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(3, 0), pady=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # ── Left column: Page & Layout settings ──
        left_container = ttk.Frame(left_frame)
        left_container.pack(fill=tk.BOTH, expand=True)
        left_container.grid_columnconfigure(0, weight=1)
        left_container.grid_rowconfigure(0, weight=0)
        left_container.grid_rowconfigure(1, weight=0)
        left_container.grid_rowconfigure(2, weight=1)

        # ── Paper & Layout ──
        f = ttk.LabelFrame(left_container, text="纸张与排版", padding=4)
        f.grid(row=0, column=0, sticky='ew', pady=(0, 3))
        f.grid_columnconfigure(1, weight=1)

        r = 0
        ttk.Label(f, text="纸张大小:").grid(row=r, column=0, sticky=tk.W, pady=1)
        paper_cb = ttk.Combobox(f, textvariable=self.page_paper_size,
                                values=["a3paper", "a4paper", "a5paper", "b4paper", "b5paper"],
                                width=10, state="readonly")
        paper_cb.grid(row=r, column=1, sticky=tk.W, padx=3)
        paper_cb.current(0)
        r += 1

        ttk.Label(f, text="纸张方向:").grid(row=r, column=0, sticky=tk.W, pady=1)
        orient_f = ttk.Frame(f)
        orient_f.grid(row=r, column=1, sticky=tk.W, padx=3)
        ttk.Radiobutton(orient_f, text="纵向", variable=self.page_orientation,
                        value="portrait").pack(side=tk.LEFT)
        ttk.Radiobutton(orient_f, text="横向", variable=self.page_orientation,
                        value="landscape").pack(side=tk.LEFT, padx=(6, 0))
        r += 1

        ttk.Checkbutton(f, text="双栏排版", variable=self.page_twocolumn).grid(
            row=r, column=0, columnspan=2, sticky=tk.W, pady=1)

        # ── Seal line settings ──
        f2 = ttk.LabelFrame(left_container, text="密封线设置", padding=4)
        f2.grid(row=1, column=0, sticky='ew', pady=(0, 3))
        f2.grid_columnconfigure(1, weight=1)

        ttk.Label(f2, text="显示方式:").grid(row=0, column=0, sticky=tk.W, pady=1)
        self.seal_display_labels = ["不显示", "侧边显示", "顶端显示"]
        self.seal_display_map = {"不显示": "hidden", "侧边显示": "side", "顶端显示": "top"}
        self._seal_disp_cb = ttk.Combobox(f2, values=self.seal_display_labels, width=10, state="readonly")
        self._seal_disp_cb.grid(row=0, column=1, sticky=tk.W, padx=3)
        self._seal_disp_cb.current(1)
        self._seal_disp_cb.bind("<<ComboboxSelected>>", lambda e: self.page_seal_display.set(self.seal_display_map[self._seal_disp_cb.get()]))

        ttk.Label(f2, text="侧边位置:").grid(row=1, column=0, sticky=tk.W, pady=1)
        pos_f = ttk.Frame(f2)
        pos_f.grid(row=1, column=1, sticky=tk.W, padx=3)
        ttk.Radiobutton(pos_f, text="左侧", variable=self.page_seal_side,
                        value="left").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(pos_f, text="右侧", variable=self.page_seal_side,
                        value="right").pack(side=tk.LEFT)

        # ── Score table & Header/Footer ──
        f3 = ttk.LabelFrame(left_container, text="评分表与页眉页脚", padding=4)
        f3.grid(row=2, column=0, sticky='ew')
        f3.grid_columnconfigure(1, weight=1)

        self.score_position_labels = ["start=试卷开头", "end=试卷结尾"]
        self.score_position_map = {"start=试卷开头": "start", "end=试卷结尾": "end"}
        self.hf_display_labels = ["all=全部页面", "first=仅正文页"]
        self.hf_display_map = {"all=全部页面": "all", "first=仅正文页": "first"}

        ttk.Label(f3, text="评分表位置:").grid(row=0, column=0, sticky=tk.W, pady=1)
        self._score_pos_cb = ttk.Combobox(f3, values=self.score_position_labels, width=12, state="readonly")
        self._score_pos_cb.grid(row=0, column=1, sticky=tk.W, padx=3)
        self._score_pos_cb.current(0)
        self._score_pos_cb.bind("<<ComboboxSelected>>", lambda e: self.page_score_position.set(self.score_position_map[self._score_pos_cb.get()]))

        ttk.Label(f3, text="页眉页脚:").grid(row=1, column=0, sticky=tk.W, pady=1)
        self._hf_disp_cb = ttk.Combobox(f3, values=self.hf_display_labels, width=12, state="readonly")
        self._hf_disp_cb.grid(row=1, column=1, sticky=tk.W, padx=3)
        self._hf_disp_cb.current(0)
        self._hf_disp_cb.bind("<<ComboboxSelected>>", lambda e: self.page_hf_display.set(self.hf_display_map[self._hf_disp_cb.get()]))

        # ── Right column: Font Settings ──
        ff = ttk.LabelFrame(right_frame, text="字体设置", padding=6)
        ff.pack(fill=tk.BOTH, expand=True)
        ff.grid_columnconfigure(1, weight=1)

        font_size_options = [
            ("初号(42pt)", "-0"), ("小初(36pt)", "0"),
            ("一号(28pt)", "-1"), ("小一(24pt)", "1"),
            ("二号(22pt)", "-2"), ("小二(18pt)", "2"),
            ("三号(16pt)", "-3"), ("小三(15pt)", "3"),
            ("四号(14pt)", "-4"), ("小四(12pt)", "4"),
            ("五号(10.5pt)", "-5"), ("小五(9pt)", "5"),
            ("六号(7.5pt)", "-6"), ("小六(6.5pt)", "6"),
            ("七号(5.25pt)", "7"), ("八号(4.5pt)", "8"),
        ]
        self.font_size_labels = [item[0] for item in font_size_options]
        self.font_size_map = dict(font_size_options)

        font_specs = [
            ('main_title',   '试卷主标题', '二号(22pt)', True),
            ('sub_title',    '试卷子标题', '二号(22pt)', True),
            ('section_title','大题内容',   '四号(14pt)', True),
            ('item_content', '小题内容',   '五号(10.5pt)', False),
            ('header',       '页眉',       '五号(10.5pt)', False),
            ('footer',       '页脚',       '五号(10.5pt)', False),
            ('seal_line',    '密封线',     '五号(10.5pt)', True),
        ]
        self.font_settings = {}
        for i, (key, label, default_size, default_bold) in enumerate(font_specs):
            size_var = tk.StringVar(value=default_size)
            bold_var = tk.BooleanVar(value=default_bold)
            ttk.Label(ff, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=1, padx=(0, 4))
            ttk.Combobox(ff, textvariable=size_var, values=self.font_size_labels,
                         width=14, state="readonly").grid(row=i, column=1, pady=1, sticky=tk.W)
            ttk.Checkbutton(ff, text="加粗", variable=bold_var).grid(row=i, column=2, pady=1, padx=(6, 0))
            self.font_settings[key] = {'size': size_var, 'bold': bold_var, '_label': label}

    # ──────────────────────────────────────────────
    # 5. 预览与保存
    # ──────────────────────────────────────────────
    def _build_preview_tab(self, parent):
        btn_f = ttk.Frame(parent)
        btn_f.pack(fill=tk.X, pady=(0, 6))
        self._gen_btn = ttk.Button(btn_f, text="  生成预览  ", command=self._generate_preview)
        self._gen_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="  保存模板  ", command=self._save_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_f, text="  打开PDF  ", command=self._open_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Label(btn_f, text="  文件名:").pack(side=tk.LEFT, padx=(10, 0))
        self.preview_filename = tk.StringVar(value=f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        ttk.Entry(btn_f, textvariable=self.preview_filename, width=25).pack(side=tk.LEFT, padx=2)

        status_f = ttk.Frame(parent)
        status_f.pack(fill=tk.X, pady=(0, 4))
        self._compile_progress = ttk.Progressbar(status_f, mode='indeterminate', length=200)
        self._compile_status = ttk.Label(status_f, text="", foreground='#555')
        self._compile_progress.pack(side=tk.LEFT, padx=(0, 8))
        self._compile_status.pack(side=tk.LEFT)

        paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        src_f = ttk.LabelFrame(paned, text="生成的 LaTeX 源码", padding=4)
        paned.add(src_f, weight=1)
        self.preview_text = tk.Text(src_f, font=('Consolas', 9), wrap=tk.NONE, width=80, height=15)
        src_scroll_y = ttk.Scrollbar(src_f, orient=tk.VERTICAL, command=self.preview_text.yview)
        src_scroll_x = ttk.Scrollbar(src_f, orient=tk.HORIZONTAL, command=self.preview_text.xview)
        self.preview_text.configure(yscrollcommand=src_scroll_y.set, xscrollcommand=src_scroll_x.set)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        src_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        src_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        log_f = ttk.LabelFrame(paned, text="编译日志", padding=4)
        paned.add(log_f, weight=1)
        self.log_text = tk.Text(log_f, font=('Consolas', 9), height=8, fg='#333')
        log_scroll = ttk.Scrollbar(log_f, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._generated_latex = ""
        self._pdf_path = None

    # ──────────────────────────────────────────────
    # 核心: 生成 LaTeX 模板（兼容 engine 占位符格式）
    # ──────────────────────────────────────────────
    def generate_template_latex(self):
        settings = self.collect_settings()
        
        per_type_items = ''
        active_rows = []
        for row in self.item_rows:
            count = int(row['item_count'].get() or 0)
            if count == 0:
                continue
            active_rows.append(row)
            section = TemplateBuilder.create_template(
                '_item_type', 5, 1.0, '_ti_hao', {},
                show_score_table=settings['scoring']['show_per_type'],
                table_style=settings['scoring'].get('table_style', 'tabular'),
                font_settings=settings.get('fonts', {}))
            per_type_items += section + '\n'
        
        # Build item_info list for score table generation
        item_info_list = []
        for row in active_rows:
            item_info_list.append({
                'item_type': row['item_type'].get().strip(),
                'item_count': int(row['item_count'].get() or 0),
                'item_score': float(row['item_score'].get() or 0)
            })
        
        paper_info = {
            'exam_sub': 'sub_title_x',
            'exam_main': 'main_title_x',
            'exam_time': 'exam_time_x',
            'all_score': 'score_x',
            'item_info': item_info_list
        }

        return TemplateBuilder.create_paper(paper_info, None, settings)

    def _build_sealing_line_latex(self):
        seal_display = getattr(self, 'page_seal_display', None)
        display_mode = seal_display.get() if seal_display else 'side'
        
        if display_mode == 'hidden':
            return ""
        
        if display_mode == 'top':
            return self._build_top_seal_line_latex()
        
        # default: side mode
        lines = []
        lines.append(r"\def\sealline{%")
        lines.append(r"\begin{tikzpicture}[remember picture,overlay]")

        left = round(self.seal_left_offset.get(), 1)
        lw = round(self.seal_line_width.get(), 1)
        don = self.seal_dash_on.get()
        doff = self.seal_dash_off.get()
        warn = self.seal_warning_text.get()

        dash = f"dash pattern=on {don}pt off {doff}pt"
        lines.append(f"    \\draw[black,line width={lw}pt,{dash}]")
        lines.append(f"        ([xshift={left}cm]current page.north west) -- ([xshift={left}cm]current page.south west);")

        seal_fs = self.font_settings.get('seal_line', {})
        seal_size_label = seal_fs.get('size', tk.StringVar(value='五号(10.5pt)'))
        if isinstance(seal_size_label, tk.StringVar):
            seal_size_label = seal_size_label.get()
        seal_zihao = self.font_size_map.get(seal_size_label, '-5')
        seal_bold = seal_fs.get('bold', tk.BooleanVar(value=True))
        if isinstance(seal_bold, tk.BooleanVar):
            seal_bold = seal_bold.get()
        seal_font = f"\\zihao{{{seal_zihao}}}" + ("\\bfseries" if seal_bold else "")

        warn_line = "- " * 20 + f"$\\bigstar$ $\\bigstar$ {warn} $\\bigstar$ $\\bigstar$" + " -" * 20
        lines.append(f"    \\node[rotate=90,anchor=south,font={seal_font},inner sep=1pt]")
        lines.append(f"        at ([xshift={left-0.2:.1f}cm,yshift=-0.2cm]current page.west) {{{warn_line}}};")

        if self.seal_show_binding.get():
            bind_offset = round(left - 0.7, 1) if left > 1.0 else 0.8
            lines.append(f"     \\draw[black,line width={lw}pt,{dash}]")
            lines.append(f"        ([xshift={bind_offset}cm]current page.north west) -- ([xshift={bind_offset}cm]current page.south west);")

        if self.seal_show_info.get():
            info_text = self.seal_info_text_w.get("1.0", tk.END).strip()
            if not info_text:
                info_text = self.seal_info_text.get()
            info_offset = round(self.seal_info_offset.get(), 1)
            lines.append(f"    \\node[rotate=90,anchor=south,font={seal_font},inner sep=0pt]")
            lines.append(f"        at ([xshift={info_offset}cm]current page.west) {{{info_text}}};")

        lines.append(r"\end{tikzpicture}%")
        lines.append(r"}")

        lines.append(r"\def\seallinex{%")
        lines.append(r"\begin{tikzpicture}[remember picture,overlay]")
        lines.append(f"    \\draw[black,line width={lw}pt,{dash}]")
        lines.append(f"        ([xshift={left}cm]current page.north west) -- ([xshift={left}cm]current page.south west);")
        lines.append(f"    \\node[rotate=90,anchor=south,font={seal_font},inner sep=1pt]")
        lines.append(f"        at ([xshift={left-0.2:.1f}cm,yshift=-0.2cm]current page.west) {{{warn_line}}};")
        if self.seal_show_binding.get():
            bind_offset = round(left - 0.7, 1) if left > 1.0 else 0.8
            lines.append(f"     \\draw[black,line width={lw}pt,{dash}]")
            lines.append(f"        ([xshift={bind_offset}cm]current page.north west) -- ([xshift={bind_offset}cm]current page.south west);")
        lines.append(r"\end{tikzpicture}%")
        lines.append(r"}")
        return "\n".join(lines)

    def _build_top_seal_line_latex(self):
        """Build seal line LaTeX for top of page position"""
        lines = []
        lw = round(self.seal_line_width.get(), 1)
        don = self.seal_dash_on.get()
        doff = self.seal_dash_off.get()
        warn = self.seal_warning_text.get()
        show_info = self.seal_show_info.get()
        show_binding = self.seal_show_binding.get()
        
        info_text = self.seal_info_text_w.get("1.0", tk.END).strip()
        if not info_text:
            info_text = self.seal_info_text.get()
        
        seal_fs = self.font_settings.get('seal_line', {})
        seal_size_label = seal_fs.get('size', tk.StringVar(value='五号(10.5pt)'))
        if isinstance(seal_size_label, tk.StringVar):
            seal_size_label = seal_size_label.get()
        seal_zihao = self.font_size_map.get(seal_size_label, '-5')
        seal_bold = seal_fs.get('bold', tk.BooleanVar(value=True))
        if isinstance(seal_bold, tk.BooleanVar):
            seal_bold = seal_bold.get()
        seal_font_cmd = f"\\zihao{{{seal_zihao}}}" + ("\\bfseries" if seal_bold else "")
        
        lines.append(r"\def\sealline{%")
        lines.append(r"\begin{center}")
        lines.append(seal_font_cmd)
        
        if show_info and info_text:
            lines.append(info_text)
            lines.append(r"\\")
            lines.append(r"\vspace{3pt}")
        
        if show_binding:
            lines.append(f"\\rule{{\\textwidth}}{{{lw}pt}}")
            lines.append(r"\\")
            lines.append(r"\vspace{2pt}")
        
        lines.append(f"\\textbf{{{warn}}}")
        lines.append(r"\\")
        
        if show_binding:
            lines.append(r"\vspace{2pt}")
            lines.append(f"\\rule{{\\textwidth}}{{{lw}pt}}")
        
        lines.append(r"\end{center}%")
        lines.append(r"}")
        
        lines.append(r"\def\seallinex{%")
        lines.append(r"\begin{center}")
        lines.append(seal_font_cmd)
        lines.append(f"\\textbf{{{warn}}}")
        lines.append(r"\end{center}%")
        lines.append(r"}")
        return "\n".join(lines)

    def _build_header_footer_latex(self):
        lines = []
        lines.append(r"\pagestyle{fancy}")
        lines.append(r"\fancyhf{}")

        header_font = self._get_hf_font_cmd('header')
        footer_font = self._get_hf_font_cmd('footer')

        lh = self.hf_left_header.get().strip()
        ch = self.hf_center_header.get().strip()
        rh = self.hf_right_header.get().strip()
        if lh:
            lines.append(r"\lhead{" + header_font + " " + lh + "}")
        if ch:
            lines.append(r"\chead{" + header_font + " " + ch + "}")
        if rh:
            lines.append(r"\rhead{" + header_font + " " + rh + "}")

        lf = self.hf_left_footer.get().strip()
        cf = self.hf_center_footer.get().strip()
        rf = self.hf_right_footer.get().strip()
        if lf:
            lines.append(r"\lfoot{" + footer_font + " " + lf + "}")
        if cf:
            lines.append(r"\cfoot{" + footer_font + " " + cf + "}")
        if rf:
            lines.append(r"\rfoot{" + footer_font + " " + rf + "}")

        if self.hf_header_rule.get():
            lines.append(r"\renewcommand{\headrulewidth}{" + f"{self.hf_header_rule_width.get():.1f}pt" + "}")
        else:
            lines.append(r"\renewcommand{\headrulewidth}{0pt}")

        if self.hf_footer_rule.get():
            lines.append(r"\renewcommand{\footrulewidth}{" + f"{self.hf_footer_rule_width.get():.1f}pt" + "}")
        else:
            lines.append(r"\renewcommand{\footrulewidth}{0pt}")

        return "\n".join(lines)

    def _get_hf_font_cmd(self, key):
        fs = self.font_settings.get(key, {})
        size_var = fs.get('size')
        bold_var = fs.get('bold')
        if size_var:
            size_label = size_var.get()
            zihao = self.font_size_map.get(size_label, '-5')
        else:
            zihao = '-5'
        bold = bold_var.get() if bold_var else False
        cmd = f"\\zihao{{{zihao}}}"
        if bold:
            cmd += "\\bfseries"
        return cmd

    def _build_score_table_latex(self, items):
        if not items:
            return ""
        n = len(items)
        cols = n + 3
        table_style = self.score_table_style.get()
        lines = []
        lines.append(r"\begin{center}")
        lines.append(r"\zihao{5}")
        
        if table_style == 'tabular':
            lines.append(r"\begin{tabular}{" + ("|c" * cols) + "|}")
        elif table_style == 'tabularx':
            lines.append(r"\begin{tabularx}{\linewidth}{" + ("|X" * cols) + "|}")
        elif table_style == 'longtable':
            lines.append(r"\begin{longtable}{" + ("|c" * cols) + "|}")
        else:
            lines.append(r"\begin{tabular}{" + ("|c" * cols) + "|}")
            
        lines.append(r"\hline")

        header = "题型"
        for i in range(1, n + 1):
            header += f" & item_x_{i}"
        header += " & 总分 & 总分复核人 \\\\"
        lines.append(header)
        lines.append(r"\hline")

        scores = "满分值"
        for i in range(1, n + 1):
            scores += f" & item_x_{i}_s分"
        scores += f" & item_x_{n+1}_s分 & \\multirow{{2}}{{*}}{{}} \\\\"
        lines.append(scores)
        lines.append(r"\hline")
        lines.append("实得分" + " &" * (n + 2) + " \\\\")
        lines.append(r"\hline")

        if self.score_include_reviewer.get():
            lines.append("阅卷人" + " &" * (n + 2) + " \\\\")
            lines.append(r"\hline")

        if table_style == 'tabular':
            lines.append(r"\end{tabular}")
        elif table_style == 'tabularx':
            lines.append(r"\end{tabularx}")
        elif table_style == 'longtable':
            lines.append(r"\end{longtable}")
        else:
            lines.append(r"\end{tabular}")
            
        lines.append(r"\end{center}")
        return "\n".join(lines)

    def _get_item_types_from_rows(self):
        types = []
        for row in self.item_rows:
            t = row['item_type'].get().strip()
            count = int(row['item_count'].get() or 0)
            if t and count > 0:
                types.append(t)
        return types

    def refresh_score_list(self):
        self._refresh_score_preview()

    # ──────────────────────────────────────────────
    # 预览与保存
    # ──────────────────────────────────────────────
    def _make_compilable(self, latex):
        s = latex
        items = self._get_item_types_from_rows()
        n = len(items)

        # Replace score placeholders first (longer patterns) to avoid partial matches
        for i in range(n, 0, -1):
            s = s.replace(f"item_x_{i}_s分", f"{10}分")
            s = s.replace(f"item_x_{i}_s", f"{10}")
        
        # Replace item type placeholders
        for i in range(n, 0, -1):
            s = s.replace(f"item_x_{i}", items[i - 1] if i <= len(items) else f"题型{i}")
        
        # Replace total score placeholder
        s = s.replace(f"item_x_{n+1}_s分", f"{str(n*10)}分")
        s = s.replace(f"item_x_{n+1}_s", f"{str(n*10)}")

        # Replace exam info placeholders
        s = s.replace("main_title_x", "考试名称")
        s = s.replace("sub_title_x", "科目名称")
        s = s.replace("exam_time_x", "120")
        s = s.replace("score_x", "100")
        
        # Build sample items for preview
        sample_items = ""
        for i, item_type in enumerate(items, 1):
            sample_items += f"\\noindent\\textbf{{{i}、{item_type}}}\\par\\vspace{{4pt}}\n"
            sample_items += "\\begin{enumerate}\n"
            sample_items += "    \\item 示例题目内容\n"
            sample_items += "\\end{enumerate}\n\\vspace{8pt}\n"
        
        if not sample_items:
            sample_items = "\\noindent\\textbf{一、单项选择题}\\par\\vspace{4pt}\n\\begin{enumerate}\n    \\item 示例题目内容\n\\end{enumerate}"
        
        s = s.replace("items_x", sample_items)
        
        # Replace template-specific placeholders
        s = s.replace("_item_type", "单项选择题")
        s = s.replace("_ti_liang", "5")
        s = s.replace("_one_score", "1")
        s = s.replace("_all_score", "5")
        s = s.replace("_ti_hao", "一")
        s = s.replace("_yao_qiu", "请根据题目要求作答。")
        s = s.replace("_item_s", "\\item 示例题目内容")
        
        return s

    def _generate_preview(self):
        self.preview_text.delete("1.0", tk.END)
        self.log_text.delete("1.0", tk.END)
        self._compile_status.config(text="正在生成 LaTeX...")
        self._gen_btn.config(state=tk.DISABLED)
        self._compile_progress.start(10)

        raw_latex = self.generate_template_latex()
        # 模板样例脚本
        compilable_latex = self._make_compilable(raw_latex)
        
        self._generated_latex = compilable_latex
        self._raw_latex = raw_latex
        # 这里放模板脚本即可
        self.preview_text.insert(tk.END, compilable_latex)

        self._compile_status.config(text="正在编译，请稍候...")
        self._compile_progress.start(10)
        threading.Thread(target=self._compile_thread, daemon=True).start()

    def _compile_thread(self):
        root = self.parent.winfo_toplevel()
        compilable = self._generated_latex
        tex_file = TEMP_DIR / "template_preview.tex"
        stdout = stderr = ""
        success = False
        error_msg = ""

        try:
            tex_file.parent.mkdir(parents=True, exist_ok=True)
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(compilable)

            env = os.environ.copy()
            bundle = RESOURCE_DIR / "tectonic_bundle"
            if bundle.exists():
                env["TECTONIC_BUNDLE_DIR"] = str(bundle)
                env["TECTONIC_CACHE_DIR"] = str(bundle)
            env["TECTONIC_OFFLINE"] = "1"
            env["TECTONIC_NO_DOWNLOAD"] = "1"


            result = subprocess.run(
                [str(LATEX_PATH), "template_preview.tex"],
                cwd=TEMP_DIR,
                capture_output=True,
                text=False,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=120
            )
            stdout = result.stdout.decode("utf-8", errors="ignore")
            stderr = result.stderr.decode("utf-8", errors="ignore")
            pdf_path = TEMP_DIR / "template_preview.pdf"
            if pdf_path.exists():
                self._pdf_path = pdf_path
                success = True
            else:
                self._pdf_path = None
        except subprocess.TimeoutExpired:
            error_msg = "\n✗ 编译超时（>120秒）\n"
        except FileNotFoundError:
            error_msg = f"\n✗ 未找到 LaTeX 编译器: {LATEX_PATH}\n"
        except Exception as e:
            error_msg = f"\n✗ 错误: {e}\n"

        root.after(0, self._compile_done, stdout, stderr, success, error_msg)

    def _compile_done(self, stdout, stderr, success, error_msg):
        self._compile_progress.stop()
        self._compile_progress.config(value=0)
        self._gen_btn.config(state=tk.NORMAL)

        if error_msg:
            self.log_text.insert(tk.END, error_msg)
            self._compile_status.config(text="编译出错", foreground='#c33')
            return

        self.log_text.insert(tk.END, stdout[-2000:] if len(stdout) > 2000 else stdout)
        if stderr:
            self.log_text.insert(tk.END, "\n--- STDERR ---\n" + stderr[-1000:])

        if success:
            self._compile_status.config(text="编译完成 ✓", foreground='#1a73e8')
            self.log_text.insert(tk.END, "\n✓ 编译成功！PDF 已生成。\n")
            messagebox.showinfo("预览", "PDF 编译成功！点击「打开PDF」查看。")
        else:
            self._compile_status.config(text="编译失败 ✗", foreground='#c33')
            self.log_text.insert(tk.END, "\n✗ 编译失败，请检查 LaTeX 语法。\n")

    def _open_pdf(self):
        if self._pdf_path and self._pdf_path.exists():
            os.startfile(str(self._pdf_path))
        else:
            pdf_path = TEMP_DIR / "template_preview.pdf"
            if pdf_path.exists():
                self._pdf_path = pdf_path
                os.startfile(str(pdf_path))
            else:
                messagebox.showinfo("提示", "PDF 不存在，请先生成预览。")

    def collect_settings(self):
        return {
            'sealing': {
                'seal_left_offset': self.seal_left_offset.get(),
                'seal_bind_offset': self.seal_bind_offset.get(),
                'seal_info_offset': self.seal_info_offset.get(),
                'seal_line_width': self.seal_line_width.get(),
                'seal_dash_on': self.seal_dash_on.get(),
                'seal_dash_off': self.seal_dash_off.get(),
                'seal_warning_text': self.seal_warning_text.get(),
                'seal_show_info': self.seal_show_info.get(),
                'seal_info_text': self.seal_info_text_w.get("1.0", tk.END).strip() or self.seal_info_text.get(),
                'seal_show_binding': self.seal_show_binding.get(),
                'seal_line_type': self.seal_line_type.get(),
                'seal_symbol': self.seal_symbol.get(),
                'seal_symbol_interval': self.seal_symbol_interval.get(),
            },
            'header_footer': {
                'hf_left_header': self.hf_left_header.get(),
                'hf_center_header': self.hf_center_header.get(),
                'hf_right_header': self.hf_right_header.get(),
                'hf_header_rule': self.hf_header_rule.get(),
                'hf_header_rule_width': self.hf_header_rule_width.get(),
                'hf_left_footer': self.hf_left_footer.get(),
                'hf_center_footer': self.hf_center_footer.get(),
                'hf_right_footer': self.hf_right_footer.get(),
                'hf_footer_rule': self.hf_footer_rule.get(),
                'hf_footer_rule_width': self.hf_footer_rule_width.get(),
            },
            'scoring': {
                'show_total': self.score_show_total.get(),
                'show_per_type': self.score_show_per_type.get(),
                'table_style': self.score_table_style.get(),
                'include_reviewer': self.score_include_reviewer.get(),
            },
            'page': {
                'paper_size': self.page_paper_size.get(),
                'orientation': self.page_orientation.get(),
                'twocolumn': self.page_twocolumn.get(),
                'seal_side': self.page_seal_side.get(),
                'seal_display': self.page_seal_display.get(),
                'score_position': self.page_score_position.get(),
                'hf_display': self.page_hf_display.get(),
            },
            'fonts': {
                key: {
                    'size': self.font_size_map[var['size'].get()],
                    'bold': var['bold'].get(),
                }
                for key, var in self.font_settings.items()
            },
        }

    def _get_label_for_zihao(self, zihao_val):
        rev_map = {v: k for k, v in self.font_size_map.items()}
        return rev_map.get(zihao_val, '五号(10.5pt)')

    def apply_settings(self, settings):
        """Apply loaded settings to the template design panel"""
        if 'sealing' in settings:
            s = settings['sealing']
            self.seal_left_offset.set(s.get('seal_left_offset', 2.2))
            self.seal_bind_offset.set(s.get('seal_bind_offset', 1.5))
            self.seal_info_offset.set(s.get('seal_info_offset', 1.0))
            self.seal_line_width.set(s.get('seal_line_width', 0.8))
            self.seal_dash_on.set(s.get('seal_dash_on', 4))
            self.seal_dash_off.set(s.get('seal_dash_off', 2))
            self.seal_warning_text.set(s.get('seal_warning_text', '密封线内不准答题'))
            self.seal_show_info.set(s.get('seal_show_info', True))
            self.seal_show_binding.set(s.get('seal_show_binding', True))
            self.seal_line_type.set(s.get('seal_line_type', 'dashed'))
            self.seal_symbol.set(s.get('seal_symbol', 'none'))
            self.seal_symbol_interval.set(s.get('seal_symbol_interval', 2.0))
            if 'seal_info_text' in s:
                self.seal_info_text_w.delete("1.0", tk.END)
                self.seal_info_text_w.insert("1.0", s['seal_info_text'])
        if 'header_footer' in settings:
            s = settings['header_footer']
            self.hf_left_header.set(s.get('hf_left_header', '\\miji \\quad 启用前'))
            self.hf_center_header.set(s.get('hf_center_header', ''))
            self.hf_right_header.set(s.get('hf_right_header', '第 \\thepage 页 / 共 \\pageref{LastPage} 页'))
            self.hf_header_rule.set(s.get('hf_header_rule', True))
            self.hf_header_rule_width.set(s.get('hf_header_rule_width', 0.5))
            self.hf_left_footer.set(s.get('hf_left_footer', ''))
            self.hf_center_footer.set(s.get('hf_center_footer', ''))
            self.hf_right_footer.set(s.get('hf_right_footer', ''))
            self.hf_footer_rule.set(s.get('hf_footer_rule', False))
            self.hf_footer_rule_width.set(s.get('hf_footer_rule_width', 0.5))
        if 'scoring' in settings:
            s = settings['scoring']
            self.score_show_total.set(s.get('show_total', True))
            self.score_show_per_type.set(s.get('show_per_type', True))
            self.score_table_style.set(s.get('table_style', 'tabular'))
            self.score_include_reviewer.set(s.get('include_reviewer', True))
        if 'page' in settings:
            s = settings['page']
            self.page_paper_size.set(s.get('paper_size', 'a3paper'))
            self.page_orientation.set(s.get('orientation', 'landscape'))
            self.page_twocolumn.set(s.get('twocolumn', True))
            self.page_seal_side.set(s.get('seal_side', 'left'))
            seal_val = s.get('seal_display', 'side')
            self.page_seal_display.set(seal_val)
            seal_label = next((k for k, v in self.seal_display_map.items() if v == seal_val), self.seal_display_labels[1])
            self._seal_disp_cb.set(seal_label)
            sp_val = s.get('score_position', 'start')
            self.page_score_position.set(sp_val)
            sp_label = next((k for k, v in self.score_position_map.items() if v == sp_val), self.score_position_labels[0])
            self._score_pos_cb.set(sp_label)
            hf_val = s.get('hf_display', 'all')
            self.page_hf_display.set(hf_val)
            hf_label = next((k for k, v in self.hf_display_map.items() if v == hf_val), self.hf_display_labels[0])
            self._hf_disp_cb.set(hf_label)
        if 'fonts' in settings:
            for key, vals in settings['fonts'].items():
                if key in self.font_settings:
                    self.font_settings[key]['size'].set(self._get_label_for_zihao(vals['size']))
                    self.font_settings[key]['bold'].set(vals.get('bold', True))
        self._redraw_seal_preview()
        self._refresh_score_preview()

    def _save_template(self):
        #保存的模板
        latex = self._raw_latex if self._raw_latex  is not None else  self.generate_template_latex();
        if not latex:
            latex = self.preview_text.get("1.0", tk.END).strip()
        if not latex:
            messagebox.showwarning("提示", "没有可保存的模板内容，请先生成预览。")
            return

        name = self.preview_filename.get().strip()
        if not name:
            name = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not name.endswith('.tex'):
            name += '.tex'

        save_dir = TEMPLATE_DIR / 'item_type'
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / name

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(latex)
            messagebox.showinfo("成功", f"模板已保存至:\n{save_path}\n\n注意：此模板为预览版本（占位符已替换为示例值）。\n如需用于生成正式试卷，请使用「基本设置」中的试卷模板路径，并确保模板包含占位符（如 items_x, main_title_x 等）。")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
