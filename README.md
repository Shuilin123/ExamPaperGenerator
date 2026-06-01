# 试卷生成器 v2.0.0

这是一个试卷自动生成工具。从 Excel 题库读取试题，通过图形界面配置试卷参数与模板，一键生成 PDF 试卷。

## 功能

- **基本设置** — 选择题库文件（Excel）、TeX 输出路径、试卷主/副标题、考试时长
- **题型设置** — 自定义试卷包含的题型（单选/多选/判断/简答/计算等）、题量与分值，支持按权重自动分配分值
- **题型映射** — 配置试卷题型名称与题库 Excel 列名的对应关系
- **答题说明** — 为每种题型单独编辑考试时的答题要求
- **模板设计** — 可视化编辑密封线、评分表、页眉页脚、页面布局，支持实时预览
- **配置管理** — 保存/加载 `.json` 配置文件，方便重复使用相同模板
- **PDF 生成** — 基于开源LaTeX 引擎编译输出，支持自定义 `.tex` 题型模板

## 快速开始

1. 解压template_builder.7z 到当前文件夹下
1. 准备题库 Excel 文件，需包含列：`题型`、`试题正文`、`试题选项`、`试题答案`、`答案要点及评分标准`
2. 运行 `exam_maker_gui.py`
3. 在"基本设置"页选择题库文件，填写试卷信息
4. 在"题型设置"页配置题量与分值
5. 在"模板设计"页调整试卷样式
6. 点击"生成并编译"输出 PDF

```
python exam_maker_gui.py
```

## 数据格式

题库文件支持 `.xls` / `.xlsx` / `.csv`，跳过首行后需包含以下列：

| 列名 | 说明 |
|------|------|
| 题型 | 题目类型（与题型映射配置对应） |
| 试题正文 | 题目内容 |
| 试题选项 | 选项内容（多选项用分隔符隔开） |
| 试题答案 | 标准答案 |
| 答案要点及评分标准 | 简答题评分要点 |

## 技术栈

- **GUI**: Python Tkinter / ttk
- **数据读取**: pandas (Excel/CSV)
- **LaTeX 编译**: Tectonic（通过 `template_builder.dll` C 扩展调用）
- **模板引擎**: 自定义 C 扩展（`template_builder.dll`）+ LaTeX 片段

## 项目结构

```
├── exam_maker_gui.py          # 主入口，GUI 构建
├── exam_engine.py             # 试卷生成逻辑
├── config_manager.py          # 配置收集/保存/加载
├── utils.py                   # 工具函数 & DLL 加载
├── template_builder.dll       # C 扩展（LaTeX 生成 & PDF 编译）
├── template_builder_api.md    # DLL API 文档
├── panels/
│   ├── basic_settings_panel.py      # 基本设置面板
│   ├── item_settings_panel.py       # 题型设置面板
│   ├── map_settings_panel.py        # 题型映射面板
│   ├── instruction_settings_panel.py# 答题说明面板
│   ├── template_design_panel.py     # 模板设计面板
│   └── about_panel.py               # 关于面板
├── template/
│   └── item_type/                   # 题型级 LaTeX 模板
├── data/                            # 题库文件 & 配置
│   ├── info.json
│   ├── 数理样题.xlsx
│   └── 样题.xlsx
├── temp/                            # 编译输出目录
└── APP.ico                          # 应用图标
```

## 许可证

© 2026 shuilin123. All rights reserved.
