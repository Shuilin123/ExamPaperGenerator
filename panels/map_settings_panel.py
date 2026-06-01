import tkinter as tk
from tkinter import ttk
from utils import UI_FONT


class MapSettingsPanel:
    def __init__(self, parent, map_items):
        self.parent = parent
        self.map_items = map_items
        self._build()

    def _build(self):
        ttk.Label(self.parent, text="题型名称映射（试卷题型 → 题库题型）", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 6))
        map_frame = ttk.Frame(self.parent)
        map_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
        ttk.Label(map_frame, text="试卷题型", font=(UI_FONT, 9, 'bold'), width=18).grid(row=0, column=0, padx=4, pady=3, sticky=tk.W)
        ttk.Label(map_frame, text="→", font=(UI_FONT, 9, 'bold'), width=4, anchor=tk.CENTER).grid(row=0, column=1, padx=2, pady=3)
        ttk.Label(map_frame, text="题库题型", font=(UI_FONT, 9, 'bold'), width=18).grid(row=0, column=2, padx=4, pady=3, sticky=tk.W)
        for i, key in enumerate(self.map_items.keys()):
            ttk.Label(map_frame, text=key, width=18).grid(row=i + 1, column=0, padx=4, pady=2, sticky=tk.W)
            ttk.Label(map_frame, text="→", width=4, anchor=tk.CENTER).grid(row=i + 1, column=1, padx=2, pady=2)
            ttk.Entry(map_frame, textvariable=self.map_items[key], width=22).grid(row=i + 1, column=2, padx=4, pady=2, sticky=tk.W)
        
        ttk.Label(self.parent, text="提示：左侧为试卷中显示的题型名称，右侧为题库Excel中的题型列名称", 
                 foreground='#888', wraplength=700, justify=tk.LEFT).pack(anchor=tk.W, padx=8, pady=(8, 4))
