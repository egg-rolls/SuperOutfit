"""
Claude-style CLI output utilities for SuperOutfit

Usage:
    from scripts.output import console, header, success, error, warn, info_table, data_table, badge, color_dot
"""

import sys
import io

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich import box

# ── Claude 暖色调主题 ──
THEME = Theme({
    'accent':  'bold #cc785c',
    'success': '#5db872',
    'warning': '#d4a017',
    'error':   '#c64545',
    'muted':   '#8e8b82',
    'dim':     '#6c6a64',
    'ink':     'bold #141413',
    'panel_border': '#cc785c',
    'table_border': '#e6dfd8',
    'header_bg': '#252320',
    'header_fg': '#faf9f5',
    'badge_bg': '#cc785c',
    'badge_fg': '#ffffff',
})

console = Console(theme=THEME, force_terminal=True, force_jupyter=False)


# ── 边框样式 ──
PANEL_BOX = box.ROUNDED
TABLE_BOX = box.SIMPLE_HEAD


def header(title, subtitle=None, width=None):
    """带装饰的标题面板"""
    text = Text()
    text.append(f"  {title}", style="accent")
    if subtitle:
        text.append(f"\n  {subtitle}", style="dim")
    console.print(Panel(
        text,
        border_style="panel_border",
        box=PANEL_BOX,
        expand=False,
        width=width,
    ))


def info_table(rows, title=None):
    """键值对表格 (label: value 格式)"""
    table = Table(
        box=TABLE_BOX,
        show_header=False,
        padding=(0, 2),
        border_style="table_border",
        title=title,
        title_style="accent",
    )
    table.add_column(style="muted", min_width=12)
    table.add_column()
    for label, value in rows:
        table.add_row(label, str(value))
    console.print(table)


def data_table(headers, rows, title=None, header_style="accent"):
    """数据表格"""
    table = Table(
        box=TABLE_BOX,
        border_style="table_border",
        title=title,
        title_style="accent",
        header_style=header_style,
        show_lines=False,
    )
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def success(msg):
    console.print(f"  [success]✓[/] {msg}")


def error(msg):
    console.print(f"  [error]✗[/] {msg}")


def warn(msg):
    console.print(f"  [warning]![/] {msg}")


def info(msg):
    console.print(f"  [muted]·[/] {msg}")


def badge(text, style='accent'):
    """带背景色的圆角色标"""
    return Text(f" {text} ", style=f"bold {style} on {'badge_bg' if style == 'accent' else style}")


def color_dot(hex_color):
    """返回带 ANSI 背景色的圆点文本"""
    if not hex_color:
        return Text("●", style="dim")
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return Text("●", style=f"bold rgb({r},{g},{b})")
    except (ValueError, IndexError):
        return Text("●", style="dim")


def grade_badge(grade):
    """评分等级徽章（带颜色）"""
    colors = {
        'SSS': 'bold #ff6b6b',
        'SS':  'bold #cc785c',
        'S':   'bold #d4a017',
        'A':   'bold #5db872',
        'B':   'bold #8e8b82',
        'C':   'bold #6c6a64',
        'D':   'dim #6c6a64',
    }
    style = colors.get(grade, 'dim')
    return Text(f" {grade} ", style=style)


def bar_chart(value, max_value=20, width=20, filled_char='█', empty_char='░'):
    """彩色条形图"""
    filled = min(value, width)
    bar = filled_char * filled + empty_char * (width - filled)
    if value >= 15:
        style = 'error'
    elif value >= 8:
        style = 'warning'
    else:
        style = 'success'
    return Text(bar, style=style)


def divider(title=None):
    """分隔线"""
    if title:
        console.print(f"  [dim]{'─' * 4}[/] [muted]{title}[/] [dim]{'─' * 40}[/]")
    else:
        console.print(f"  [dim]{'─' * 50}[/]")


def empty_state(icon, message):
    """空状态提示"""
    text = Text()
    text.append(f"\n  {icon}  {message}\n", style="dim")
    console.print(Panel(text, border_style="table_border", box=PANEL_BOX, expand=False))


def kv_pairs(pairs):
    """快速打印键值对（不带表格边框）"""
    for key, val in pairs:
        console.print(f"  [muted]{key}:[/] {val}")
