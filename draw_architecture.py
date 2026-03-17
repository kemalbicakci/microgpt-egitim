"""
MicroGPT genel mimari diyagramını çizer ve architecture_tr.png olarak kaydeder.
Tamamen matplotlib ile — hiçbir ek bağımlılık yok.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(14, 11))
ax.set_xlim(0, 14)
ax.set_ylim(0, 11)
ax.axis('off')
fig.patch.set_facecolor('#1a1a2e')
ax.set_facecolor('#1a1a2e')

# ── Renk paleti ──────────────────────────────────────────────────────────────
C_INPUT   = '#2c3e6e'   # girdi kutuları
C_EMBED   = '#1a5276'   # gömme
C_NORM    = '#4a235a'   # norm
C_ATTN    = '#1a4a2e'   # dikkat
C_MLP     = '#4a3000'   # MLP
C_RES     = '#2e2e2e'   # artık bağlantı arka planı
C_HEAD    = '#5d1a1a'   # LM kafası
C_OUT     = '#1a3a1a'   # çıktı
C_BORDER  = '#e9c46a'
C_ARROW   = '#e9c46a'
C_TEXT    = '#ecf0f1'
C_TITLE   = '#e94f37'
C_MUTED   = '#95a5a6'
C_BLOCK   = '#162136'   # transformer bloğu çerçevesi

def rbox(ax, x, y, w, h, color, border=C_BORDER, lw=1.5, radius=0.18):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle=f"round,pad=0.05,rounding_size={radius}",
                         linewidth=lw, edgecolor=border, facecolor=color, zorder=3)
    ax.add_patch(box)

def txt(ax, x, y, s, size=10, color=C_TEXT, bold=False, ha='center', va='center'):
    ax.text(x, y, s, fontsize=size, color=color,
            fontweight='bold' if bold else 'normal',
            ha=ha, va=va, zorder=5)

def arrow(ax, x1, y1, x2, y2, color=C_ARROW, lw=1.8):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=lw, mutation_scale=14),
                zorder=4)

def dashed_arrow(ax, x1, y1, x2, y2, color='#7f8c8d', lw=1.2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=lw, linestyle='dashed', mutation_scale=12),
                zorder=4)

# ─────────────────────────────────────────────────────────────────────────────
# Sütun x-koordinatları
CX = 7.0   # merkez sütun

# ── Başlık ───────────────────────────────────────────────────────────────────
txt(ax, CX, 10.55, 'MicroGPT — Genel Mimari', size=17, color=C_TITLE, bold=True)
txt(ax, CX, 10.18, 'GPT-2 tarzı yalnızca-çözücü Transformer  ·  saf Python',
    size=10, color=C_MUTED)

# ── Girdi tokeni ─────────────────────────────────────────────────────────────
rbox(ax, CX, 9.55, 3.2, 0.52, C_INPUT)
txt(ax, CX, 9.55, 'Girdi Tokeni   token_id, pos_id', size=10.5, bold=True)
arrow(ax, CX, 9.29, CX, 8.96)

# ── Token + Pozisyon Gömme ───────────────────────────────────────────────────
rbox(ax, CX - 1.1, 8.72, 1.95, 0.44, '#1b4f72')
txt(ax, CX - 1.1, 8.72, 'wte[token_id]', size=9.5)
rbox(ax, CX + 1.1, 8.72, 1.95, 0.44, '#154360')
txt(ax, CX + 1.1, 8.72, 'wpe[pos_id]', size=9.5)

# + işareti
rbox(ax, CX, 8.72, 0.4, 0.36, '#2c3e50', border='#aab7b8', lw=1)
txt(ax, CX, 8.72, '+', size=13, bold=True, color='#f0f0f0')
# token → +
ax.annotate('', xy=(CX - 0.21, 8.72), xytext=(CX - 1.1 + 0.98, 8.72),
            arrowprops=dict(arrowstyle='->', color=C_ARROW, lw=1.4, mutation_scale=12), zorder=4)
# pos → +
ax.annotate('', xy=(CX + 0.21, 8.72), xytext=(CX + 1.1 - 0.98, 8.72),
            arrowprops=dict(arrowstyle='->', color=C_ARROW, lw=1.4, mutation_scale=12), zorder=4)

txt(ax, CX - 3.2, 8.72, 'Token\nGömmesi\n(wte)', size=8.5, color='#aed6f1', ha='center')
txt(ax, CX + 3.2, 8.72, 'Pozisyon\nGömmesi\n(wpe)', size=8.5, color='#aed6f1', ha='center')

arrow(ax, CX, 8.54, CX, 8.12)  # + → RMSNorm

# ── RMSNorm (ilk) ────────────────────────────────────────────────────────────
rbox(ax, CX, 7.90, 3.2, 0.42, C_NORM)
txt(ax, CX, 7.90, 'RMSNorm', size=10.5, bold=True)
arrow(ax, CX, 7.69, CX, 7.36)

# ═══════════════════════════════════════════════════════════════════════════
# Transformer Bloğu çerçevesi
# ═══════════════════════════════════════════════════════════════════════════
blk = FancyBboxPatch((CX - 3.7, 2.32), 7.4, 5.06,
                     boxstyle="round,pad=0.1,rounding_size=0.25",
                     linewidth=2.2, edgecolor='#e9c46a',
                     facecolor=C_BLOCK, zorder=1, linestyle='--')
ax.add_patch(blk)
txt(ax, CX - 3.0, 7.28, '× n_layer', size=9, color='#e9c46a', bold=True, ha='left')
txt(ax, CX + 2.55, 2.44, 'Transformer\nBloğu', size=8.5, color='#e9c46a', ha='center')

# ── Artık bağlantı (dikkat için) — girdi kaydetme ────────────────────────────
# Artık bağlantı sol taraftan geçer
# x_residual = x   noktası → 7.20'de
txt(ax, CX - 3.35, 7.15, 'x_artık = x', size=7.5, color='#7f8c8d', ha='center')
# sol ok aşağı 6.20'e
ax.annotate('', xy=(CX - 3.3, 5.26), xytext=(CX - 3.3, 7.00),
            arrowprops=dict(arrowstyle='->', color='#5d6d7e',
                            lw=1.3, linestyle='dashed', mutation_scale=10), zorder=4)

# ── Çok Başlı Öz-Dikkat ──────────────────────────────────────────────────────
rbox(ax, CX, 7.15, 3.2, 0.42, C_NORM)
txt(ax, CX, 7.15, 'RMSNorm', size=10.5, bold=True)
arrow(ax, CX, 6.94, CX, 6.62)

# Q K V
for xi, lbl in [(CX-1.15, 'Wq\nSorgu'), (CX, 'Wk\nAnahtar'), (CX+1.15, 'Wv\nDeğer')]:
    rbox(ax, xi, 6.38, 0.92, 0.44, C_ATTN)
    txt(ax, xi, 6.38, lbl, size=8.5)

# birleştirme oku
arrow(ax, CX, 6.16, CX, 5.86)
rbox(ax, CX, 5.64, 3.6, 0.42, C_ATTN)
txt(ax, CX, 5.64, 'Çok Başlı Öz-Dikkat  (n_head=4)', size=10, bold=True)
arrow(ax, CX, 5.43, CX, 5.12)

rbox(ax, CX, 4.90, 3.2, 0.42, C_ATTN)
txt(ax, CX, 4.90, 'Wo  — Çıktı Projeksiyonu', size=10)
arrow(ax, CX, 4.69, CX, 4.40)

# Artık toplama (dikkat)
rbox(ax, CX, 4.18, 1.0, 0.38, '#2c3e50', border='#aab7b8', lw=1.2)
txt(ax, CX, 4.18, 'x + artık', size=9, bold=True, color='#f0f0f0')
# artık bağlantı sağdan gelip toplama kutusuna giriyor
ax.annotate('', xy=(CX + 0.52, 4.18), xytext=(CX + 3.3, 4.18),
            arrowprops=dict(arrowstyle='->', color='#5d6d7e',
                            lw=1.3, linestyle='dashed', mutation_scale=10), zorder=4)
ax.plot([CX + 3.3, CX + 3.3], [7.00, 4.18], color='#5d6d7e', lw=1.3, linestyle='--', zorder=3)
txt(ax, CX + 3.55, 5.6, 'Artık\nBağlantı', size=8, color='#5d6d7e', ha='center')
arrow(ax, CX, 3.97, CX, 3.67)

# ── x_residual 2. artık ──────────────────────────────────────────────────────
txt(ax, CX - 3.35, 3.58, 'x_artık = x', size=7.5, color='#7f8c8d', ha='center')
ax.annotate('', xy=(CX - 3.3, 2.56), xytext=(CX - 3.3, 3.46),
            arrowprops=dict(arrowstyle='->', color='#5d6d7e',
                            lw=1.3, linestyle='dashed', mutation_scale=10), zorder=4)

# ── MLP Bloğu ────────────────────────────────────────────────────────────────
rbox(ax, CX, 3.45, 3.2, 0.42, C_NORM)
txt(ax, CX, 3.45, 'RMSNorm', size=10.5, bold=True)
arrow(ax, CX, 3.24, CX, 2.94)

rbox(ax, CX - 0.88, 2.72, 1.54, 0.42, C_MLP)
txt(ax, CX - 0.88, 2.72, 'FC1  (×4 genişlik)', size=9)
rbox(ax, CX + 0.88, 2.72, 1.54, 0.42, C_MLP)
txt(ax, CX + 0.88, 2.72, 'ReLU → FC2', size=9)
ax.annotate('', xy=(CX + 0.1, 2.72), xytext=(CX - 0.1, 2.72),
            arrowprops=dict(arrowstyle='->', color=C_ARROW, lw=1.3, mutation_scale=11), zorder=4)
arrow(ax, CX + 1.65, 2.72, CX + 1.95, 2.72)
ax.plot([CX + 1.95, CX + 1.95], [2.72, 2.44], color=C_ARROW, lw=1.3, zorder=3)
arrow(ax, CX + 1.95, 2.44, CX + 0.52, 2.44)

# Artık toplama (MLP)
rbox(ax, CX, 2.44, 1.0, 0.38, '#2c3e50', border='#aab7b8', lw=1.2)
txt(ax, CX, 2.44, 'x + artık', size=9, bold=True, color='#f0f0f0')
ax.annotate('', xy=(CX - 0.52, 2.44), xytext=(CX - 3.3, 2.44),
            arrowprops=dict(arrowstyle='->', color='#5d6d7e',
                            lw=1.3, linestyle='dashed', mutation_scale=10), zorder=4)
ax.plot([CX - 3.3, CX - 3.3], [3.46, 2.44], color='#5d6d7e', lw=1.3, linestyle='--', zorder=3)
txt(ax, CX - 3.55, 3.0, 'Artık\nBağlantı', size=8, color='#5d6d7e', ha='center')
arrow(ax, CX, 2.25, CX, 1.92)

# ── LM Kafası ────────────────────────────────────────────────────────────────
rbox(ax, CX, 1.70, 3.2, 0.42, C_HEAD)
txt(ax, CX, 1.70, 'LM Kafası  (lm_head)  →  Logitler', size=10.5, bold=True)
arrow(ax, CX, 1.49, CX, 1.18)

# ── Softmax → Çıktı ──────────────────────────────────────────────────────────
rbox(ax, CX, 0.96, 3.2, 0.42, C_OUT)
txt(ax, CX, 0.96, 'Softmax  →  Olasılık Dağılımı  (vocab_size)', size=10.5, bold=True)
arrow(ax, CX, 0.75, CX, 0.46)

rbox(ax, CX, 0.28, 4.2, 0.38, C_INPUT, border='#2ecc71', lw=2)
txt(ax, CX, 0.28, 'Çıktı: Bir Sonraki Harf Tahmini', size=11, bold=True, color='#2ecc71')

# ── Boyut açıklamaları (sağ kenar) ───────────────────────────────────────────
notes = [
    (9.75, 9.55,  'token_id ∈ [0, vocab_size)'),
    (9.75, 8.72,  'n_embd = 16 boyut'),
    (9.75, 7.90,  'karekök-ortalama = 1'),
    (9.75, 5.64,  '4 kafa × 4 boyut'),
    (9.75, 2.72,  '4 × n_embd = 64  →  16'),
    (9.75, 1.70,  'n_embd → vocab_size'),
    (9.75, 0.96,  'Σ olasılık = 1'),
]
for xn, yn, nt in notes:
    ax.plot([xn - 0.15, xn - 0.6], [yn, yn], color='#5d6d7e', lw=0.9, linestyle=':', zorder=2)
    txt(ax, xn, yn, nt, size=8, color='#7f8c8d', ha='left')

# ── Alt not ──────────────────────────────────────────────────────────────────
txt(ax, CX, -0.22,
    'KV önbelleği: keys[li] ve values[li] her adımda büyür — geçmiş tokenleri yeniden hesaplamaya gerek yok',
    size=8, color='#5d6d7e')

plt.tight_layout(pad=0.3)
plt.savefig('architecture_tr.png', dpi=180, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.close()
print("Kaydedildi: architecture_tr.png")
