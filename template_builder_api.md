# template_builder 中文 API 文档

## 模块属性

| 属性 | 说明 |
|------|------|
| `VALID_ZIHAO` | 合法中文字号集合（例如 `'-0'`、`'5'`、`'8'`） |
| `DLL_AVAILABLE` | 当从 C 扩展 `.pyd` 或 `.dll` 加载时为 `True` |
| `LATEX_PATH` | 可执行文件 `shuilin.exe`（tectonic）的路径 |
| `TEMP_DIR` | 编译输出的临时目录 |
| `RESOURCE_DIR` | `.pyd` 或 `.dll` 所在目录 |

## 函数

### `_make_font_cmd(size, bold=False)`

生成指定字号的 LaTeX 字体命令。

- **size** – `VALID_ZIHAO` 中的字符串（如 `'5'`、`'-2'`）或磅值（如 `'12'`）
- **bold** – 若为 `True`，追加 `\bfseries`
- **返回** – LaTeX 命令字符串，如 `\zihao{5}` 或 `\fontsize{12pt}{16pt}\selectfont`

## 类

### `TemplateBuilder`

提供静态方法，用于生成 LaTeX 模板片段并组装完整试卷。

#### `TemplateBuilder.create_paper(paper_info, items, template_settings=None)`

组装完整的试卷 LaTeX 文档。

- **paper_info** – `dict`，包含键：`exam_main`、`exam_sub`、`exam_time`、`all_score`、`item_info`（`item_type`、`item_count`、`item_score` 组成的 `dict` 列表）
- **items** – 预渲染的试题内容 LaTeX 字符串（`enumerate` 环境主体）
- **template_settings** – `dict`，包含 `page`、`sealing`、`header_footer`、`scoring`、`fonts` 等节
- **返回** – 完整的 LaTeX 文档字符串

#### `TemplateBuilder.create_template(typex, num, score, item_number, item_instructions, show_score_table=True, table_style='tabular', font_settings=None)`

为单个题型区块创建 LaTeX。

- **typex** – 题型名称（如 `"选择题"`）
- **num** – 该题型题目数量
- **score** – 每题分值
- **item_number** – 题型序号标签（如 `"一"`）
- **item_instructions** – `dict`，题型名称到答题说明的映射
- **show_score_table** – 是否显示该题型得分表
- **table_style** – `'tabular'`、`'tabularx'` 或 `'longtable'`
- **font_settings** – 该题型的字体配置 dict
- **返回** – 该题型的 LaTeX 字符串

#### `TemplateBuilder.add_item(temp, data, item_type, option_separator='$;$')`

- **temp** – 包含 `_item_s` 的模板字符串（来自 `create_template`）
- **data** – `pd.DataFrame`，包含列 `试题正文` 和可选的 `试题选项`
- **item_type** – 字符串；若包含 `"选择"`，选项将格式化为 A/B/C/D
- **option_separator** – 选项分隔符（默认 `$;$`）
- **返回** – 加入试题后的模板

#### `TemplateBuilder.build_sealing_line(s, side='left', display_mode='side', font_size='5')`

生成密封线的 LaTeX。

- **s** – 密封配置 dict（键含 `seal_left_offset`、`seal_line_width`、`seal_warning_text` 等）
- **side** – `'left'` 或 `'right'`
- **display_mode** – `'side'`、`'top'` 或 `'hidden'`
- **font_size** – 警告文字的字号

#### `TemplateBuilder.build_header_footer(s, header_font_size='-0', footer_font_size='-0', header_bold=False, footer_bold=False)`

生成 LaTeX `\pagestyle{fancy}` 页眉页脚定义。

- **s** – 页眉页脚配置 dict（键含 `hf_left_header`、`hf_center_header`、`hf_right_header` 等）

#### `TemplateBuilder.build_score_table(item_info, include_reviewer=True, table_style='tabular', font_size='5')`

生成所有题型的累计得分表。

- **item_info** – `item_type`、`item_count`、`item_score` 组成的 `dict` 列表
- **include_reviewer** – 是否包含阅卷人列
- **table_style** – `'tabular'`、`'tabularx'` 或 `'longtable'`

### `PdfGenerator`

提供编译 PDF 与数据抽样的静态方法。

#### `PdfGenerator.generate_pdf(data, tex_path=None)`

将 LaTeX 写入磁盘并编译。

- **data** – LaTeX 字符串
- **tex_path** – 写入 `.tex` 文件的路径（默认为 `TEMP_DIR/paper.tex`）
- **返回** – `(True, "")` 成功，`(False, error_msg)` 失败

#### `PdfGenerator.sample_data(data, count)`

从 DataFrame 中随机抽取 `count` 行。

- **data** – `pd.DataFrame`
- **count** – 抽样行数
- **返回** – 抽样后的 DataFrame
- **抛出** – `ValueError` 如果数据不足

## C 扩展函数（从 `.DLL` 加载时暴露）

| 函数 | 说明 |
|------|------|
| `escape_latex(text)` | 转义 LaTeX 特殊字符（`\`、`{`、`}`、`#`、`$`、`%`、`&`、`~`、`_`、`^`） |
| `CompilePdf(path)` | 在 `.tex` 文件上运行 tectonic（返回退出码） |
| `GetTectonicPath()` | 已提取的 `shuilin.exe` 路径，或 `None` |
| `GetBundlePath()` | 已提取的 bundle 目录路径 |
| `GetResourceData(id)` | 按整数 ID 获取嵌入资源的原始字节 |
| `GetResourcePath(rel_path)` | 将资源提取到临时目录，返回完整路径 |
| `GetModuleDir()` | `.dll` 所在目录 |
| `CleanupTempFiles()` | 删除所有临时提取的资源 |
| `IsEmbedded()` | 若从 C 扩展 `.dll` 运行则为 `True` |

## 独立 DLL 函数（从 `template_builder.dll` 加载时可用）

| 函数 | 说明 |
|------|------|
| `TB_compile_pdf(tex_path)` | 编译 `.tex` 为 PDF，返回退出码 |
| `TB_get_tectonic_path()` | 已提取的 `shuilin.exe` 路径 |
| `TB_get_bundle_path()` | 已提取的 tectonic bundle 目录路径 |
| `TB_get_dll_dir()` | DLL 所在目录 |
| `TB_cleanup_temp_files()` | 删除所有临时提取的资源 |
| `TB_is_embedded()` | 始终返回 1 |
| `TB_get_resource_data(res_id, out_buf, out_size)` | 获取嵌入资源的字节数据 |
| `TB_free(ptr)` | 释放 `TB_get_resource_data` 分配的缓冲区 |
| `TB_get_resource_path(rel_path)` | 将资源提取到临时目录并返回路径 |
| `TB_escape_latex(text, out_buf, buf_len)` | 转义 LaTeX 特殊字符 |
