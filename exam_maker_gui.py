import tkinter as tk
from tkinter import ttk, messagebox
import threading

from utils import UI_FONT, RESOURCE_DIR, TEMPLATE_DIR
from exam_engine import ExamEngine
from config_manager import ConfigManager
from panels.basic_settings_panel import BasicSettingsPanel
from panels.item_settings_panel import ItemSettingsPanel
from panels.template_design_panel import TemplateDesignPanel
from panels.instruction_settings_panel import InstructionSettingsPanel
from panels.about_panel import AboutPanel


class ExamMakerGUI:
    ICON_PATH = str(RESOURCE_DIR / "APP.ico")

    def __init__(self, root):
        self.root = root
        self.root.title("试卷生成器")
        self.root.geometry("560x560")
        self.root.resizable(False, False)
        self._set_icon()
        self._style()
        self._init_defaults()
        self._build_ui()

    def _set_icon(self):
        import os
        if os.path.exists(self.ICON_PATH):
            try:
                self.root.iconbitmap(self.ICON_PATH)
            except Exception:
                pass

    def _style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', font=(UI_FONT, 9))
        style.configure('TButton', font=(UI_FONT, 9), padding=2)
        style.configure('Header.TLabel', font=(UI_FONT, 10, 'bold'), foreground='#1a73e8')
        style.configure('Treeview', font=(UI_FONT, 9), rowheight=28)
        style.configure('Treeview.Heading', font=(UI_FONT, 9, 'bold'))
        style.configure('TNotebook.Tab', font=(UI_FONT, 9), padding=[8, 2])

    def _init_defaults(self):
        self.data_file = tk.StringVar()
        self.tex_path = tk.StringVar(value='./temp/paper.tex')
        self.paper_template_path = tk.StringVar(value='')
        self.option_separator = tk.StringVar(value='$;$')
        self.exam_main = tk.StringVar(value="2026年数据中国技能大赛")
        self.exam_sub = tk.StringVar(value="网络安全与人工智能竞赛(虚构)")
        self.exam_time = tk.StringVar(value="150")
        self.item_rows = []
        self.instruction_items = {}

        self.engine = ExamEngine()

        default_item_info = [
            {"item_type": "单项选择题", "item_count": 3, "item_score": 1, "bank_type": "单选题"},
            {"item_type": "多项选择题", "item_count": 2, "item_score": 1.5, "bank_type": "多选题"},
            {"item_type": "判断题", "item_count": 5, "item_score": 0.5, "bank_type": "判断题"},
            {"item_type": "简答题", "item_count": 5, "item_score": 3, "bank_type": "简答题"}
        ]
        default_instructions = {
            "单项选择题": "每小题给出的四个选项中，最多有一个选项符合题目要求。",
            "多项选择题": "每小题给出的四个选项中，有多个选项符合题目要求，有错选、不选得0分。",
            "简答题": "",
            "判断题": "对下列命题进行判断，正确的在括号内打√，错误的打×。"
        }
        for item in default_item_info:
            ConfigManager._add_item_row_data(self.item_rows, item['item_type'], str(item['item_count']), str(item['item_score']), item['bank_type'])
        for k, v in default_instructions.items():
            self.instruction_items[k] = tk.StringVar(value=v)

    def _refresh_item_tree(self):
        if hasattr(self, 'item_panel'):
            self.item_panel.refresh_item_tree()
        if hasattr(self, 'template_panel'):
            self.template_panel._refresh_score_preview()

    def _on_data_file_changed(self, type_counts):
        if hasattr(self, 'item_panel'):
            self.item_panel.update_bank_types(type_counts)

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=6)
        main_frame.pack(fill=tk.BOTH, expand=True)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        tab1 = ttk.Frame(notebook, padding=4)
        tab2 = ttk.Frame(notebook, padding=4)
        tab3 = ttk.Frame(notebook, padding=4)
        tab4 = ttk.Frame(notebook, padding=4)
        tab5 = ttk.Frame(notebook, padding=4)
        notebook.add(tab1, text="  基本设置  ")
        notebook.add(tab2, text="  题型设置  ")
        notebook.add(tab3, text="  模板设计(可选)  ")
        notebook.add(tab4, text="  答题说明  ")
        notebook.add(tab5, text="  关于  ")

        self.basic_panel = BasicSettingsPanel(tab1, self.data_file, self.tex_path, self.paper_template_path, self.option_separator, self.exam_main, self.exam_sub, self.exam_time, self._on_data_file_changed)
        self.item_panel = ItemSettingsPanel(tab2, self.item_rows, lambda t, c, s, b: ConfigManager._add_item_row_data(self.item_rows, t, c, s, b),
                                            on_change_callback=lambda: self.template_panel._refresh_score_preview(),
                                            on_generate=self._on_generate,
                                            on_save_config=self._save_config,
                                            on_load_config=self._load_config)
        self.template_panel = TemplateDesignPanel(tab3, self.item_rows, self.exam_main, self.exam_sub, self.exam_time)
        self.instruction_panel = InstructionSettingsPanel(tab4, self.instruction_items)
        self.about_panel = AboutPanel(tab5)

    def _on_generate(self):
        config = ConfigManager.collect_config(self.item_rows, self.instruction_items, self.data_file, self.tex_path, self.paper_template_path, self.option_separator, self.exam_main, self.exam_sub, self.exam_time)
        if not config:
            return
        if not config['data_file']:
            messagebox.showwarning("提示", "请先选择题库文件")
            return

        if hasattr(self, 'template_panel'):
            config['template_settings'] = self.template_panel.collect_settings()

        self.item_panel.gen_btn.config(state=tk.DISABLED)
        self.item_panel.gen_status.config(text="正在生成试卷...", foreground='#555')
        self.item_panel.gen_progress.start(10)
        threading.Thread(target=self._generate_thread, args=(config,), daemon=True).start()

    def _generate_thread(self, config):
        root = self.root
        success, msg = self.engine.generate_from_config(config)
        root.after(0, self._generate_done, success, msg)

    def _generate_done(self, success, msg):
        self.item_panel.gen_progress.stop()
        self.item_panel.gen_progress.config(value=0)
        self.item_panel.gen_btn.config(state=tk.NORMAL)

        if success:
            self.item_panel.gen_status.config(text="生成完成 ✓", foreground='#1a73e8')
            messagebox.showinfo("成功", "离线生成试卷完成！")
        else:
            self.item_panel.gen_status.config(text="生成失败 ✗", foreground='#c33')
            messagebox.showerror("错误", msg)

    def _save_config(self):
        ConfigManager.save_config(self.root, self.item_rows, self.instruction_items, self.data_file, self.tex_path, self.paper_template_path, self.option_separator, self.exam_main, self.exam_sub, self.exam_time, template_panel=self.template_panel)

    def _load_config(self):
        ConfigManager.load_config(self.root, self.item_rows, self.instruction_items, self.data_file, self.tex_path, self.paper_template_path, self.option_separator, self.exam_main, self.exam_sub, self.exam_time, self._refresh_item_tree, self._on_data_file_changed, template_panel=self.template_panel)


def main():
    root = tk.Tk()
    ExamMakerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
