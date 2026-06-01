import tkinter as tk
from tkinter import ttk
from utils import UI_FONT


class InstructionSettingsPanel:
    def __init__(self, parent, instruction_items):
        self.parent = parent
        self.instruction_items = instruction_items
        self._build()

    def _build(self):
        ttk.Label(self.parent, text="各题型答题说明", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 2))

        parent_frame = ttk.Frame(self.parent)
        parent_frame.pack(fill=tk.BOTH, expand=True)
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(0, weight=1)

        self.instructions_canvas = tk.Canvas(parent_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.instructions_canvas.yview)
        self.scrollable = ttk.Frame(self.instructions_canvas)
        self.scrollable.bind("<Configure>", lambda e: self.instructions_canvas.configure(scrollregion=self.instructions_canvas.bbox("all")))
        self.instructions_canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.instructions_canvas.configure(yscrollcommand=scrollbar.set)
        self.instructions_canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.instructions_canvas.bind('<Configure>', self._on_canvas_resize)

        self._build_instruction_widgets()

    def _on_canvas_resize(self, event):
        self.instructions_canvas.itemconfig('all', width=event.width - 4) if self.instructions_canvas.find_all() else None
        for child in self.scrollable.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                child.configure(width=event.width - 10)

    def _build_instruction_widgets(self):
        for key in self.instruction_items.keys():
            f = ttk.LabelFrame(self.scrollable, text=key, padding=4)
            f.pack(fill=tk.X, padx=4, pady=3)
            text_widget = tk.Text(f, height=3, font=(UI_FONT, 9), wrap=tk.WORD)
            text_widget.insert(tk.END, self.instruction_items[key].get())
            text_widget.pack(fill=tk.X, padx=2, pady=2, expand=True)
            self.instruction_items[key] = text_widget
