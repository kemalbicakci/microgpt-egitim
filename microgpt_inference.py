"""
Eğitilmiş Türkçe GPT modelinden isim üretimi.
Eğitim YOK — model_turkce.json dosyasından ağırlıkları yükler.

Kullanım:
  1. Önce microgpt_turkce.py ile modeli eğit (model_turkce.json üretilir).
  2. Sonra bu dosyayı çalıştır:
       python microgpt_inference.py
  3. İstersen ne kadar isim üretileceğini ve sıcaklığı değiştirebilirsin:
       python microgpt_inference.py --sayi 50 --sicaklik 0.8
"""

import json
import math
import random
import argparse

# ---------------------------------------------------------------------------
# Argümanlar
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('--sayi',     type=int,   default=20,  help='Üretilecek isim sayısı')
parser.add_argument('--sicaklik', type=float, default=0.5, help='Örnekleme sıcaklığı (0.1=kesin, 2.0=yaratıcı)')
parser.add_argument('--model',    type=str,   default='model_turkce.json', help='Model dosyası')
parser.add_argument('--seed',     type=int,   default=None, help='Rastgele tohum (tekrar üretilebilirlik için)')
args = parser.parse_args()

if args.seed is not None:
    random.seed(args.seed)

# ---------------------------------------------------------------------------
# Modeli yükle
# ---------------------------------------------------------------------------

print(f"Model yükleniyor: {args.model}")
with open(args.model, encoding='utf-8') as f:
    ckpt = json.load(f)

uchars     = ckpt['uchars']
n_layer    = ckpt['n_layer']
n_embd     = ckpt['n_embd']
block_size = ckpt['block_size']
n_head     = ckpt['n_head']
vocab_size = ckpt['vocab_size']
head_dim   = n_embd // n_head
BOS        = vocab_size - 1   # son index = BOS

# state_dict: saf float listesi (Value nesnesi yok — eğitim gerekmez)
state_dict = ckpt['state_dict']

print(f"vocab_size : {vocab_size}")
print(f"karakterler: {''.join(uchars)}")
print(f"n_layer={n_layer}  n_embd={n_embd}  n_head={n_head}  block_size={block_size}")

# ---------------------------------------------------------------------------
# İleri geçiş (saf float — autograd YOK)
# ---------------------------------------------------------------------------

def linear(x, w):
    return [sum(wij * xj for wij, xj in zip(wo, x)) for wo in w]

def softmax(logits):
    m = max(logits)
    exps = [math.exp(v - m) for v in logits]
    s = sum(exps)
    return [e / s for e in exps]

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
            attn_logits = [sum(q_h[j] * k_h[t][j] for j in range(head_dim)) / head_dim**0.5
                           for t in range(len(k_h))]
            attn_weights = softmax(attn_logits)
            head_out = [sum(attn_weights[t] * v_h[t][j] for t in range(len(v_h)))
                        for j in range(head_dim)]
            x_attn.extend(head_out)
        x = linear(x_attn, state_dict[f'layer{li}.attn_wo'])
        x = [a + b for a, b in zip(x, x_residual)]
        x_residual = x
        x = rmsnorm(x)
        x = linear(x, state_dict[f'layer{li}.mlp_fc1'])
        x = [max(0.0, xi) for xi in x]   # ReLU — saf float
        x = linear(x, state_dict[f'layer{li}.mlp_fc2'])
        x = [a + b for a, b in zip(x, x_residual)]

    return linear(x, state_dict['lm_head'])

# ---------------------------------------------------------------------------
# İsim üretimi
# ---------------------------------------------------------------------------

print(f"\n--- {args.sayi} hayal edilen Türkçe isim (sıcaklık={args.sicaklik}) ---\n")

for sample_idx in range(args.sayi):
    keys_buf  = [[] for _ in range(n_layer)]
    vals_buf  = [[] for _ in range(n_layer)]
    token_id  = BOS
    sample    = []

    for pos_id in range(block_size):
        logits   = gpt(token_id, pos_id, keys_buf, vals_buf)
        scaled   = [l / args.sicaklik for l in logits]
        probs    = softmax(scaled)
        token_id = random.choices(range(vocab_size), weights=probs)[0]
        if token_id == BOS:
            break
        sample.append(uchars[token_id])

    print(f"  {sample_idx+1:3d}.  {''.join(sample)}")
