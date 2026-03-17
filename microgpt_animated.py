"""
The most atomic way to train and run inference for a GPT in pure, dependency-free Python.
This file is the complete algorithm.
Everything else is just efficiency.

@karpathy

--- ANIMATED TEACHING VERSION ---
Same algorithm. All static plots replaced with matplotlib animations so you can
*watch* the model learn:
  • training_curves_animated.gif  — loss curve building up step-by-step
  • attention_animated.gif        — attention heatmap evolving during training
  • weight_dist_animated.gif      — weight histogram shifting from noise → signal
  • embedding_pca_animated.gif    — token embeddings in 2D PCA space, clusters forming
  • generation_animated.gif       — name generated character-by-character with prob bars
"""

import os       # os.path.exists
import math     # math.log, math.exp
import random   # random.seed, random.choices, random.gauss, random.shuffle
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
random.seed(42) # Let there be order among chaos

# ---------------------------------------------------------------------------
# How many training snapshots to capture for animation
# (more = smoother gif, but slower training)
# ---------------------------------------------------------------------------
N_SNAPSHOTS = 25   # evenly-spaced checkpoints throughout training

# ---------------------------------------------------------------------------
# Animated visualization helpers
# ---------------------------------------------------------------------------

def animate_training_curves(loss_history, lr_history):
    """
    Animate the training loss and learning-rate curves building up step-by-step.
    You see exactly when the loss drops and how the LR decays alongside it.
    """
    steps = list(range(1, len(loss_history) + 1))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle('Training Progress (animated)', fontsize=14, fontweight='bold')

    line1, = ax1.plot([], [], color='steelblue', linewidth=1.2, alpha=0.9)
    line2, = ax2.plot([], [], color='seagreen',  linewidth=1.5)

    ax1.set_xlim(1, len(steps))
    ax1.set_ylim(min(loss_history) * 0.9, max(loss_history) * 1.05)
    ax1.set_ylabel('Loss'); ax1.set_title('Training Loss')
    ax1.grid(True, alpha=0.3)
    step_label = ax1.text(0.98, 0.95, '', transform=ax1.transAxes,
                          ha='right', va='top', fontsize=9, color='navy')

    ax2.set_xlim(1, len(steps))
    ax2.set_ylim(0, max(lr_history) * 1.1)
    ax2.set_ylabel('Learning Rate'); ax2.set_xlabel('Step')
    ax2.set_title('Learning Rate Schedule (linear decay)')
    ax2.grid(True, alpha=0.3)

    # Only animate a subset of frames to keep the gif small
    stride = max(1, len(steps) // 150)
    frame_indices = list(range(0, len(steps), stride))
    if frame_indices[-1] != len(steps) - 1:
        frame_indices.append(len(steps) - 1)

    def update(fi):
        idx = frame_indices[fi]
        line1.set_data(steps[:idx + 1], loss_history[:idx + 1])
        line2.set_data(steps[:idx + 1], lr_history[:idx + 1])
        step_label.set_text(f'step {steps[idx]:4d}  loss {loss_history[idx]:.4f}')
        return line1, line2, step_label

    ani = animation.FuncAnimation(fig, update, frames=len(frame_indices),
                                  interval=30, blit=True)
    plt.tight_layout()
    ani.save('training_curves_animated.gif', writer='pillow', fps=30)
    plt.show()
    print("Saved training_curves_animated.gif")


def animate_attention_heatmap(attn_snapshots, steps_shown, token_labels=None):
    """
    Animate the self-attention weight matrix across training checkpoints.
    Each frame = one snapshot.  Brighter = more attention.

    attn_snapshots : list of 2-D lists (seq_len × seq_len), values in [0, 1]
    steps_shown    : list of step numbers corresponding to each snapshot
    token_labels   : optional list of character strings for tick labels
    """
    seq_len = len(attn_snapshots[0])
    fig, ax = plt.subplots(figsize=(6, 5))

    im = ax.imshow([[0.0] * seq_len] * seq_len,
                   cmap='Blues', vmin=0, vmax=1, aspect='auto')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Attention weight')
    title_obj = ax.set_title(f'Attention — step {steps_shown[0]}')
    ax.set_xlabel('Key position (attended-to)')
    ax.set_ylabel('Query position (attending)')

    if token_labels is not None and len(token_labels) == seq_len:
        ax.set_xticks(range(seq_len)); ax.set_xticklabels(token_labels, fontsize=8)
        ax.set_yticks(range(seq_len)); ax.set_yticklabels(token_labels, fontsize=8)

    note = ax.text(0.01, 0.01, 'Lower-left triangle = causal mask',
                   transform=ax.transAxes, fontsize=7, color='gray')

    def update(frame):
        im.set_data(attn_snapshots[frame])
        title_obj.set_text(f'Self-Attention Weights — step {steps_shown[frame]}')
        return im, title_obj, note

    ani = animation.FuncAnimation(fig, update, frames=len(attn_snapshots),
                                  interval=300, blit=True)
    plt.tight_layout()
    ani.save('attention_animated.gif', writer='pillow', fps=4)
    plt.show()
    print("Saved attention_animated.gif")


def animate_weight_distribution(weight_snapshots, steps_shown):
    """
    Animate a histogram of all weight values at each training checkpoint.
    Watch the distribution go from wide-random → narrower-trained.
    """
    all_vals = [v for snap in weight_snapshots for v in snap]
    xmin, xmax = min(all_vals), max(all_vals)

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.suptitle('Weight Distribution Over Training', fontsize=13, fontweight='bold')

    def update(frame):
        ax.cla()
        vals = weight_snapshots[frame]
        mean_v = sum(vals) / len(vals)
        std_v  = (sum((v - mean_v) ** 2 for v in vals) / len(vals)) ** 0.5
        ax.hist(vals, bins=80, color='steelblue', edgecolor='white',
                alpha=0.85, range=(xmin, xmax))
        ax.axvline(mean_v, color='red',    linestyle='--', linewidth=1.5,
                   label=f'mean = {mean_v:.4f}')
        ax.axvline(mean_v + std_v, color='orange', linestyle=':', linewidth=1.2,
                   label=f'±1σ = {std_v:.4f}')
        ax.axvline(mean_v - std_v, color='orange', linestyle=':', linewidth=1.2)
        ax.set_xlim(xmin, xmax)
        ax.set_xlabel('Weight value')
        ax.set_ylabel('Count')
        ax.set_title(f'step {steps_shown[frame]:4d}  |  {len(vals):,} parameters')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        return []

    ani = animation.FuncAnimation(fig, update, frames=len(weight_snapshots),
                                  interval=350, blit=False)
    plt.tight_layout()
    ani.save('weight_dist_animated.gif', writer='pillow', fps=3)
    plt.show()
    print("Saved weight_dist_animated.gif")


def animate_token_generation(generation_steps, uchars_list):
    """
    Animate name generation character by character.
    Top panel: partial text built so far.
    Bottom panel: bar chart of top-k next-token probabilities.

    generation_steps : list of (partial_text, top_k_indices, top_k_probs)
    """
    TOP_K = 10   # show this many candidate characters per step

    fig = plt.figure(figsize=(10, 6))
    gs = GridSpec(2, 1, figure=fig, height_ratios=[1, 2], hspace=0.45)
    ax_text = fig.add_subplot(gs[0])
    ax_bar  = fig.add_subplot(gs[1])
    fig.suptitle('Autoregressive Text Generation (animated)',
                 fontsize=13, fontweight='bold')

    def update(frame):
        partial, topk_ids, topk_probs = generation_steps[frame]
        # --- top panel: text so far ---
        ax_text.cla()
        ax_text.axis('off')
        display = partial if partial else '▏'  # blinking-cursor placeholder
        ax_text.text(0.5, 0.5, f'"{display}"',
                     ha='center', va='center', fontsize=20,
                     fontfamily='monospace', fontweight='bold',
                     bbox=dict(boxstyle='round,pad=0.5',
                               facecolor='lightyellow', alpha=0.9))
        ax_text.set_title(f'Characters generated: {len(partial)}', fontsize=10)

        # --- bottom panel: next-token probs ---
        ax_bar.cla()
        chars  = [uchars_list[i] if i < len(uchars_list) else '<BOS>'
                  for i in topk_ids]
        colors = ['gold' if j == 0 else 'steelblue' for j in range(len(chars))]
        bars = ax_bar.bar(chars, topk_probs, color=colors, edgecolor='white')
        ax_bar.set_ylim(0, 1)
        ax_bar.set_ylabel('Probability')
        ax_bar.set_xlabel('Next character (top candidates)')
        ax_bar.set_title(f'Next-token distribution  —  chosen: "{chars[0]}" '
                         f'(p={topk_probs[0]:.2f})')
        ax_bar.grid(True, alpha=0.3, axis='y')
        # label bars with their probability
        for bar, p in zip(bars, topk_probs):
            if p > 0.01:
                ax_bar.text(bar.get_x() + bar.get_width() / 2,
                            p + 0.01, f'{p:.2f}', ha='center',
                            va='bottom', fontsize=8)
        return []

    ani = animation.FuncAnimation(fig, update, frames=len(generation_steps),
                                  interval=700, blit=False)
    plt.tight_layout()
    ani.save('generation_animated.gif', writer='pillow', fps=1.5)
    plt.show()
    print("Saved generation_animated.gif")


def pca_2d(rows):
    """
    Pure-Python PCA: project a list of float vectors down to 2D.
    Uses power iteration to find the top-2 principal components.
    No numpy required.
    """
    n, d = len(rows), len(rows[0])
    # 1. Center
    mean = [sum(rows[i][j] for i in range(n)) / n for j in range(d)]
    X = [[rows[i][j] - mean[j] for j in range(d)] for i in range(n)]

    def dot(a, b): return sum(ai * bi for ai, bi in zip(a, b))
    def normalize(v):
        norm = dot(v, v) ** 0.5
        return [vi / (norm + 1e-10) for vi in v]
    def mat_vec(M, vec):   # M is d×d
        return [sum(M[i][j] * vec[j] for j in range(d)) for i in range(d)]

    # 2. Covariance matrix  C = Xᵀ X / n   (d × d)
    C = [[sum(X[k][i] * X[k][j] for k in range(n)) / n for j in range(d)] for i in range(d)]

    # 3. Power iteration for PC1
    pc1 = normalize([math.sin(i * 1.3 + 0.7) for i in range(d)])  # deterministic start
    for _ in range(200):
        pc1 = normalize(mat_vec(C, pc1))

    # 4. Deflate C to remove PC1 direction, then find PC2
    lam1 = dot(mat_vec(C, pc1), pc1)
    C2 = [[C[i][j] - lam1 * pc1[i] * pc1[j] for j in range(d)] for i in range(d)]
    pc2 = normalize([math.cos(i * 1.7 + 0.3) for i in range(d)])
    # Orthogonalise against pc1 before iterating
    proj = dot(pc2, pc1)
    pc2 = normalize([pc2[j] - proj * pc1[j] for j in range(d)])
    for _ in range(200):
        pc2 = normalize(mat_vec(C2, pc2))

    # 5. Project
    return [(dot(X[i], pc1), dot(X[i], pc2)) for i in range(n)]


def animate_embedding_pca(wte_snapshots, steps_shown, uchars_list):
    """
    Animate the 2-D PCA projection of the token embedding table (wte) across
    training checkpoints.

    What to watch:
      • At step 0 embeddings are random — no structure.
      • As training proceeds, vowels (red) and consonants (blue) cluster apart.
      • Similar-sounding characters (e.g. 'b'/'p', 'a'/'e') drift close together.
      • <BOS> (green star) drifts away from all regular characters — it has a
        unique distributional role (start/end of name).

    This is the clearest window into *what the model has learned to represent*.
    """
    vowels = set('aeiouAEIOU')
    from matplotlib.lines import Line2D

    print("  Computing PCA projections …", flush=True)
    all_coords = []
    for wte in wte_snapshots:
        rows = [[v for v in row] for row in wte]   # already plain floats
        all_coords.append(pca_2d(rows))

    # Fixed axis limits across all frames for a stable view
    all_x = [c[0] for coords in all_coords for c in coords]
    all_y = [c[1] for coords in all_coords for c in coords]
    xpad = (max(all_x) - min(all_x)) * 0.12
    ypad = (max(all_y) - min(all_y)) * 0.12
    xlim = (min(all_x) - xpad, max(all_x) + xpad)
    ylim = (min(all_y) - ypad, max(all_y) + ypad)

    fig, ax = plt.subplots(figsize=(8, 7))
    legend_handles = [
        Line2D([0],[0], marker='o', color='w', markerfacecolor='#e74c3c',
               markersize=9, label='vowel'),
        Line2D([0],[0], marker='o', color='w', markerfacecolor='#3498db',
               markersize=9, label='consonant'),
        Line2D([0],[0], marker='*', color='w', markerfacecolor='#2ecc71',
               markersize=12, label='<BOS>'),
    ]

    def update(frame):
        ax.cla()
        coords = all_coords[frame]
        # Regular characters
        for i, (x, y) in enumerate(coords[:-1]):   # last entry = BOS
            ch = uchars_list[i]
            color = '#e74c3c' if ch in vowels else '#3498db'
            ax.scatter(x, y, color=color, s=55, zorder=3, alpha=0.85)
            ax.text(x, y + (ylim[1] - ylim[0]) * 0.012, ch,
                    ha='center', va='bottom', fontsize=8,
                    color=color, fontweight='bold')
        # BOS token
        bx, by = coords[-1]
        ax.scatter(bx, by, color='#2ecc71', s=130, marker='*', zorder=4)
        ax.text(bx, by + (ylim[1] - ylim[0]) * 0.012, '<BOS>',
                ha='center', va='bottom', fontsize=7, color='#27ae60')

        ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        ax.set_xlabel('PC 1  (direction of greatest variance)', fontsize=9)
        ax.set_ylabel('PC 2', fontsize=9)
        ax.set_title(f'Token Embedding Space (PCA) — step {steps_shown[frame]}',
                     fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.18)
        ax.legend(handles=legend_handles, loc='upper right', fontsize=9)
        return []

    ani = animation.FuncAnimation(fig, update, frames=len(all_coords),
                                  interval=400, blit=False)
    plt.tight_layout()
    ani.save('embedding_pca_animated.gif', writer='pillow', fps=3)
    plt.show()
    print("Saved embedding_pca_animated.gif")


def visualize_hyperparams(hparams: dict):
    """Display all hyperparameters as a formatted matplotlib table (static, kept as-is)."""
    rows = [[k, str(v['value']), v['desc']] for k, v in hparams.items()]
    _, ax = plt.subplots(figsize=(10, len(rows) * 0.5 + 1.5))
    ax.axis('off')
    tbl = ax.table(
        cellText=rows,
        colLabels=['Parameter', 'Value', 'Description'],
        loc='center', cellLoc='left'
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.6)
    for col in range(3):
        tbl[0, col].set_facecolor('#2c3e50')
        tbl[0, col].set_text_props(color='white', fontweight='bold')
    for row in range(1, len(rows) + 1):
        color = '#ecf0f1' if row % 2 == 0 else 'white'
        for col in range(3):
            tbl[row, col].set_facecolor(color)
    ax.set_title('Model & Training Hyperparameters', fontsize=14, fontweight='bold', pad=12)
    plt.tight_layout()
    plt.savefig('hyperparams.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved hyperparams.png")


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

if not os.path.exists('input.txt'):
    import urllib.request
    names_url = 'https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt'
    urllib.request.urlretrieve(names_url, 'input.txt')
docs = [line.strip() for line in open('input.txt') if line.strip()]
random.shuffle(docs)
print(f"num docs: {len(docs)}")

uchars = sorted(set(''.join(docs)))
BOS = len(uchars)
vocab_size = len(uchars) + 1
print(f"vocab size: {vocab_size}")

# ---------------------------------------------------------------------------
# Autograd
# ---------------------------------------------------------------------------

class Value:
    __slots__ = ('data', 'grad', '_children', '_local_grads')

    def __init__(self, data, children=(), local_grads=()):
        self.data = data
        self.grad = 0
        self._children = children
        self._local_grads = local_grads

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data + other.data, (self, other), (1, 1))

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data * other.data, (self, other), (other.data, self.data))

    def __pow__(self, other): return Value(self.data**other, (self,), (other * self.data**(other-1),))
    def log(self): return Value(math.log(self.data), (self,), (1/self.data,))
    def exp(self): return Value(math.exp(self.data), (self,), (math.exp(self.data),))
    def relu(self): return Value(max(0, self.data), (self,), (float(self.data > 0),))
    def __neg__(self): return self * -1
    def __radd__(self, other): return self + other
    def __sub__(self, other): return self + (-other)
    def __rsub__(self, other): return other + (-self)
    def __rmul__(self, other): return self * other
    def __truediv__(self, other): return self * other**-1
    def __rtruediv__(self, other): return other * self**-1

    def backward(self):
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._children:
                    build_topo(child)
                topo.append(v)
        build_topo(self)
        self.grad = 1
        for v in reversed(topo):
            for child, local_grad in zip(v._children, v._local_grads):
                child.grad += local_grad * v.grad

# ---------------------------------------------------------------------------
# Hyperparameters
# ---------------------------------------------------------------------------

n_layer = 1
n_embd = 16
block_size = 16
n_head = 4
head_dim = n_embd // n_head

learning_rate = 0.01
beta1 = 0.85
beta2 = 0.99
eps_adam = 1e-8

num_steps = 1000
temperature = 0.5

HPARAMS = {
    'n_layer':       {'value': n_layer,       'desc': 'Depth of transformer (number of layers)'},
    'n_embd':        {'value': n_embd,        'desc': 'Embedding dimension (network width)'},
    'block_size':    {'value': block_size,    'desc': 'Max context length (attention window)'},
    'n_head':        {'value': n_head,        'desc': 'Number of attention heads'},
    'head_dim':      {'value': head_dim,      'desc': 'Dimension per attention head (n_embd // n_head)'},
    'vocab_size':    {'value': vocab_size,    'desc': 'Total unique tokens (chars + BOS)'},
    'learning_rate': {'value': learning_rate, 'desc': 'Adam optimizer learning rate'},
    'beta1':         {'value': beta1,         'desc': 'Adam first-moment decay coefficient'},
    'beta2':         {'value': beta2,         'desc': 'Adam second-moment decay coefficient'},
    'eps_adam':      {'value': eps_adam,      'desc': 'Adam epsilon for numerical stability'},
    'num_steps':     {'value': num_steps,     'desc': 'Total training steps'},
    'temperature':   {'value': temperature,   'desc': 'Inference sampling temperature (0,1]'},
}
visualize_hyperparams(HPARAMS)

# ---------------------------------------------------------------------------
# Model parameters (weights)
# ---------------------------------------------------------------------------

matrix = lambda nout, nin, std=0.08: [[Value(random.gauss(0, std)) for _ in range(nin)] for _ in range(nout)]
state_dict = {'wte': matrix(vocab_size, n_embd), 'wpe': matrix(block_size, n_embd), 'lm_head': matrix(vocab_size, n_embd)}
for i in range(n_layer):
    state_dict[f'layer{i}.attn_wq'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wk'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wv'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wo'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.mlp_fc1'] = matrix(4 * n_embd, n_embd)
    state_dict[f'layer{i}.mlp_fc2'] = matrix(n_embd, 4 * n_embd)
params = [p for mat in state_dict.values() for row in mat for p in row]
print(f"num params: {len(params)}")

# ---------------------------------------------------------------------------
# Model architecture
# ---------------------------------------------------------------------------

def linear(x, w):
    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]

def softmax(logits):
    max_val = max(val.data for val in logits)
    exps = [(val - max_val).exp() for val in logits]
    total = sum(exps)
    return [e / total for e in exps]

def rmsnorm(x):
    ms = sum(xi * xi for xi in x) / len(x)
    scale = (ms + 1e-5) ** -0.5
    return [xi * scale for xi in x]

def gpt(token_id, pos_id, keys, values):
    tok_emb = state_dict['wte'][token_id]
    pos_emb = state_dict['wpe'][pos_id]
    x = [t + p for t, p in zip(tok_emb, pos_emb)]
    x = rmsnorm(x)
    for li in range(n_layer):
        x_residual = x
        x = rmsnorm(x)
        q = linear(x, state_dict[f'layer{li}.attn_wq'])
        k = linear(x, state_dict[f'layer{li}.attn_wk'])
        v = linear(x, state_dict[f'layer{li}.attn_wv'])
        keys[li].append(k)
        values[li].append(v)
        x_attn = []
        for h in range(n_head):
            hs = h * head_dim
            q_h = q[hs:hs+head_dim]
            k_h = [ki[hs:hs+head_dim] for ki in keys[li]]
            v_h = [vi[hs:hs+head_dim] for vi in values[li]]
            attn_logits = [sum(q_h[j] * k_h[t][j] for j in range(head_dim)) / head_dim**0.5 for t in range(len(k_h))]
            attn_weights = softmax(attn_logits)
            head_out = [sum(attn_weights[t] * v_h[t][j] for t in range(len(v_h))) for j in range(head_dim)]
            x_attn.extend(head_out)
        x = linear(x_attn, state_dict[f'layer{li}.attn_wo'])
        x = [a + b for a, b in zip(x, x_residual)]
        x_residual = x
        x = rmsnorm(x)
        x = linear(x, state_dict[f'layer{li}.mlp_fc1'])
        x = [xi.relu() for xi in x]
        x = linear(x, state_dict[f'layer{li}.mlp_fc2'])
        x = [a + b for a, b in zip(x, x_residual)]
    logits = linear(x, state_dict['lm_head'])
    return logits


def capture_attention_matrix(tokens):
    """
    Run a *no-grad* forward pass on `tokens` and return the average-over-heads
    attention weight matrix for layer 0 as a plain 2-D list of floats.
    Used only for snapshot collection — does NOT touch .grad.
    """
    n = min(block_size, len(tokens) - 1)
    snap_keys   = [[] for _ in range(n_layer)]
    snap_values = [[] for _ in range(n_layer)]
    # n × n matrix, rows = query positions, cols = key positions
    attn_mat = [[0.0] * n for _ in range(n)]

    for pos_id in range(n):
        token_id = tokens[pos_id]
        tok_emb = state_dict['wte'][token_id]
        pos_emb = state_dict['wpe'][pos_id]
        x = [t + p for t, p in zip(tok_emb, pos_emb)]
        x = rmsnorm(x)

        for li in range(n_layer):
            x_residual = x
            x = rmsnorm(x)
            q = linear(x, state_dict[f'layer{li}.attn_wq'])
            k = linear(x, state_dict[f'layer{li}.attn_wk'])
            v = linear(x, state_dict[f'layer{li}.attn_wv'])
            snap_keys[li].append(k)
            snap_values[li].append(v)

            x_attn = []
            avg_weights_this_pos = [0.0] * len(snap_keys[li])
            for h in range(n_head):
                hs = h * head_dim
                q_h = q[hs:hs+head_dim]
                k_h = [ki[hs:hs+head_dim] for ki in snap_keys[li]]
                v_h = [vi[hs:hs+head_dim] for vi in snap_values[li]]
                attn_logits = [sum(q_h[j] * k_h[t][j] for j in range(head_dim)) / head_dim**0.5
                               for t in range(len(k_h))]
                attn_weights = softmax(attn_logits)
                for t, w in enumerate(attn_weights):
                    avg_weights_this_pos[t] += w.data / n_head
                head_out = [sum(attn_weights[t] * v_h[t][j] for t in range(len(v_h)))
                            for j in range(head_dim)]
                x_attn.extend(head_out)

            # Store in attention matrix row
            for t, w in enumerate(avg_weights_this_pos):
                attn_mat[pos_id][t] = w

            x = linear(x_attn, state_dict[f'layer{li}.attn_wo'])
            x = [a + b for a, b in zip(x, x_residual)]
            x_residual = x
            x = rmsnorm(x)
            x = linear(x, state_dict[f'layer{li}.mlp_fc1'])
            x = [xi.relu() for xi in x]
            x = linear(x, state_dict[f'layer{li}.mlp_fc2'])
            x = [a + b for a, b in zip(x, x_residual)]

    return attn_mat, n


def capture_generation_steps(max_len=12, top_k=10):
    """
    Run one greedy-ish inference pass and record, at each step:
      (text_so_far, top_k_token_ids_sorted_by_prob, top_k_probs)
    Used to animate the generation process.
    """
    keys_g = [[] for _ in range(n_layer)]
    vals_g  = [[] for _ in range(n_layer)]
    token_id = BOS
    sample = []
    steps = []
    for pos_id in range(max_len):
        logits = gpt(token_id, pos_id, keys_g, vals_g)
        probs_vals = softmax([l / temperature for l in logits])
        probs_float = [p.data for p in probs_vals]

        # top-k indices sorted descending
        sorted_ids = sorted(range(len(probs_float)), key=lambda i: -probs_float[i])[:top_k]
        topk_probs = [probs_float[i] for i in sorted_ids]

        # sample next token
        token_id = random.choices(range(vocab_size), weights=probs_float)[0]

        steps.append((''.join(sample), sorted_ids, topk_probs))

        if token_id == BOS:
            break
        sample.append(uchars[token_id])

    return steps


# ---------------------------------------------------------------------------
# Training — with snapshot collection
# ---------------------------------------------------------------------------

m = [0.0] * len(params)
v = [0.0] * len(params)

loss_history = []
lr_history   = []

# Snapshot buffers
weight_snapshots = []   # list of list[float]  (all param values)
attn_snapshots   = []   # list of 2-D list (n×n attention matrix)
wte_snapshots    = []   # list of list-of-list[float]  (vocab_size × n_embd)
snapshot_steps   = []   # which step each snapshot belongs to

# Decide at which steps to collect snapshots
snap_at = set(int(i * (num_steps - 1) / (N_SNAPSHOTS - 1)) for i in range(N_SNAPSHOTS))
# Always include step 0
snap_at.add(0)

# Pick a fixed doc for consistent attention snapshots across training
snap_doc   = docs[0]
snap_tokens = [BOS] + [uchars.index(ch) for ch in snap_doc] + [BOS]

for step in range(num_steps):

    doc = docs[step % len(docs)]
    tokens = [BOS] + [uchars.index(ch) for ch in doc] + [BOS]
    n = min(block_size, len(tokens) - 1)

    keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]
    losses = []
    for pos_id in range(n):
        token_id, target_id = tokens[pos_id], tokens[pos_id + 1]
        logits = gpt(token_id, pos_id, keys, values)
        probs = softmax(logits)
        loss_t = -probs[target_id].log()
        losses.append(loss_t)
    loss = (1 / n) * sum(losses)

    loss.backward()

    lr_t = learning_rate * (1 - step / num_steps)
    for i, p in enumerate(params):
        m[i] = beta1 * m[i] + (1 - beta1) * p.grad
        v[i] = beta2 * v[i] + (1 - beta2) * p.grad ** 2
        m_hat = m[i] / (1 - beta1 ** (step + 1))
        v_hat = v[i] / (1 - beta2 ** (step + 1))
        p.data -= lr_t * m_hat / (v_hat ** 0.5 + eps_adam)
        p.grad = 0

    loss_history.append(loss.data)
    lr_history.append(lr_t)

    # --- Collect snapshots ---
    if step in snap_at:
        weight_snapshots.append([p.data for p in params])
        attn_mat, _ = capture_attention_matrix(snap_tokens)
        attn_snapshots.append(attn_mat)
        wte_snapshots.append([[v.data for v in row] for row in state_dict['wte']])
        snapshot_steps.append(step + 1)

    print(f"step {step+1:4d} / {num_steps:4d} | loss {loss.data:.4f}", end='\r')

print()  # newline after \r progress

# ---------------------------------------------------------------------------
# Post-training animations
# ---------------------------------------------------------------------------

print("\nRendering animations …")

# 1. Training curves
animate_training_curves(loss_history, lr_history)

# 2. Attention heatmap evolution
#    Pad every snapshot to the same size (block_size × block_size) for consistent frames
snap_size = max(len(m) for m in attn_snapshots)
padded_attn = []
for mat in attn_snapshots:
    padded = [[0.0] * snap_size for _ in range(snap_size)]
    for r, row in enumerate(mat):
        for c, val in enumerate(row):
            padded[r][c] = val
    padded_attn.append(padded)
# Token labels for the snap_doc (truncated to snap_size)
snap_label_chars = (['<BOS>'] + list(snap_doc))[:snap_size]
snap_label_chars += [''] * (snap_size - len(snap_label_chars))
animate_attention_heatmap(padded_attn, snapshot_steps,
                          token_labels=snap_label_chars if snap_size <= 18 else None)

# 3. Weight distribution evolution
animate_weight_distribution(weight_snapshots, snapshot_steps)

# 4. Token embedding PCA
animate_embedding_pca(wte_snapshots, snapshot_steps, uchars)

# ---------------------------------------------------------------------------
# Inference — animated generation
# ---------------------------------------------------------------------------

print("\n--- inference (new, hallucinated names) ---")
for sample_idx in range(5):   # first 5 shown as static text
    keys_i, values_i = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]
    token_id = BOS
    sample = []
    for pos_id in range(block_size):
        logits = gpt(token_id, pos_id, keys_i, values_i)
        probs = softmax([l / temperature for l in logits])
        token_id = random.choices(range(vocab_size), weights=[p.data for p in probs])[0]
        if token_id == BOS:
            break
        sample.append(uchars[token_id])
    print(f"sample {sample_idx+1:2d}: {''.join(sample)}")

# 4. Animated generation for one more sample
print("\nRendering generation animation …")
gen_steps = capture_generation_steps(max_len=block_size, top_k=10)
animate_token_generation(gen_steps, uchars)
