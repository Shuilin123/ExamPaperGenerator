import tkinter as tk
from tkinter import font as tkfont
import ctypes
import sys
from pathlib import Path
import os
import shutil


try:
    if sys.platform == 'win32':
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_resource_path(relative_path):
    """Get the correct path for resources, works for both dev and frozen exe."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.resolve()
    return base_path / relative_path


def get_script_dir():
    """Get the directory where the exe or script is running from."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve()
    else:
        return Path(__file__).parent.resolve()


def _extract_resources():
    """Extract bundled resources to the exe directory on first run."""
    if not getattr(sys, 'frozen', False):
        return

    script_dir = get_script_dir()
    frozen_base = Path(sys._MEIPASS)

    resources_to_extract = [
        ("template", script_dir / "template"),
        ("data", script_dir / "data"),
        ("README.md", script_dir / "README.md"),
        ("使用说明.txt", script_dir / "使用说明.txt"),
    ]

    for src_name, dest_path in resources_to_extract:
        src_path = frozen_base / src_name
        if not src_path.exists():
            continue
        if dest_path.exists():
            continue
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.is_dir():
                shutil.copytree(str(src_path), str(dest_path))
            else:
                shutil.copy2(str(src_path), str(dest_path))
        except Exception:
            pass

    temp_dir = script_dir / "temp"
    temp_dir.mkdir(exist_ok=True)


_extract_resources()


SCRIPT_DIR = get_script_dir()
if getattr(sys, 'frozen', False):
    RESOURCE_DIR = Path(sys._MEIPASS)
else:
    RESOURCE_DIR = get_resource_path('.')

LATEX_PATH = ""
TEMP_DIR = ""
TEMPLATE_DIR = SCRIPT_DIR / "template"

_DLL = None
_DLL_MODULE = None
DLL_BUNDLE_DIR = None
DLL_AVAILABLE = False


def get_font():
    root = tk.Tk()
    root.withdraw()
    for font_name in ("Microsoft YaHei UI", "Microsoft YaHei", "SimHei"):
        try:
            f = tkfont.Font(root, family=font_name, size=9)
            root.destroy()
            return font_name
        except tk.TclError:
            continue
    root.destroy()
    return "TkDefaultFont"


UI_FONT = get_font()


def escape_latex(text):
    """Escape special LaTeX characters in user-provided text."""
    if not text:
        return ""
    text = str(text)
    # Order matters: backslash must be escaped first
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('#', r'\#'),
        ('$', r'\$'),
        ('%', r'\%'),
        ('&', r'\&'),
        ('~', r'\textasciitilde{}'),
        ('_', r'\_'),
        ('^', r'\textasciicircum{}'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def number_to_chinese(num):
    if num < 1 or num > 500:
        return "超出范围"
    chinese_nums = {
        0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
        5: '五', 6: '六', 7: '七', 8: '八', 9: '九',
        10: '十', 100: '百', 1000: '千'
    }
    if num < 11:
        return chinese_nums[num]
    elif num < 20:
        return '十' + chinese_nums[num - 10]
    elif num < 100:
        tens = num // 10
        units = num % 10
        if units == 0:
            return chinese_nums[tens] + '十'
        else:
            return chinese_nums[tens] + '十' + chinese_nums[units]
    elif num < 1000:
        hundreds = num // 100
        remainder = num % 100
        if remainder == 0:
            return chinese_nums[hundreds] + '百'
        elif remainder < 10:
            return chinese_nums[hundreds] + '百零' + chinese_nums[remainder]
        else:
            tens_part = number_to_chinese(remainder)
            return chinese_nums[hundreds] + '百' + tens_part
    else:
        return '五百'


# ===== 加载 template_builder.dll 并导出全部功能 =====
TemplateBuilder = None
PdfGenerator = None
_make_font_cmd = None

def _load_as_dll(dll_path, module_name="template_builder"):
    from importlib.machinery import ModuleSpec
    import importlib._bootstrap_external as _be
    dll_path = str(Path(dll_path).resolve())
    loader = _be.ExtensionFileLoader(module_name, dll_path)
    spec = ModuleSpec(module_name, loader, origin=dll_path)
    mod = loader.create_module(spec)
    loader.exec_module(mod)
    sys.modules[module_name] = mod
    return mod

_dll_mod_path = SCRIPT_DIR / "template_builder.dll"
if _dll_mod_path.exists():
    try:
        _tb_mod = _load_as_dll(str(_dll_mod_path), "template_builder")
        _DLL_MODULE = _tb_mod
        _DLL = _tb_mod
        _tb_exepath = _tb_mod.GetTectonicPath()
        if _tb_exepath:
            LATEX_PATH = Path(_tb_exepath)
        _tb_bundpath = _tb_mod.GetBundlePath()
        if _tb_bundpath:
            DLL_BUNDLE_DIR = Path(_tb_bundpath)
        DLL_AVAILABLE = True
        TemplateBuilder = _tb_mod.TemplateBuilder
        PdfGenerator = _tb_mod.PdfGenerator
        _make_font_cmd = _tb_mod._make_font_cmd
    except Exception:
        import traceback
        traceback.print_exc()
