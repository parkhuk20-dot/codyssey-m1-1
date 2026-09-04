"""공통 차트 스타일. 검증된 팔레트(dataviz 기준)를 슬롯 단위로 정의한다."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SURFACE   = "#fcfcfb"
INK       = "#0b0b0b"
INK_2     = "#52514e"
MUTED     = "#898781"
GRID      = "#e1e0d9"
AXIS      = "#c3c2b7"

# 카테고리 슬롯 (고정 순서, 순환 금지)
S1_BLUE   = "#2a78d6"
S2_ORANGE = "#eb6834"
S3_AQUA   = "#1baf7a"
DIV_COOL  = "#2a78d6"   # 발산형 한랭 극
DIV_WARM  = "#e34948"   # 발산형 온난 극
DIV_MID   = "#f0efec"   # 중립 중점

# 단일 색상 순차 램프 (blue 100 -> 700)
BLUE_RAMP = ["#cde2fb","#b7d3f6","#9ec5f4","#86b6ef","#6da7ec","#5598e7","#3987e5",
             "#2a78d6","#256abf","#1c5cab","#184f95","#104281","#0d366b"]
SEQ_CMAP  = LinearSegmentedColormap.from_list("seqblue", BLUE_RAMP)
# 순서형(ordinal) 램프: 표면 대비 2:1 확보를 위해 step250(#86b6ef)부터 시작
ORD_CMAP  = LinearSegmentedColormap.from_list("ordblue", BLUE_RAMP[3:])

plt.rcParams.update({
    "font.family": "Noto Sans CJK JP",
    "axes.unicode_minus": False,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS,
    "axes.linewidth": 0.8,
    "axes.labelcolor": INK_2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "font.size": 10,
    "legend.frameon": False,
})

def frame(ax, ygrid=True):
    """축·격자를 후퇴시킨다. 격자는 실선 헤어라인."""
    for s in ("top","right"):
        ax.spines[s].set_visible(False)
    for s in ("left","bottom"):
        ax.spines[s].set_color(AXIS); ax.spines[s].set_linewidth(0.8)
    if ygrid:
        ax.set_axisbelow(True)
        ax.grid(axis="y", color=GRID, linewidth=0.8, linestyle="-")
        ax.grid(axis="x", visible=False)

def titles(ax, title, subtitle=None):
    """제목/부제를 축 위쪽에 겹치지 않게 쌓는다."""
    if subtitle:
        ax.text(0, 1.135, title, transform=ax.transAxes, color=INK,
                fontsize=13.5, fontweight="600", va="bottom", ha="left")
        ax.text(0, 1.035, subtitle, transform=ax.transAxes, color=INK_2,
                fontsize=10, va="bottom", ha="left")
    else:
        ax.text(0, 1.035, title, transform=ax.transAxes, color=INK,
                fontsize=13.5, fontweight="600", va="bottom", ha="left")

def save(fig, path):
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print("  저장:", path)
