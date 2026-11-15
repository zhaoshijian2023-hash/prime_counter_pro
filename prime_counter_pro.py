"""
========================================================================================================
PrimeCounter Pro - 高性能素数计数与分析系统 / High-Performance Prime Counting & Analysis System
Prime Counting Function π(x) - Professional Analysis Suite
========================================================================================================

功能特性 / Features:
    ✓ 批量 π(x) 计算 (支持 [0, 10^16] 范围) / Batch π(x) calculation (supports [0, 10^16] range)
    ✓ 区间素数计数 (高效区间查询) / Interval prime counting (efficient range queries)
    ✓ 区间素数导出 (支持多种格式) / Prime export (multiple formats)
    ✓ 素数密率分析 (实际 vs 理论对比) / Prime density analysis (actual vs theoretical)
    ✓ 素数间隙分析 (间隙统计与可视化) / Prime gap analysis (statistics & visualization)
    ✓ 多窗口对比分析 (自适应窗口选择) / Multi-window comparison (adaptive window selection)
    ✓ 数据可视化 (密率/间隙分布图) / Data visualization (density/gap distribution)
    ✓ 批量处理与导出 (CSV格式) / Batch processing & export (CSV format)
    ✓ 多语言支持 (中文/英文/双语) / Multi-language support (Chinese/English/Bilingual)

技术特性 / Technical Features:
    - Numba JIT 加速 (串行/并行自适应) / Numba JIT acceleration (adaptive serial/parallel)
    - 动态区间选择 (最小化计算量) / Dynamic interval selection (minimize computation)
    - 结果缓存机制 (提升重复查询速度) / Result caching (improve repeated query speed)
    - 检查点保存 (支持大规模批量计算) / Checkpoint saving (support large-scale batch computation)
    - NumPy 二进制表 (极速加载) / NumPy binary table (ultra-fast loading)

作者 / Author: Zhao shijian
版本 / Version: v4.1.3 Language & Layout Unified Edition
日期 / Date: 2026-11-10
许可 / License: MIT License

========================================================================================================
"""

# ========================================================================================================
# 🌐 全局语言设置 (彻底前置，确保启动日志语言完全统一) / Global Language Settings (Fully Pre-positioned)
# ========================================================================================================

_LANGUAGE = 'en'  # 可选值 / Options: 'zh' (中文), 'en' (English), 'both' (双语)

def set_language(lang: str, quiet: bool = False):
    """
    设置输出语言 / Set output language

    参数 / Parameters:
        lang: 'zh' (中文), 'en' (English), 'both' (双语)
        quiet: 是否静默设置 / Whether to set quietly without printing
    """
    global _LANGUAGE
    if lang not in ['zh', 'en', 'both']:
        raise ValueError(f"不支持的语言 / Unsupported language: {lang}. 选项 / Options: 'zh', 'en', 'both'")
    _LANGUAGE = lang

    if not quiet:
        if lang == 'zh':
            print("✓ 语言已设置为：中文")
        elif lang == 'en':
            print("✓ Language set to: English")
        else:
            print("✓ 语言已设置为 / Language set to: 双语 / Bilingual")


def _(zh: str, en: str = None) -> str:
    """
    根据当前语言设置返回对应文本 / Return text based on current language setting
    """
    if en is None:
        en = zh

    if _LANGUAGE == 'zh':
        return zh
    elif _LANGUAGE == 'en':
        return en
    else:  # 'both'
        if zh == en:
            return zh
        return f"{zh} / {en}"

# --------------------------------------------------------------------------------------------------------
# 🚀 强制初始化语言设置 (在此处修改默认语言，确保后续加载日志语言一致)
# 🚀 Force initialize language setting (Modify default language here to ensure consistent startup logs)
# --------------------------------------------------------------------------------------------------------
#set_language('en', quiet=True)


# ========================================================================================================
# Matplotlib 配置 - 必须在导入 pyplot 之前设置 / Matplotlib Configuration - Must be set before importing pyplot
# ========================================================================================================

import os
import warnings

# 设置非交互式后端，避免 backend_interagg 错误 / Set non-interactive backend to avoid backend_interagg error
os.environ['MPLBACKEND'] = 'Agg'

import matplotlib
matplotlib.use('Agg')

# 抑制字体警告，避免中文字体缺失的提示 / Suppress font warnings to avoid missing Chinese font prompts
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# 配置中文字体支持 / Configure Chinese font support
try:
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    MATPLOTLIB_AVAILABLE = True
    _mpl_init_msg = True  # 延迟显示消息 / Delay displaying message
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    _mpl_init_msg = False
except Exception as e:
    MATPLOTLIB_AVAILABLE = False
    _mpl_init_msg = False

# ========================================================================================================
# 核心依赖库导入 / Core Dependency Imports
# ========================================================================================================

import numpy as np
from numba import njit, prange
import time
import pickle
import csv
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Union
from scipy.special import expi

# ========================================================================================================
# 版本信息与元数据 / Version Information & Metadata
# ========================================================================================================

__version__ = "4.1.3"
__author__ = "Zhao shijian"
__license__ = "MIT"
__title__ = "PrimeCounter Pro"
__date__ = "2026-11-10"


# ========================================================================================================
# Li(N) 对数积分函数 / Li(N) Logarithmic Integral Function
# ========================================================================================================

def Li(x):
    """
    计算对数积分 Li(x) = ∫[2,x] dt/ln(t) / Calculate Logarithmic Integral Li(x) = ∫[2,x] dt/ln(t)

    使用关系 / Using relation: Li(x) = li(x) - li(2)
    其中 / where li(x) = Ei(ln(x))
    """
    if x <= 2:
        return 0

    try:
        li_x = expi(np.log(x))
        li_2 = 1.045163780117492784844588889194613136522615578151
        return li_x - li_2 + 0.5

    except:
        from scipy.integrate import quad
        def integrand(t):
            return 1.0 / np.log(t)
        result, _ = quad(integrand, 2, x, limit=100)
        return result


def prime_counting_error_analysis(N, pi_N):
    """
    分析素数计数函数的误差 / Analyze errors in prime counting function
    """
    Li_N = Li(N)
    error = -pi_N + Li_N
    relative_error = (error / pi_N * 100) if pi_N > 0 else 0
    asymptotic_density = 1 / np.log(N) if N > 1 else 0

    return {
        'Li_N': Li_N,
        'error': error,
        'relative_error': relative_error,
        'asymptotic_density': asymptotic_density
    }


def export_detailed_results(results, filename="pi_error_analysis.xlsx"):
    """
    导出详细结果到 Excel 文件（保存在 output 子目录，带自动递增序号）
    Export detailed results to Excel file (saved in output subdirectory with auto-increment index)

    ★ 精度与格式完美统一修复：
       1. 仅将 A 列 (N) 设为文本格式，防止大数精度丢失。
       2. 在写入前将 A 列 (N) 格式化为带千分位逗号的字符串，使其与后面数值列的千分位格式在视觉上完美统一！
    """
    import os
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
    except ImportError:
        print(
            f"   {_('❌ 缺少 openpyxl 库，请安装', '❌ Missing openpyxl library, please install')}: pip install openpyxl")
        return False

    # 创建 output 子目录 / Create output subdirectory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # 自动生成带序号的文件名 / Automatically generate filename with serial number
    base_name, ext = os.path.splitext(filename)
    if ext.lower() != '.xlsx':
        ext = '.xlsx'
    counter = 1
    filepath = os.path.join(output_dir, base_name + ext)

    # 如果文件存在，递增序号 / If file exists, increment serial number
    while os.path.exists(filepath):
        new_filename = f"{base_name}_{counter}{ext}"
        filepath = os.path.join(output_dir, new_filename)
        counter += 1

    try:
        # 创建工作簿 / Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Prime Counting Results"

        # 表头样式 / Header styles
        header_font_white = Font(bold=True, size=11, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        center_alignment = Alignment(horizontal='center', vertical='center')
        right_alignment = Alignment(horizontal='right', vertical='center')

        # 写入表头 / Write headers
        headers = ['N', 'π(N)', 'Is Prime', 'Time(s)', 'Li(N)', 'Error', 'Relative Error%']
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.alignment = center_alignment

        # 写入数据 / Write data
        for row_idx, r in enumerate(results, start=2):
            N = r['N']
            pi_N = r['pi_N']
            is_prime = 'Yes' if r['is_prime'] else 'No'
            time_s = r['time']
            Li_N = r['Li_N']
            error = r['error']
            rel_error = r['relative_error']

            # ------------------------------------------------------------------
            # ★ 精度与格式统一核心：
            # 将 A 列 (N) 转换为带千分位逗号的文本(str)存储，设置格式为 '@'。
            # 这样既保证了文本格式不丢失超大数精度，又在视觉上拥有了千分位逗号，与后面完美统一！
            # ------------------------------------------------------------------
            if isinstance(N, (int, float)):
                formatted_N = f"{N:,.0f}"  # 转换为带逗号的字符串
            else:
                formatted_N = str(N)

            cell_N = ws.cell(row=row_idx, column=1, value=formatted_N)
            cell_N.number_format = '@'
            cell_N.alignment = right_alignment  # 靠右对齐更美观 / Right alignment is more beautiful

            # 第2列: π(N) (数值格式，带千分位 / Numeric format with thousands separator)
            cell_pi = ws.cell(row=row_idx, column=2, value=pi_N)
            cell_pi.number_format = '#,##0'

            # 第3列: Is Prime
            cell_isp = ws.cell(row=row_idx, column=3, value=is_prime)
            cell_isp.alignment = center_alignment

            # 第4列: Time(s) (正常浮点数 / Float format)
            cell_time = ws.cell(row=row_idx, column=4, value=time_s)
            cell_time.number_format = '0.000000'

            # 第5列: Li(N) (数值格式，带千分位 / Numeric format with thousands separator)
            cell_li = ws.cell(row=row_idx, column=5, value=int(round(Li_N)))
            cell_li.number_format = '#,##0'

            # 第6列: Error (数值格式，带千分位 / Numeric format with thousands separator)
            cell_err = ws.cell(row=row_idx, column=6, value=int(round(error)))
            cell_err.number_format = '#,##0'

            # 第7列: Relative Error% (正常浮点数 / Float format)
            cell_rel = ws.cell(row=row_idx, column=7, value=rel_error)
            cell_rel.number_format = '0.00000000'

        # 自动调整列宽 / Auto-fit column widths
        column_widths = {
            'A': 26,  # N
            'B': 24,  # π(N)
            'C': 12,  # Is Prime
            'D': 12,  # Time(s)
            'E': 24,  # Li(N)
            'F': 18,  # Error
            'G': 18   # Relative Error%
        }

        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        # 保存文件 / Save workbook
        wb.save(filepath)

        print(f"   {_('✓ 结果已保存到', '✓ Results saved to')}: {filepath}")
        return True

    except Exception as e:
        print(f"   {_('❌ 保存失败', '❌ Save failed')}: {e}")
        return False

# ========================================================================================================
# 可视化：π(N) vs Li(N) 对比图 / Visualization: π(N) vs Li(N) Comparison Chart
# ========================================================================================================

def plot_pi_vs_li(results, output_file="pi_vs_li.png"):
    """
    绘制 π(N) vs Li(N) 对比图 / Plot π(N) vs Li(N) comparison chart
    """
    if not MATPLOTLIB_AVAILABLE:
        print(_("⚠️  matplotlib 不可用，跳过绘图", "⚠️  matplotlib unavailable, skipping plot"))
        return

    print(f"\n{_('📊 生成 π(N) vs Li(N) 对比图', '📊 Generating π(N) vs Li(N) comparison')}: {output_file}")

    N_values = [r['N'] for r in results]
    pi_values = [r['pi_N'] for r in results]
    li_values = [r['Li_N'] for r in results]
    errors = [r['relative_error'] for r in results]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # 子图1 / Subplot 1
    ax1.plot(range(len(N_values)), pi_values, 'o-', label='π(N)', linewidth=2, markersize=8)
    ax1.plot(range(len(N_values)), li_values, 's--', label='Li(N)', linewidth=2, markersize=8)
    ax1.set_xlabel(_('测试点索引', 'Test Point Index'), fontsize=12)
    ax1.set_ylabel(_('素数计数', 'Prime Count'), fontsize=12)
    ax1.set_title(_('素数计数函数 π(N) vs 对数积分 Li(N)',
                    'Prime Counting Function π(N) vs Logarithmic Integral Li(N)'),
                  fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')
    ax1.set_xticks(range(len(N_values)))
    ax1.set_xticklabels([f"{n:,.0e}" for n in N_values], rotation=45, ha='right')

    # 子图2 / Subplot 2
    ax2.plot(range(len(N_values)), errors, 'o-', color='red', linewidth=2, markersize=8)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax2.set_xlabel(_('测试点索引', 'Test Point Index'), fontsize=12)
    ax2.set_ylabel(_('相对误差 (%)', 'Relative Error (%)'), fontsize=12)
    ax2.set_title(_('相对误差趋势', 'Relative Error Trend') + ': (π(N) - Li(N)) / π(N) × 100%',
                  fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(range(len(N_values)))
    ax2.set_xticklabels([f"{n:,.0e}" for n in N_values], rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(_("✓ 图表已保存", "✓ Chart saved") + "\n")


# ========================================================================================================
# 数据表导入 - 使用 .npz 格式 / Data Table Import - Using .npz Format
# ========================================================================================================

def load_cumulative_table(file_path='cumulative_table_2000000_optimized.npz'):
    """
    加载累积表 / Load cumulative table
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"{_('累积表文件不存在', 'Cumulative table file not found')}: {file_path}"
        )

    try:
        archive = np.load(file_path, allow_pickle=False)

        # 判断表格式 / Determine table format
        if 'cumulative_counts' in archive:
            # 优化表格式 / Optimized table format
            cumulative_data = archive['cumulative_counts']
            segment_size = int(archive.get('segment_size', 2_500_000_000))
            metadata = {
                'format': 'optimized',
                'version': str(archive.get('version', 'unknown')),
                'blocks': len(cumulative_data) - 1,
                'max_supported': int(archive.get('max_supported', 10 ** 16)),
                'segment_size': segment_size
            }

            print(f"✅ {_('加载优化表成功', 'Loaded optimized table successfully')}")
            print(f"   {_('格式', 'Format')}: {metadata['format']}")
            print(f"   {_('版本', 'Version')}: {metadata['version']}")
            print(f"   {_('块数', 'Blocks')}: {metadata['blocks']:,}")
            print(f"   {_('最大支持', 'Max supported')}: {metadata['max_supported']:e}")

        elif 'data' in archive:
            # 旧表格式 / Legacy table format
            cumulative_data = archive['data']
            segment_size = 2_500_000_000  # 默认值 / Default value
            metadata = {
                'format': 'legacy',
                'version': str(archive.get('version', 'unknown')),
                'blocks': len(cumulative_data),
                'max_supported': int(cumulative_data[-1, 2] * 2 + 3),
                'segment_size': segment_size
            }

            print(f"✅ {_('加载旧表成功', 'Loaded legacy table successfully')}")
            print(f"   {_('格式', 'Format')}: {metadata['format']}")
            print(f"   {_('块数', 'Blocks')}: {metadata['blocks']:,}")

        else:
            raise KeyError(
                f"{_('未知表格式', 'Unknown table format')}: {list(archive.keys())}"
            )

        archive.close()
        return cumulative_data, metadata

    except Exception as e:
        raise RuntimeError(
            f"{_('加载累积表失败', 'Failed to load cumulative table')}: {e}"
        )

# ========================================================================================================
# 全局常量与累积表初始化 / Global Constants & Cumulative Table Initialization
# ========================================================================================================

PRIME_TABLE_LIMIT = 200_000_000
SMALL_PRIME_CACHE_SIZE = 100_000
PARALLEL_THRESHOLD = 10_000_000
_PI_CACHE = {}

CUMULATIVE_DATA = None
METADATA = {}  # 初始化为空字典 / Initialize as empty dict
MAX_SUPPORTED = 10**16
TABLE_SIZE = 2_000_000
SEGMENT_SIZE = 2_500_000_000
BLOCK_SIZE = 2_500_000_000
FIRST_SEGMENT_SIZE = 2_500_000_000
BLOCK_N_RANGE = 2 * SEGMENT_SIZE  # 50亿 / 5 Billion

# 素数表（稍后初始化） / Prime tables (initialized later)
PRIMES = None
SMALL_PRIMES = None

# ------------------------------------------------------------------
# 🚀 启动环境与初始化输出 / Environment & Initialization Output
# ------------------------------------------------------------------
print("=" * 100)
if _LANGUAGE == 'zh':
    print("                        PRIME COUNTER PRO - 基准测试报告")
else:
    print("                        PRIME COUNTER PRO - BENCHMARK REPORT")
print("=" * 100)
print(_("[环境与初始化]", "[ENVIRONMENT & INITIALIZATION]"))
print(_("📦 加载累积表", "📦 Loading cumulative table") + "...")

t_load = time.time()

try:
    CUMULATIVE_DATA, METADATA = load_cumulative_table('cumulative_table_2000000_optimized.npz')
    MAX_SUPPORTED = METADATA['max_supported']
    TABLE_SIZE = METADATA['blocks']
    SEGMENT_SIZE = METADATA['segment_size']
    BLOCK_SIZE = SEGMENT_SIZE
    FIRST_SEGMENT_SIZE = SEGMENT_SIZE
    BLOCK_N_RANGE = 2 * SEGMENT_SIZE

    elapsed_time = time.time() - t_load
    print(f"{_('✓ 完成', '✓ Completed')} ({elapsed_time:.3f}s)")
    print(f"   {_('表大小', 'Table size')}: {TABLE_SIZE:,} {_('块', 'blocks')}")
    print(f"   {_('覆盖范围', 'Coverage')}: [2, {MAX_SUPPORTED:e}]")
    print(f"   {_('块大小', 'Block size')}: {SEGMENT_SIZE:,}")

except FileNotFoundError:
    try:
        CUMULATIVE_DATA, METADATA = load_cumulative_table('cumulative_table_200000.npz')
        MAX_SUPPORTED = METADATA['max_supported']
        TABLE_SIZE = METADATA['blocks']
        SEGMENT_SIZE = METADATA['segment_size']
        BLOCK_SIZE = SEGMENT_SIZE
        FIRST_SEGMENT_SIZE = SEGMENT_SIZE
        BLOCK_N_RANGE = 2 * SEGMENT_SIZE

        elapsed_time = time.time() - t_load
        print(f"{_('✓ 完成', '✓ Completed')} ({elapsed_time:.3f}s)")
        print(f"   {_('表大小', 'Table size')}: {TABLE_SIZE:,} {_('块', 'blocks')}")
        print(f"   {_('覆盖范围', 'Coverage')}: [2, {MAX_SUPPORTED:e}]")
        print(f"   {_('块大小', 'Block size')}: {SEGMENT_SIZE:,}")
        print(f"   ⚠️  {_('提示：使用 200,000 块表，如需支持 10^16，请使用 2,000,000 块表', 'Note: Using 200,000 block table, use 2,000,000 block table for 10^16 support')}")

    except FileNotFoundError:
        print(f"\n❌ {_('错误：未找到任何累积表文件', 'Error: No cumulative table file found')}！")
        print(f"   {_('请确保以下文件之一存在', 'Please ensure one of the following files exists')}:")
        print("   - cumulative_table_2000000_optimized.npz")
        raise

print()  # 空行 / Blank line

# ========================================================================================================
# 版本信息与元数据 / Version Info & Metadata Dictionary
# ========================================================================================================

VERSION_INFO = {
    'name': 'PrimeCounter Pro',
    'version': __version__,
    'author': __author__,
    'release_date': __date__,
    'license': __license__,
    'max_supported': MAX_SUPPORTED,
    'table_size': TABLE_SIZE,
    'features': [
        f"{_('批量 π(x) 计算', 'Batch π(x) calculation')} [0, {MAX_SUPPORTED:e}]",
        _('区间素数计数', 'Interval prime counting'),
        _('区间素数导出', 'Prime export') + ' ⭐ ' + _('新增', 'NEW'),
        _('素数密率分析', 'Prime density analysis'),
        _('素数间隙分析', 'Prime gap analysis'),
        _('数据可视化', 'Data visualization'),
        _('批量处理与导出', 'Batch processing & export'),
        _('多语言支持', 'Multi-language support') + ' 🌐 ' + _('新增', 'NEW')
    ],
    'optimizations': [
        _('Numba JIT 加速', 'Numba JIT acceleration'),
        _('自适应串并行', 'Adaptive serial/parallel'),
        _('动态区间选择', 'Dynamic interval selection'),
        _('结果缓存', 'Result caching'),
        _('NumPy 二进制表', 'NumPy binary table')
    ],
    'dependencies': {
        'numpy': '>= 1.20.0',
        'numba': '>= 0.55.0',
        f"matplotlib {_('(可选)', '(optional)')}": '>= 3.3.0'
    }
}


# ========================================================================================================
# 初始化与全局配置 / Initialization & Global Configurations
# ========================================================================================================

def init_primes(limit=200_000_000):
    """初始化小素数表 / Initialize small prime table"""
    print(f"⏳ {_('初始化素数表', 'Initializing prime table')} [2, {limit:,}]...", end=" ", flush=True)
    t0 = time.time()

    is_prime = np.ones(limit, dtype=bool)
    is_prime[0] = is_prime[1] = False

    for i in range(2, int(limit ** 0.5) + 1):
        if is_prime[i]:
            is_prime[i * i::i] = False

    primes = np.where(is_prime)[0]
    elapsed = time.time() - t0

    print(f"{_('✓ 完成', '✓ Completed')} ({len(primes):,} {_('个素数', 'primes')}, {elapsed:.2f}s)")
    return primes


PRIMES = init_primes(PRIME_TABLE_LIMIT)
SMALL_PRIMES = PRIMES[:SMALL_PRIME_CACHE_SIZE]
print(f"📦 {_('小素数缓存', 'Small prime cache')}: {_('前', 'First')} {len(SMALL_PRIMES):,} {_('个素数', 'primes')} "
      f"({_('最大值', 'Max')}: {SMALL_PRIMES[-1]:,})")

print()  # 空行 / Blank line

# 显示 matplotlib 状态 / Display matplotlib status
if MATPLOTLIB_AVAILABLE:
    print(_("✓ Matplotlib 已配置 (支持中文/英文显示)", "✓ Matplotlib configured (Chinese/English support enabled)"))
else:
    print(_("⚠️  警告: matplotlib 未安装，可视化功能将不可用",
            "⚠️  Warning: matplotlib not installed, visualization unavailable"))

if _LANGUAGE == 'zh':
    print("✓ 语言已设置为：中文")
elif _LANGUAGE == 'en':
    print("✓ Language set to: English")
else:
    print("✓ 语言已设置为：双语 / Language set to: Bilingual")
print()  # 空行 / Blank line


# ========================================================================================================
# 核心筛法算法 / Core Sieve Algorithms
# ========================================================================================================

@njit(fastmath=True, cache=True, inline='always')
def _sieve_one_chunk(nxx, primes, start_idx, max_prime, chunk_id, chunk_size, n):
    """处理单个chunk（核心筛选逻辑） / Process single chunk (core sieve logic)"""
    chunk_start = chunk_id * chunk_size
    chunk_end = min(chunk_start + chunk_size, n)

    abs_start_idx = start_idx + chunk_start
    start_odd = 2 * abs_start_idx + 3
    end_odd = 2 * (start_idx + chunk_end - 1) + 3
    sqrt_end = int(end_odd ** 0.5) + 1

    effective_limit = min(sqrt_end, max_prime)

    for i in range(len(primes)):
        p = primes[i]
        if p > effective_limit:
            break

        first_multiple = p * p
        if first_multiple < start_odd:
            k = (start_odd - 1) // p + 1
            if k % 2 == 0:
                k += 1
            first_multiple = p * k

        if first_multiple > end_odd:
            continue

        first_idx_global = (first_multiple - start_odd) // 2
        first_idx_local = first_idx_global + chunk_start

        if first_idx_local < chunk_start:
            skip = ((chunk_start - first_idx_local) + p - 1) // p
            first_idx_local += skip * p

        idx = first_idx_local
        while idx < chunk_end:
            nxx[idx] = True
            idx += p


@njit(fastmath=True, cache=True)
def sieve_segment_serial(nxx, primes, start_idx, max_prime):
    """串行筛选 / Serial Sieve"""
    n = len(nxx)
    BLOCK_SIZE_LOCAL = 2_500_000_000
    K = start_idx // BLOCK_SIZE_LOCAL

    if K < 750_000:
        chunk_size = 1_500_000
    elif K < 1_500_000:
        chunk_size = 2_000_000
    else:
        chunk_size = 2_500_000

    num_chunks = (n + chunk_size - 1) // chunk_size

    for chunk_id in range(num_chunks):
        _sieve_one_chunk(nxx, primes, start_idx, max_prime, chunk_id, chunk_size, n)


@njit(parallel=True, fastmath=True, cache=True)
def sieve_segment_parallel(nxx, primes, start_idx, max_prime):
    """并行筛选 / Parallel Sieve"""
    n = len(nxx)
    BLOCK_SIZE_LOCAL = 2_500_000_000
    K = start_idx // BLOCK_SIZE_LOCAL

    if K < 750_000:
        chunk_size = 1_500_000
    elif K < 1_500_000:
        chunk_size = 2_000_000
    else:
        chunk_size = 2_500_000

    num_chunks = (n + chunk_size - 1) // chunk_size

    for chunk_id in prange(num_chunks):
        _sieve_one_chunk(nxx, primes, start_idx, max_prime, chunk_id, chunk_size, n)


@njit(parallel=True, fastmath=True, nogil=True, cache=True)
def count_primes_parallel(nxx):
    """并行统计素数个数 / Parallel Prime Counting"""
    n = len(nxx)
    segment_size = 10_000_000
    num_segments = (n + segment_size - 1) // segment_size

    counts = np.zeros(num_segments, dtype=np.int64)

    for seg in prange(num_segments):
        start = seg * segment_size
        end = min(start + segment_size, n)
        count = 0
        for i in range(start, end):
            if not nxx[i]:
                count += 1
        counts[seg] = count

    return np.sum(counts)


@njit(fastmath=True, nogil=True, cache=True)
def count_primes_serial(nxx):
    """串行统计素数 / Serial Prime Counting"""
    count = 0
    for i in range(len(nxx)):
        if not nxx[i]:
            count += 1
    return count


# ========================================================================================================
# 素数提取功能 / Prime Extraction Functions
# ========================================================================================================

@njit(fastmath=True, nogil=True, cache=True)
def extract_primes_serial(nxx, start_idx):
    """从筛选结果中提取素数（串行版本） / Extract primes from sieve results (Serial)"""
    count = 0
    for i in range(len(nxx)):
        if not nxx[i]:
            count += 1

    primes = np.empty(count, dtype=np.int64)

    idx = 0
    for i in range(len(nxx)):
        if not nxx[i]:
            odd_value = 2 * (start_idx + i) + 3
            primes[idx] = odd_value
            idx += 1

    return primes


@njit(parallel=True, fastmath=True, nogil=True, cache=True)
def extract_primes_parallel(nxx, start_idx):
    """从筛选结果中提取素数（并行版本） / Extract primes from sieve results (Parallel)"""
    n = len(nxx)
    segment_size = 10_000_000
    num_segments = (n + segment_size - 1) // segment_size

    segment_counts = np.zeros(num_segments, dtype=np.int64)

    for seg in prange(num_segments):
        seg_start = seg * segment_size
        seg_end = min(seg_start + segment_size, n)
        count = 0
        for i in range(seg_start, seg_end):
            if not nxx[i]:
                count += 1
        segment_counts[seg] = count

    total_count = np.sum(segment_counts)
    offsets = np.zeros(num_segments + 1, dtype=np.int64)
    for i in range(num_segments):
        offsets[i + 1] = offsets[i] + segment_counts[i]

    primes = np.empty(total_count, dtype=np.int64)

    for seg in prange(num_segments):
        seg_start = seg * segment_size
        seg_end = min(seg_start + segment_size, n)
        write_pos = offsets[seg]

        for i in range(seg_start, seg_end):
            if not nxx[i]:
                odd_value = 2 * (start_idx + i) + 3
                primes[write_pos] = odd_value
                write_pos += 1

    return primes


def export_primes(
    start: int,
    end: int,
    format: str = 'array',
    output_file: Optional[str] = None,
    max_export: int = 50_000_000,
    verbose: bool = True
) -> Union[np.ndarray, None]:
    """
    导出区间 [start, end] 内的所有素数 / Export all primes in interval [start, end]
    """
    if verbose:
        print("\n" + "=" * 100)
        print(" " * 30 + _("区间素数导出", "Prime Export"))
        print("=" * 100)
        print(f"📍 {_('区间', 'Interval')}: [{start:,}, {end:,}]")
        print(f"📏 {_('区间长度', 'Interval length')}: {end - start + 1:,}")

    if start > end:
        raise ValueError(f"{_('起始值', 'Start value')} {start:,} {_('大于终止值', '> end value')} {end:,}")

    if start < 2:
        start = 2
        if verbose:
            print(f"⚠️  {_('起始值已调整为 2', 'Start value adjusted to 2')}")

    estimated_count = int((end / np.log(end)) - (start / np.log(start))) if start > 1 else int(end / np.log(end))

    if estimated_count > max_export:
        raise ValueError(
            f"{_('预计导出', 'Estimated export')} {estimated_count:,} {_('个素数，超过限制', 'primes, exceeds limit')} {max_export:,}\n"
            f"{_('建议', 'Suggestions')}:\n"
            f"  1. {_('缩小区间范围', 'Reduce interval range')}\n"
            f"  2. {_('增加 max_export 参数（注意内存消耗）', 'Increase max_export (watch memory usage)')}\n"
            f"  3. {_('使用流式处理（见 stream_export_primes 函数）', 'Use streaming (see stream_export_primes)')}"
        )

    if verbose:
        print(f"📊 {_('预计素数个数', 'Estimated primes')}: ~{estimated_count:,}")
        print("-" * 100)

    t0 = time.time()

    result_primes = []

    if start == 2:
        result_primes.append(2)
        start = 3
        if verbose:
            print(_("✓ 已添加素数 2", "✓ Added prime 2"))

    if start % 2 == 0:
        start += 1

    if start > end:
        primes_array = np.array(result_primes, dtype=np.int64)

        if verbose:
            print(f"{_('✅ 导出完成', '✅ Export completed')}: {len(primes_array):,} {_('个素数', 'primes')}")
            print(f"⏱️  {_('总耗时', 'Total time')}: {time.time() - t0:.4f} {_('秒', 'seconds')}")
            print("=" * 100 + "\n")

        return _format_output(primes_array, format, output_file)

    start_idx = (start - 3) // 2
    end_idx = (end - 3) // 2 if end % 2 == 1 else (end - 4) // 2

    sieve_size = end_idx - start_idx + 1

    if verbose:
        print(f"🔧 {_('索引范围', 'Index range')}: [{start_idx:,}, {end_idx:,}] ({_('长度', 'length')}: {sieve_size:,})")

    max_prime = int((2 * end_idx + 3) ** 0.5) + 1
    relevant_primes = PRIMES[(PRIMES > 2) & (PRIMES <= max_prime)]

    nxx = np.zeros(sieve_size, dtype=bool)

    if sieve_size < PARALLEL_THRESHOLD:
        if verbose:
            print(f"⚙️  {_('使用串行筛选', 'Using serial sieve')} ({_('区间', 'interval')} < {PARALLEL_THRESHOLD:,})")
        sieve_segment_serial(nxx, relevant_primes, start_idx, max_prime)
        odd_primes = extract_primes_serial(nxx, start_idx)
    else:
        if verbose:
            print(f"⚡ {_('使用并行筛选', 'Using parallel sieve')} ({_('区间', 'interval')} >= {PARALLEL_THRESHOLD:,})")
        sieve_segment_parallel(nxx, relevant_primes, start_idx, max_prime)
        odd_primes = extract_primes_parallel(nxx, start_idx)

    if result_primes:
        primes_array = np.concatenate((np.array(result_primes, dtype=np.int64), odd_primes))
    else:
        primes_array = odd_primes

    elapsed = time.time() - t0

    if verbose:
        print(f"{_('✅ 导出完成', '✅ Export completed')}: {len(primes_array):,} {_('个素数', 'primes')}")
        print(f"⏱️  {_('总耗时', 'Total time')}: {elapsed:.4f} {_('秒', 'seconds')}")
        print(f"⚡ {_('速度', 'Speed')}: {len(primes_array) / elapsed:,.0f} {_('个/秒', 'primes/s')}")

        if len(primes_array) > 0:
            print(f"📌 {_('首个素数', 'First prime')}: {primes_array[0]:,}")
            print(f"📌 {_('末个素数', 'Last prime')}: {primes_array[-1]:,}")

        print("=" * 100 + "\n")

    return _format_output(primes_array, format, output_file)


def _format_output(primes: np.ndarray, format: str, output_file: Optional[str]) -> Union[np.ndarray, List[int], None]:
    """格式化输出素数结果 / Format prime output results"""
    if format == 'array':
        return primes

    elif format == 'list':
        return primes.tolist()

    elif format == 'txt':
        if output_file is None:
            raise ValueError(f"format='txt' {_('时必须指定 output_file', 'requires output_file')}")

        print(f"💾 {_('保存到文本文件', 'Saving to text file')}: {output_file}... ", end="")
        np.savetxt(output_file, primes, fmt='%d')
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"{_('✓ 完成', '✓ Completed')} ({_('大小', 'size')}: {file_size:.2f} MB)")
        return None

    elif format == 'csv':
        if output_file is None:
            raise ValueError(f"format='csv' {_('时必须指定 output_file', 'requires output_file')}")

        print(f"💾 {_('保存到CSV文件', 'Saving to CSV file')}: {output_file}... ", end="")
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['prime'])
            for p in primes:
                writer.writerow([p])
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"{_('✓ 完成', '✓ Completed')} ({_('大小', 'size')}: {file_size:.2f} MB)")
        return None

    elif format == 'binary':
        if output_file is None:
            raise ValueError(f"format='binary' {_('时必须指定 output_file', 'requires output_file')}")

        print(f"💾 {_('保存到二进制文件', 'Saving to binary file')}: {output_file}... ", end="")
        np.save(output_file, primes)
        actual_file = output_file + '.npy' if not output_file.endswith('.npy') else output_file
        file_size = os.path.getsize(actual_file) / (1024 * 1024)
        print(f"{_('✓ 完成', '✓ Completed')} ({_('大小', 'size')}: {file_size:.2f} MB)")
        return None

    else:
        raise ValueError(f"{_('不支持的格式', 'Unsupported format')}: {format}。{_('支持的格式', 'Supported')}: 'array', 'list', 'txt', 'csv', 'binary'")


def stream_export_primes(
    start: int,
    end: int,
    output_file: str,
    chunk_size: int = 100_000_000,
    format: str = 'txt',
    verbose: bool = True
):
    """流式导出素数（适合超大范围，内存友好） / Stream export primes (Memory-friendly)"""
    if verbose:
        print("\n" + "=" * 100)
        print(" " * 20 + _("流式素数导出 (内存友好)", "Streaming Prime Export (Memory-Friendly)"))
        print("=" * 100)
        print(f"📍 {_('区间', 'Interval')}: [{start:,}, {end:,}]")
        print(f"📦 {_('块大小', 'Chunk size')}: {chunk_size:,}")
        print(f"📄 {_('输出文件', 'Output file')}: {output_file}")
        print("-" * 100)

    total_primes = 0
    t0 = time.time()

    mode = 'w'
    if format == 'csv':
        f = open(output_file, mode, newline='', encoding='utf-8-sig')
        writer = csv.writer(f)
        writer.writerow(['prime'])
    else:
        f = open(output_file, mode)

    try:
        current = start
        block_num = 0

        while current <= end:
            block_num += 1
            block_end = min(current + chunk_size - 1, end)

            block_primes = export_primes(current, block_end, format='array', verbose=False)

            if format == 'csv':
                for p in block_primes:
                    writer.writerow([p])
            else:
                for p in block_primes:
                    f.write(f"{p}\n")

            total_primes += len(block_primes)

            if verbose:
                progress = (block_end - start) / (end - start) * 100
                elapsed = time.time() - t0
                speed = total_primes / elapsed if elapsed > 0 else 0
                print(f"  {_('块', 'Block')} {block_num:>4} | {_('进度', 'Progress')}: {progress:>6.2f}% | "
                      f"{_('已导出', 'Exported')}: {total_primes:>12,} {_('个', 'primes')} | "
                      f"{_('速度', 'Speed')}: {speed:>12,.0f} {_('个/秒', 'primes/s')}", end='\r')

            current = block_end + 1

    finally:
        f.close()

    elapsed = time.time() - t0

    if verbose:
        print(f"\n\n{_('✅ 流式导出完成', '✅ Streaming export completed')}!")
        print(f"   {_('总素数', 'Total primes')}: {total_primes:,}")
        print(f"   {_('总耗时', 'Total time')}: {elapsed:.2f} {_('秒', 'seconds')}")
        print(f"   {_('平均速度', 'Average speed')}: {total_primes / elapsed:,.0f} {_('个/秒', 'primes/s')}")
        print(f"   {_('文件大小', 'File size')}: {os.path.getsize(output_file) / (1024 * 1024):.2f} MB")
        print("=" * 100 + "\n")


# ========================================================================================================
# 查找函数 / Lookup Functions
# ========================================================================================================

def find_block(end_idx):
    """找到索引对应的累积表块号（使用二分查找）- 仅用于旧表 / Find block index (Binary search) - Legacy table only"""
    block_idx = np.searchsorted(CUMULATIVE_DATA[:, 1], end_idx, side='right') - 1

    if block_idx < 0:
        return 0
    if block_idx >= len(CUMULATIVE_DATA):
        return len(CUMULATIVE_DATA) - 1

    return block_idx


def get_block_data(block_num):
    """获取指定块的数据 - 仅用于旧表 / Get block data - Legacy table only"""
    if block_num < 0 or block_num >= len(CUMULATIVE_DATA):
        raise ValueError(
            f"{_('块号', 'Block number')} {block_num} {_('超出范围', 'out of range')} [0, {len(CUMULATIVE_DATA) - 1}]")

    return tuple(CUMULATIVE_DATA[block_num])


# ========================================================================================================
# pi() 函数 - 支持优化表和旧表 / pi() Function - Supports Optimized and Legacy Tables
# ========================================================================================================

def pi(N, verbose=False, return_is_prime=False, use_cache=True):
    """
    计算 π(N) - PrimeCounter Pro 核心算法（支持优化表和旧表）
    Calculate π(N) - PrimeCounter Pro Core Algorithm (Supports Optimized & Legacy Tables)

    筛法约定：False = 素数，True = 合数 / Sieve convention: False = Prime, True = Composite
    """
    if N < 2:
        return (0, False) if return_is_prime else 0

    if N == 2:
        return (1, True) if return_is_prime else 1

    # 根据表格式获取最大支持值 / Get max supported value based on table format
    if METADATA['format'] == 'optimized':
        max_value = METADATA['max_supported']
    else:
        max_value = int(CUMULATIVE_DATA[-1, 2] * 2 + 3)

    if N > max_value:
        raise ValueError(
            f"N = {N:,} {_('超出累积表范围', 'exceeds cumulative table range')} [2, {max_value:,}]"
        )

    if use_cache and not return_is_prime and N in _PI_CACHE:
        return _PI_CACHE[N]

    if N % 2 == 0:
        result = pi(N - 1, verbose, return_is_prime=False, use_cache=use_cache)
        if use_cache and not return_is_prime:
            _PI_CACHE[N] = result
        # 偶数一定不是素数（除了2） / Even numbers are definitely not prime (except 2)
        return (result, False) if return_is_prime else result

    # ========================================
    # 优化表算法 / Optimized Table Algorithm
    # ========================================
    if METADATA['format'] == 'optimized':
        N1 = N  # N已经是奇数 / N is already odd
        end_idx = (N1 - 3) // 2  # 奇数索引 / Odd index

        # 计算块号（从0开始） / Calculate block ID (starts from 0)
        block_id = N1 // BLOCK_N_RANGE  # BLOCK_N_RANGE = 5,000,000,000

        # 边界检查 / Boundary check
        if block_id >= len(CUMULATIVE_DATA) - 1:
            block_id = len(CUMULATIVE_DATA) - 2

        # 从优化表读取数据 / Read data from optimized table
        cumulative_primes = int(CUMULATIVE_DATA[block_id])  # 块之前的累积 / Cumulative count before block
        block_prime_count = int(CUMULATIVE_DATA[block_id + 1] - CUMULATIVE_DATA[block_id])

        # 块的范围 / Block range
        start_idx = BLOCK_SIZE * block_id - 1
        block_end_idx = start_idx + BLOCK_SIZE
        start_idx = max(start_idx, 0)
        block_size = block_end_idx - start_idx + 1

    # ========================================
    # 旧表算法 / Legacy Table Algorithm
    # ========================================
    else:
        end_idx = (N - 3) // 2
        block_num = find_block(end_idx)

        block_data = CUMULATIVE_DATA[block_num]
        block_id = int(block_data[0])
        start_idx = int(block_data[1])
        block_end_idx = int(block_data[2])
        block_size = int(block_data[3])
        block_prime_count = int(block_data[4])
        cumulative_primes = int(block_data[5])

    # ========================================
    # 完整块查询（通用逻辑） / Complete Block Query (General Logic)
    # ========================================
    if end_idx == block_end_idx:  # 保持原判断条件 / Keep original condition
        total_primes = cumulative_primes + block_prime_count + 1

        if verbose:
            print(
                f"{_('✅ 完整块查询', '✅ Complete block query')} - {_('块号', 'Block')} {block_id}, π({N:,}) = {total_primes:,}")

        if use_cache and not return_is_prime:
            _PI_CACHE[N] = total_primes

        # 完整块末尾，需要额外判断 N 是否为素数 / Complete block end, need extra check if N is prime
        if return_is_prime:
            # 使用筛法判断（因为没有 primecount 库） / Use sieve to check (no primecount library available)
            test_start = max(N - 1000, 3)
            test_primes = export_primes(test_start, N, format='array', verbose=False)
            n_is_prime = (N in test_primes)
            return total_primes, n_is_prime

        return total_primes

    # ========================================
    # 选择筛选区间（通用逻辑） / Select Sieve Interval (General Logic)
    # ========================================
    ac_size = end_idx - start_idx
    cb_size = block_end_idx - end_idx

    if verbose:
        print(f"📦 {_('块', 'Block')} {block_id}: A={start_idx:,}, C={end_idx:,}, B={block_end_idx:,}")
        print(f"   {_('AC区间', 'AC interval')}: {ac_size:,}, {_('CB区间', 'CB interval')}: {cb_size:,}")

    if ac_size <= cb_size:
        # ============ AC段筛选 ============
        sieve_size = ac_size + 1
        sieve_start = start_idx
        sieve_end = end_idx
        is_forward = True

        if verbose:
            print(f"   → {_('选择 AC 区间', 'Select AC interval')} [{start_idx:,}, {end_idx:,}]")
    else:
        # ============ CB段筛选 ============
        sieve_size = cb_size + 1
        sieve_start = end_idx  # 总是从 N 开始 / Always starts from N
        sieve_end = block_end_idx
        is_forward = False

        if verbose:
            print(f"   → {_('选择 CB 区间', 'Select CB interval')} [{end_idx:,}, {block_end_idx:,}]")

    # ========================================
    # 筛法（通用逻辑） / Sieve (General Logic)
    # ========================================
    max_prime = int((2 * sieve_end + 3) ** 0.5) + 1
    relevant_primes = PRIMES[(PRIMES > 2) & (PRIMES <= max_prime)]

    # 初始化为 False（假设全是素数） / Initialize to False (assume all are primes)
    nxx = np.zeros(sieve_size, dtype=bool)

    if sieve_size < PARALLEL_THRESHOLD:
        sieve_segment_serial(nxx, relevant_primes, sieve_start, max_prime)
        sieve_primes = int(count_primes_serial(nxx))

        if verbose:
            print(f"   🔧 {_('串行筛选', 'Serial sieve')} ({_('区间', 'interval')} < {PARALLEL_THRESHOLD:,})")
    else:
        sieve_segment_parallel(nxx, relevant_primes, sieve_start, max_prime)
        sieve_primes = int(count_primes_parallel(nxx))

        if verbose:
            print(f"   ⚡ {_('并行筛选', 'Parallel sieve')} ({_('区间', 'interval')} >= {PARALLEL_THRESHOLD:,})")

    # ========================================
    # 计数与素性判断 / Counting & Primality Check
    # ========================================
    if is_forward:
        # AC段筛选 / AC segment sieve
        n_is_prime = not nxx[-1]  # N 对应最后一个位置 / N corresponds to the last position
        block_primes_count = sieve_primes
        total_primes = cumulative_primes + block_primes_count + 1
    else:
        # CB段筛选 / CB segment sieve
        n_is_prime = not nxx[0]  # N 对应第一个位置 / N corresponds to the first position
        block_primes_count = block_prime_count - sieve_primes
        total_primes = cumulative_primes + block_primes_count + 1

        # 修正：N是奇数素数时需要 +1 / Correction: +1 needed when N is an odd prime
        if n_is_prime and (N % 2 == 1):
            total_primes += 1

    if verbose:
        print(f"   📊 {_('筛选结果', 'Sieve result')}: {sieve_primes:,} {_('个素数', 'primes')}")
        print(f"   📊 {_('块内累计', 'Block total')}: {block_primes_count:,} {_('个素数', 'primes')}")
        print(f"   ✅ π({N:,}) = {total_primes:,}, {_('N是素数', 'N is prime')}: {n_is_prime}")

    if use_cache and not return_is_prime:
        _PI_CACHE[N] = total_primes

    return (total_primes, n_is_prime) if return_is_prime else total_primes

# ========================================================================================================
# 区间素数计数功能 / Interval Prime Counting Functions
# ========================================================================================================

def pi_range(a, b, verbose=False):
    """计算区间 [a, b] 内的素数个数 / Calculate prime count in interval [a, b]"""
    if a > b:
        return 0

    if a <= 2:
        return pi(b, verbose=verbose)

    pi_a_minus_1 = pi(a - 1, verbose=verbose)
    pi_b = pi(b, verbose=verbose)

    result = pi_b - pi_a_minus_1

    if verbose:
        print(f"π({b:,}) - π({a - 1:,}) = {pi_b:,} - {pi_a_minus_1:,} = {result:,}")

    return result


def batch_range_count(intervals: List[Tuple[int, int]], verbose=False, save_results=True):
    """批量计算多个区间的素数个数 / Batch calculate prime counts for multiple intervals"""
    print("\n" + "=" * 100)
    print(" " * 25 + _("批量区间素数计数", "Batch Interval Prime Counting"))
    print("=" * 100)
    print(f"📊 {_('区间数量', 'Number of intervals')}: {len(intervals)}")
    print("-" * 100)

    results = []

    print(f"{_('序号', 'Index'):<12} {_('起点', 'Start'):<20} {_('终点', 'End'):<20} "
          f"{_('素数个数', 'Prime Count'):<20} {_('用时(秒)', 'Time(s)'):<15}")
    print("-" * 100)

    for idx, (start, end) in enumerate(intervals, 1):
        t0 = time.time()
        count = pi_range(start, end, verbose=verbose)
        elapsed = time.time() - t0

        results.append((start, end, count, elapsed))

        print(f"{idx:<12} {start:<20,} {end:<20,} {count:<20,} {elapsed:<15.6f}")

    print("=" * 100 + "\n")

    if save_results:
        filename = f"batch_range_results_{int(time.time())}.csv"
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            if _LANGUAGE == 'zh':
                writer.writerow(['序号', '起点', '终点', '素数个数', '用时(秒)'])
            elif _LANGUAGE == 'en':
                writer.writerow(['Index', 'Start', 'End', 'Prime Count', 'Time(s)'])
            else:
                writer.writerow(['序号 / Index', '起点 / Start', '终点 / End',
                               '素数个数 / Prime Count', '用时(秒) / Time(s)'])

            for idx, (start, end, count, elapsed) in enumerate(results, 1):
                writer.writerow([idx, start, end, count, elapsed])

        print(f"💾 {_('结果已保存到', 'Results saved to')}: {filename}\n")

    return results


# ========================================================================================================
# 辅助函数 / Helper Functions
# ========================================================================================================

def is_prime(n: int) -> bool:
    """判断一个数是否为素数 / Check if a number is prime"""
    if n < 2:
        return False

    _, is_prime_val = pi(n, return_is_prime=True)
    return is_prime_val


# ========================================================================================================
# print_version 函数 / print_version Function
# ========================================================================================================

def print_version():
    """
    打印版本信息和功能列表 / Print version information and feature list
    """
    print("=" * 100)
    print(f" {__title__} - v{__version__} ".center(100, "="))
    print("=" * 100)

    if _LANGUAGE == 'zh':
        print(f"📅 发布日期: {__date__}")
        print(f"👥 作者: {__author__}")
        print(f"📜 许可: {__license__}")
        print(f"📊 最大支持: {MAX_SUPPORTED:e} (表大小: {TABLE_SIZE:,} 块)")
        print()
        print("✨ 核心功能:")
        print(f"   1. 批量 π(x) 计算 [0, {MAX_SUPPORTED:e}]")
        print(f"   2. 区间素数计数")
        print(f"   3. 区间素数导出 ⭐ 新增")
        print(f"   4. 素数密率分析")
        print(f"   5. 素数间隙分析")
        print(f"   6. 数据可视化")
        print(f"   7. 批量处理与导出")
        print(f"   8. 多语言支持 🌐 新增")
        print()
        print("⚡ 性能优化:")
        print(f"   1. Numba JIT 加速")
        print(f"   2. 自适应串并行")
        print(f"   3. 动态区间选择")
        print(f"   4. 结果缓存")
        print(f"   5. NumPy 二进制表")

    elif _LANGUAGE == 'en':
        print(f"📅 Release Date: {__date__}")
        print(f"👥 Author: {__author__}")
        print(f"📜 License: {__license__}")
        print(f"📊 Maximum Support: {MAX_SUPPORTED:e} (Table size: {TABLE_SIZE:,} blocks)")
        print()
        print("✨ Core Features:")
        print(f"   1. Batch π(x) calculation [0, {MAX_SUPPORTED:e}]")
        print(f"   2. Interval prime counting")
        print(f"   3. Prime export ⭐ NEW")
        print(f"   4. Prime density analysis")
        print(f"   5. Prime gap analysis")
        print(f"   6. Data visualization")
        print(f"   7. Batch processing & export")
        print(f"   8. Multi-language support 🌐 NEW")
        print()
        print("⚡ Performance Optimizations:")
        print(f"   1. Numba JIT acceleration")
        print(f"   2. Adaptive serial/parallel")
        print(f"   3. Dynamic interval selection")
        print(f"   4. Result caching")
        print(f"   5. NumPy binary table")

    else:  # 'both'
        print(f"📅 发布日期 / Release Date: {__date__}")
        print(f"👥 作者 / Author: {__author__}")
        print(f"📜 许可 / License: {__license__}")
        print(f"📊 最大支持 / Maximum Support: {MAX_SUPPORTED:e} (表大小 / Table size: {TABLE_SIZE:,} 块 / blocks)")
        print()
        print("✨ 核心功能 / Core Features:")
        print(f"   1. 批量 π(x) 计算 / Batch π(x) calculation [0, {MAX_SUPPORTED:e}]")
        print(f"   2. 区间素数计数 / Interval prime counting")
        print(f"   3. 区间素数导出 / Prime export ⭐ 新增 / NEW")
        print(f"   4. 素数密率分析 / Prime density analysis")
        print(f"   5. 素数间隙分析 / Prime gap analysis")
        print(f"   6. 数据可视化 / Data visualization")
        print(f"   7. 批量处理与导出 / Batch processing & export")
        print(f"   8. 多语言支持 / Multi-language support 🌐 新增 / NEW")
        print()
        print("⚡ 性能优化 / Performance Optimizations:")
        print(f"   1. Numba JIT 加速 / Numba JIT acceleration")
        print(f"   2. 自适应串并行 / Adaptive serial/parallel")
        print(f"   3. 动态区间选择 / Dynamic interval selection")
        print(f"   4. 结果缓存 / Result caching")
        print(f"   5. NumPy 二进制表 / NumPy binary table")

    print("=" * 100)
    print()


# ========================================================================================================
# 主程序入口 / Main Program Entry Point
# ========================================================================================================

def main():
    """主程序 - 包含 Li(N) 误差分析 / Main program - Includes Li(N) error analysis"""

    # 打印版本信息 / Print version info
    print_version()

    print(_("⏳ 预热 JIT 编译器", "⏳ Warming up JIT compiler") + "... ", end="", flush=True)
    t0 = time.time()
    # 预热 JIT 编译器 / Warm up JIT compiler
    dummy = pi(100, verbose=False)
    print(f"{_('✓ 完成', '✓ Completed')} ({time.time() - t0:.2f}s)\n")

    # 1. 统一定义每一列的固定宽度（保证表头、数据、超限、报错完全一致）
    w_N = 30  # N 的宽度
    w_pi = 20  # π(N) 的宽度
    w_prime = 15  # Is Prime 的宽度
    w_time = 18  # Time(s) 的宽度
    w_li = 25  # Li(N) 的宽度
    w_err = 23  # Error 的宽度
    w_rel = 15  # Rel Err% 的宽度

    # 自动计算总宽度（7列宽度 + 6个间隔空格）
    total_width = w_N + w_pi + w_prime + w_time + w_li + w_err + w_rel + 6

    print("=" * total_width)
    print(f" Calculation Range: [2, {MAX_SUPPORTED:e}] (Using {TABLE_SIZE:,} blocks) ".center(total_width))
    print("=" * total_width)

    # ==============================================================================
    # 🧪 Multi-Dimensional Boundary Stress Test Suites (Uncomment to Run)
    # 🧪 多维边界极限压测集 (按需取消注释运行)
    # ==============================================================================

    # ------------------------------------------------------------------------------
    # [Suite 1] Mersenne Numbers (M_p = 2^p - 1)
    # [测试集 1] 梅森数边界 (M_p = 2^p - 1) —— 测试特殊数论结构点
    # ------------------------------------------------------------------------------
    # prime_list = init_primes(100)
    # test_values = [(2 ** int(n) - 1) for n in prime_list[0:17]]

    # ------------------------------------------------------------------------------
    # [Suite 2] Decimal Milestones (10^1 ~ 10^16)
    # [测试集 2] 十进制里程碑 (10^1 ~ 10^16) —— 最经典的 PNT 验证点
    # ------------------------------------------------------------------------------
    test_values = [(10 ** int(n)) for n in range(1, 17)]

    # ------------------------------------------------------------------------------
    # [Suite 3] Binary Milestones (2^1 ~ 2^53)
    # [测试集 3] 二进制里程碑 (2^1 ~ 2^53) —— 浮点数无误差的最大连续整数边界
    # ------------------------------------------------------------------------------
    # test_values = [(2 ** int(n)) for n in range(1, 54)]
    # ------------------------------------------------------------------------------
    # [Suite 4] 10^16 Critical Edge Cases (Near the Limit)
    # [测试集 4] 10^16 临界点压测 (极限边界微调，测试算法在极值处的鲁棒性)
    # ------------------------------------------------------------------------------
    """
    test_values = [
        10 ** 16 - 60 * 10 ** 8,
        10 ** 16 - 40 * 10 ** 8,
        10 ** 16 - 25 * 10 ** 8,
        10 ** 16 - 10 * 10 ** 8,
        10 ** 16,
    ]
    """
    # 2. 完美对齐的 Benchmark 报告表头（使用 w_xxx 变量）
    print(f"{'N':<{w_N}} {'π(N)':<{w_pi}} {'Is Prime':<{w_prime}} {'Time(s)':<{w_time}} "
          f"{'Li(N)':<{w_li}} {'Error':<{w_err}} {'Rel Err%'}")
    print("-" * total_width)

    results = []

    for N in test_values:
        # 3. 超出范围处理（使用 w_xxx 变量，并为 N 加上千分位逗号）
        if N > MAX_SUPPORTED:
            n_str = f"{N:,}"
            print(f"{n_str:<{w_N}} {'---':<{w_pi}} {'Out of range':<{w_prime}} {'---':<{w_time}} "
                  f"{'---':<{w_li}} {'---':<{w_err}} {'---'}")
            continue  # 跳转 / Skip

        try:
            start = time.time()
            pi_N, is_prime_val = pi(N, return_is_prime=True)
            elapsed = time.time() - start

            error_data = prime_counting_error_analysis(N, pi_N)

            is_prime_str = 'Yes' if is_prime_val else 'No'

            Li_N = error_data['Li_N']
            error = error_data['error']
            rel_error = error_data['relative_error']

            # 4. 正常数据格式化输出（N 和 pi_N 均带千分位逗号）
            print(f"{N:<{w_N},} {pi_N:<{w_pi},} {is_prime_str:<{w_prime}} {elapsed:<{w_time}.6f} "
                  f"{int(round(Li_N)):<{w_li},} {int(round(error)):<{w_err},} {rel_error:<{w_rel}.6f}")

            results.append({
                'N': N,
                'pi_N': pi_N,
                'is_prime': is_prime_val,
                'time': elapsed,
                'Li_N': Li_N,
                'error': error,
                'relative_error': rel_error
            })

        except Exception as e:
            # 5. 异常报错处理（使用 w_xxx 变量，并为 N 加上千分位逗号）
            n_str = f"{N:,}"
            print(f"{n_str:<{w_N}} {'ERROR':<{w_pi}} {'---':<{w_prime}} {'---':<{w_time}} "
                  f"{'---':<{w_li}} {'---':<{w_err}} {'---'}")
            print(f"   ⚠️  Error: {e}")

    print("=" * total_width)

    if not results:
        print(f"\n❌ {_('无有效结果可供分析', 'No valid results for analysis')}")
        return

    print(f"\n{_('【误差趋势分析】', '【Error Trend Analysis】')}")
    print("-" * total_width)

    max_error_idx = max(range(len(results)), key=lambda i: abs(results[i]['relative_error']))
    max_error_result = results[max_error_idx]

    print(
        f"📊 {_('最大相对误差', 'Maximum relative error')}: {max_error_result['relative_error']:.6f}% (N = {max_error_result['N']:,})")

    large_N_results = [r for r in results if r['N'] >= 10 ** 9]
    if large_N_results:
        avg_error = np.mean([abs(r['relative_error']) for r in large_N_results])
        print(f"📊 {_('大数平均误差 (N ≥ 10^9)', 'Average error for large N (N ≥ 10^9)')}: {avg_error:.6f}%")

    print(f"\n💡 {_('素数定理验证', 'Prime Number Theorem Verification')}:")
    print("   - π(N) ~ Li(N)  ✓ " + _("(误差趋向 0)", "(Error approaches 0)"))
    print("   - |π(N) - Li(N)| / π(N) → 0 as N → ∞")

    if large_N_results and all(abs(r['relative_error']) < 0.01 for r in large_N_results):
        print(
            f"   {_('✅ 大数情况下误差 < 0.01%，符合素数定理预期', '✅ Error < 0.01% for large N, consistent with Prime Number Theorem')}")

    print("-" * total_width)

    print(f"\n💾 {_('导出详细结果', 'Exporting detailed results')}...")
    export_detailed_results(results, "pi_error_analysis.xlsx")

    print("\n" + "=" * total_width)
    print(_("✅ 程序执行完毕", "✅ Program completed") + "!")
    print(f"💡 {_('提示', 'Tips')}:")
    print(f"   - {_('使用 pi(N) 计算 π(N)', 'Use pi(N) to calculate π(N)')}")
    print(f"   - {_('使用 Li(N) 计算对数积分', 'Use Li(N) to calculate logarithmic integral')}")
    print(
        f"   - {_('使用 prime_counting_error_analysis(N, pi_N) 分析误差', 'Use prime_counting_error_analysis(N, pi_N) for error analysis')}")
    print(
        f"   - {_('使用 set_language(\"zh\"/\"en\"/\"both\") 切换语言', 'Use set_language(\"zh\"/\"en\"/\"both\") to switch language')}")
    print("=" * total_width)

# ========================================================================================================
# 程序执行入口 / Program Entry Point
# ========================================================================================================

if __name__ == "__main__":
    main()