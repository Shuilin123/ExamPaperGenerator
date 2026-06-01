import pandas as pd
from pathlib import Path
from utils import number_to_chinese, escape_latex, TemplateBuilder, _make_font_cmd, PdfGenerator


class ExamEngine:
    def __init__(self):
        self.template_builder = TemplateBuilder()
        self.pdf_generator = PdfGenerator()

    def generate_from_config(self, config):
        excell_name = config.get('data_file')
        if not excell_name:
            return False, "未选择文件，程序退出。"
        try:
            data = pd.read_excel(excell_name, skiprows=1)
            data.columns = data.columns.str.strip()
            if '题型' in data.columns:
                data['题型'] = data['题型'].astype(str).str.strip()
        except Exception as e:
            return False, f"读取题库文件失败：{e}"

        required_cols = ['题型', '试题正文', '试题选项', '试题答案', '答案要点及评分标准']
        missing = [c for c in required_cols if c not in data.columns]
        if missing:
            return False, f"题库文件缺少以下列：{', '.join(missing)}\n当前列名：{', '.join(data.columns)}"
        items = r''
        item_info = config['item_info']
        paper_info = config['paper_info']
        map_item = config['map_item']
        item_instructions = config['item_instructions']
        option_separator = paper_info.get('option_separator', '$;$')
        template_settings = config.get('template_settings', {})
        show_per_type = template_settings.get('scoring', {}).get('show_per_type', True)
        table_style = template_settings.get('scoring', {}).get('table_style', 'tabular')

        active_item_info = [x for x in paper_info['item_info'] if x['item_count'] > 0]
        paper_info = paper_info.copy()
        paper_info['item_info'] = active_item_info

        answer_parts = []
        for i in range(0, len(paper_info['item_info'])):
            datx = paper_info['item_info'][i]
            item_type = datx['item_type']
            if datx['item_count'] == 0:
                continue
            strx = self.template_builder.create_template(
                item_type, datx['item_count'], datx['item_score'],
                number_to_chinese(i + 1), item_instructions, show_per_type, table_style,
                font_settings=template_settings.get('fonts', {}))
            bank_type = map_item[item_type]
            datay = data.loc[data['题型'] == bank_type,:]
            if len(datay) < datx['item_count']:
                return False, f"题库数量不足！题型「{item_type}」(映射: {bank_type}) 需要 {datx['item_count']} 题，但题库中只有 {len(datay)} 题。请检查题库文件或调整题量设置。"
            datay = self.pdf_generator.sample_data(datay, datx['item_count'])
            if bank_type == '简答题':
                answer_parts.append(datay[['答案要点及评分标准']].copy())
            else:
                answer_parts.append(datay[['试题答案']].copy())
            datay = datay[['试题正文', '试题选项']]
            stry = self.template_builder.add_item(strx, datay, item_type, option_separator)
            items += (stry + '\n')

        if answer_parts:
            answer = pd.concat(answer_parts, ignore_index=True)
            if '试题答案' not in answer.columns:
                answer['试题答案'] = ''
            if '答案要点及评分标准' not in answer.columns:
                answer['答案要点及评分标准'] = ''
            answer = answer.reset_index()
            answer.rename(columns={"index": "题号"}, inplace=True)
            answer['题号'] = range(1, len(answer) + 1)
            answer['答案'] = answer['试题答案'].fillna('').astype(str) + ' ' + answer['答案要点及评分标准'].fillna('').astype(str)
            answer = answer[['题号', '答案']]
        else:
            answer = pd.DataFrame(columns=['题号', '答案'])

        try:
            safe_name = (paper_info['exam_main'] if paper_info['exam_sub'] == '' else paper_info['exam_sub']).replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            save_path = './' + safe_name + '参考答案与评分意见.xlsx'
            answer.to_excel(save_path, index=False)
        except Exception as e:
            return False, f"保存答案文件失败：{e}"

        custom_template_path = paper_info.get('paper_template_path', '')
        if custom_template_path:
            template_path = Path(custom_template_path)
            if not template_path.is_absolute():
                template_path = Path(__file__).parent / custom_template_path
            if template_path.exists():
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        stry = f.read()
                    if not stry.strip():
                        return False, "模板文件为空"

                    if 'items_x' in stry:
                        stry = stry.replace('items_x', items)
                    else:
                        stry = stry.replace('\\end{document}', items + '\\end{document}')

                    stry = stry.replace('sub_title_x', escape_latex(paper_info.get('exam_sub', '')))
                    stry = stry.replace('main_title_x', escape_latex(paper_info.get('exam_main', '')))
                    stry = stry.replace('exam_time_x', str(paper_info.get('exam_time', 150)))
                    stry = stry.replace('score_x', f"{paper_info.get('all_score', 100):.1f}")
                    item_info_list = paper_info.get('item_info', [])
                    n = len(item_info_list)
                    for i in range(n - 1, -1, -1):
                        datx = item_info_list[i]
                        stry = stry.replace(f'item_x_{i+1}_s', f"{datx['item_count'] * datx['item_score']:.1f}")
                        stry = stry.replace(f'item_x_{i+1}', escape_latex(datx['item_type']))
                    stry = stry.replace(f'item_x_{n+1}_s', f"{paper_info.get('all_score', 100):.1f}")
                except Exception as e:
                    return False, f"读取用户模板文件失败：{e}"
            else:
                stry = self.template_builder.create_paper(paper_info, items, template_settings)
        else:
            stry = self.template_builder.create_paper(paper_info, items, template_settings)

        path = config.get('tex_path', './temp/paper.tex')
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        item_info_list = paper_info.get('item_info', [])
        for i, datx in enumerate(item_info_list):
            stry = stry.replace(f'item_x_{i+1}_s', f"{datx['item_count'] * datx['item_score']:.1f}")
            stry = stry.replace(f'item_x_{i+1}', escape_latex(datx['item_type']))
        stry = stry.replace(f'item_x_{len(item_info_list)+1}_s', f"{paper_info.get('all_score', 100):.1f}")

        with open(path, "w", encoding="utf-8") as f:
            f.write(stry)
        stry = stry.replace("main\\_title\\_x", paper_info['exam_main']).replace("sub\\_title\\_x", paper_info['exam_sub'])
        return self.pdf_generator.generate_pdf(stry, path)

    @staticmethod
    def _remove_braced_block(text, cmd_start, brace_pos):
        depth = 0
        i = brace_pos
        while i < len(text):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    return text[:cmd_start] + text[i + 1:]
            i += 1
        return text[:cmd_start]

    @staticmethod
    def _remove_def(text, cmd):
        idx = text.find(cmd)
        while idx != -1:
            brace_pos = text.find('{', idx)
            if brace_pos != -1:
                text = ExamEngine._remove_braced_block(text, idx, brace_pos)
            idx = text.find(cmd)
        return text

    def _apply_template_settings(self, latex, template_settings, paper_info):
        import re
        page = template_settings.get('page', {})
        fonts = template_settings.get('fonts', {})
        sealing = template_settings.get('sealing', {})
        hf = template_settings.get('header_footer', {})
        scoring = template_settings.get('scoring', {})

        if page:
            paper_size = page.get('paper_size', 'a3paper')
            orientation = page.get('orientation', 'landscape')
            twocolumn = page.get('twocolumn', True)
            columns = 'twocolumn' if twocolumn else 'onecolumn'
            orient_opt = orientation if orientation == 'landscape' else ''
            new_docclass = f'\\documentclass[12pt,{paper_size},{columns},{orient_opt}]{{ctexart}}'
            new_docclass = new_docclass.replace(',,', ',').replace('[,', '[').replace(',]', ']')
            latex = re.sub(
                r'\\documentclass\[.*?\]\{ctexart\}',
                lambda m: new_docclass if 'ctexart' in m.group(0) else m.group(0),
                latex
            )

            seal_side = page.get('seal_side', 'left')
            left_margin = '3.0' if seal_side == 'left' else '1.5'
            right_margin = '1.5' if seal_side == 'left' else '3.0'
            latex = re.sub(
                r'left=[\d.]+cm,\s*right=[\d.]+cm',
                f'left={left_margin}cm, right={right_margin}cm',
                latex
            )

        if sealing:
            seal_side = page.get('seal_side', 'left') if page else 'left'
            seal_display = page.get('seal_display', 'side') if page else 'side'
            seal_font_size = '5'
            if 'seal_line' in fonts:
                sz = fonts['seal_line'].get('size', '5')
                valid_zihao = {'-0','0','-1','1','-2','2','-3','3','-4','4','-5','5','-6','6','7','8'}
                if sz in valid_zihao:
                    seal_font_size = sz
            new_seal = TemplateBuilder.build_sealing_line(
                sealing, side=seal_side, display_mode=seal_display, font_size=seal_font_size
            )
            if new_seal.strip():
                if r'\def\sealline' in latex:
                    latex = ExamEngine._remove_def(latex, r'\def\sealline')
                if r'\def\seallinex' in latex:
                    latex = ExamEngine._remove_def(latex, r'\def\seallinex')
                begin_doc = latex.find(r'\begin{document}')
                if begin_doc != -1:
                    latex = latex[:begin_doc] + new_seal + '\n\n' + latex[begin_doc:]

        if hf:
            hf_font_size = '-0'
            hf_bold = False
            if 'header' in fonts:
                sz = fonts['header'].get('size', '-0')
                hf_font_size = sz
                hf_bold = fonts['header'].get('bold', False)
            footer_font_size = '-0'
            footer_bold = False
            if 'footer' in fonts:
                sz = fonts['footer'].get('size', '-0')
                footer_font_size = sz
                footer_bold = fonts['footer'].get('bold', False)
            new_hf = TemplateBuilder.build_header_footer(
                hf, header_font_size=hf_font_size, footer_font_size=footer_font_size,
                header_bold=hf_bold, footer_bold=footer_bold
            )
            if r'\pagestyle{fancy}' in latex:
                latex = re.sub(
                    r'\\pagestyle\{fancy\}.*?(?=\\setlist)',
                    lambda m: new_hf + '\n',
                    latex,
                    flags=re.DOTALL
                )

        if scoring:
            show_total = scoring.get('show_total', True)
            include_reviewer = scoring.get('include_reviewer', True)
            table_style = scoring.get('table_style', 'tabular')
            item_info_list = paper_info.get('item_info', [])
            if show_total and r'\begin{center}' in latex and r'题型' in latex:
                new_score_table = TemplateBuilder.build_score_table(
                    item_info_list, include_reviewer, table_style
                )
                score_match = re.search(
                    r'\\begin\{center\}.*?题型.*?\\end\{(tabular|tabularx|longtable)\}.*?\\end\{center\}',
                    latex,
                    flags=re.DOTALL
                )
                if score_match:
                    latex = latex.replace(score_match.group(0), new_score_table)

            n = len(item_info_list)
            for i in range(n - 1, -1, -1):
                datx = item_info_list[i]
                latex = latex.replace(f'item_x_{i+1}_s', f"{datx['item_count'] * datx['item_score']:.1f}")
                latex = latex.replace(f'item_x_{i+1}', escape_latex(datx['item_type']))
            latex = latex.replace(f'item_x_{n+1}_s', f"{paper_info.get('all_score', 100):.1f}")

        if fonts:
            f = fonts.get('main_title', {})
            if f:
                sz = f.get('size', '4')
                bold = f.get('bold', True)
                title_cmd = _make_font_cmd(sz, bold)
                latex = re.sub(
                    r'\{\\zihao\{[^}]*\}(?:\\bfseries\s*)?\\mainTitle\}',
                    lambda m: '{' + title_cmd + ' \\mainTitle}',
                    latex
                )
            f = fonts.get('sub_title', {})
            if f:
                sz = f.get('size', '4')
                bold = f.get('bold', True)
                title_cmd = _make_font_cmd(sz, bold)
                latex = re.sub(
                    r'\{\\zihao\{[^}]*\}(?:\\bfseries\s*)?\\subTitle\}',
                    lambda m: '{' + title_cmd + ' \\subTitle}',
                    latex
                )

        return latex
