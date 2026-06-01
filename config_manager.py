import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import pandas as pd
from utils import TEMPLATE_DIR


class ConfigManager:
    @staticmethod
    def collect_config(item_rows, instruction_items, data_file, tex_path, paper_template_path, option_separator, exam_main, exam_sub, exam_time):
        item_info = []
        for row in item_rows:
            try:
                item_info.append({
                    'item_type': row['item_type'].get(),
                    'item_count': int(row['item_count'].get()),
                    'item_score': float(row['item_score'].get()),
                    'bank_type': row['bank_type'].get()
                })
            except ValueError:
                messagebox.showerror("错误", "题量和分值必须为数字")
                return None
        try:
            exam_time_val = int(exam_time.get())
        except (ValueError, TypeError):
            exam_time_val = 150
        all_score = round(sum(x['item_count'] * x['item_score'] for x in item_info), 1)
        
        paper_template_path_val = paper_template_path.get()
        if paper_template_path_val and not Path(paper_template_path_val).is_absolute():
            paper_template_path_val = str(Path(paper_template_path_val).resolve())
        if paper_template_path_val and not Path(paper_template_path_val).exists():
            messagebox.showwarning("警告", f"试卷模板文件不存在：{paper_template_path_val}\n将使用默认模板生成。")
            paper_template_path_val = ""
            
        paper_info = {
            'item_info': item_info,
            'exam_time': exam_time_val,
            'exam_main': exam_main.get(),
            'exam_sub': exam_sub.get(),
            'paper_template_path': paper_template_path_val,
            'option_separator': option_separator.get(),
            'all_score': all_score
        }
        map_item = {x['item_type']: x['bank_type'] for x in item_info}
        item_instructions = {}
        for k, v in instruction_items.items():
            if isinstance(v, tk.Text):
                item_instructions[k] = v.get("1.0", tk.END).strip()
            else:
                item_instructions[k] = v.get()
        return {
            'data_file': data_file.get(),
            'tex_path': tex_path.get(),
            'item_info': item_info,
            'paper_info': paper_info,
            'map_item': map_item,
            'item_instructions': item_instructions
        }

    @staticmethod
    def save_config(parent, item_rows, instruction_items, data_file, tex_path, paper_template_path, option_separator, exam_main, exam_sub, exam_time, template_panel=None):
        config = ConfigManager.collect_config(item_rows, instruction_items, data_file, tex_path, paper_template_path, option_separator, exam_main, exam_sub, exam_time)
        if not config:
            return
        path = filedialog.asksaveasfilename(title="保存配置", defaultextension=".json", filetypes=[("JSON文件", "*.json")])
        if path:
            save_data = {
                'data_file': config['data_file'],
                'tex_path': config['tex_path'],
                'exam_main': config['paper_info']['exam_main'],
                'exam_sub': config['paper_info']['exam_sub'],
                'exam_time': config['paper_info']['exam_time'],
                'paper_template_path': config['paper_info']['paper_template_path'],
                'option_separator': config['paper_info']['option_separator'],
                'item_info': config['item_info'],
                'item_instructions': config['item_instructions']
            }
            if template_panel:
                save_data['template_settings'] = template_panel.collect_settings()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "配置已保存")

    @staticmethod
    def load_config(parent, item_rows, instruction_items, data_file, tex_path, paper_template_path, option_separator, exam_main, exam_sub, exam_time, refresh_widgets_callback=None, on_data_file_change=None, template_panel=None):
        path = filedialog.askopenfilename(title="加载配置", filetypes=[("JSON文件", "*.json")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data_file.set(data.get('data_file', ''))
            tex_path.set(data.get('tex_path', './temp/paper.tex'))
            paper_template_path.set(data.get('paper_template_path', ''))
            option_separator.set(data.get('option_separator', '$;$'))
            exam_main.set(data.get('exam_main', ''))
            exam_sub.set(data.get('exam_sub', ''))
            exam_time.set(str(int(data.get('exam_time', 150))))
            item_info = data.get('item_info', [])
            item_rows.clear()
            for item in item_info:
                score_val = item.get('item_score', 1)
                try:
                    score_val = float(score_val)
                except (ValueError, TypeError):
                    score_val = 1.0
                ConfigManager._add_item_row_data(item_rows,
                    item.get('item_type', ''),
                    str(item.get('item_count', 1)),
                    f"{score_val:.1f}",
                    item.get('bank_type', item.get('item_type', '')))
            refresh_widgets_callback()
            loaded_file = data.get('data_file', '')
            if loaded_file and on_data_file_change:
                try:
                    df = pd.read_excel(loaded_file, skiprows=1)
                    df.columns = df.columns.str.strip()
                    if '题型' in df.columns:
                        type_counts = df['题型'].astype(str).str.strip().value_counts().to_dict()
                        on_data_file_change(type_counts)
                except Exception:
                    pass
            instructions = data.get('item_instructions', {})
            for k, v in instruction_items.items():
                if k in instructions and isinstance(v, tk.Text):
                    v.delete("1.0", tk.END)
                    v.insert("1.0", instructions[k])
            
            if template_panel and 'template_settings' in data:
                template_panel.apply_settings(data['template_settings'])
                
            messagebox.showinfo("成功", "配置已加载")
            return True
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败：{e}")
            return False

    @staticmethod
    def _add_item_row_data(item_rows, item_type, count, score, bank_type=None):
        if bank_type is None:
            bank_type = item_type
        row = {
            'item_type': tk.StringVar(value=item_type),
            'item_count': tk.StringVar(value=count),
            'item_score': tk.StringVar(value=score),
            'bank_type': tk.StringVar(value=bank_type)
        }
        item_rows.append(row)
