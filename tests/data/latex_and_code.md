## Variable-Mode Factor in PARAFAC

### The decomposition written out

For a 3-D tensor $X_{i,t,v}$ (example × time × variable), a rank-$R$ PARAFAC model is:

$$X_{i,t,v} \approx \sum_{r=1}^{R} \lambda_r \;\underbrace{a_{i,r}}_{\text{sample factor}}\;\underbrace{b_{t,r}}_{\text{time factor}}\;\underbrace{c_{v,r}}_{\text{variable factor}}$$

The **variable-mode factor** $c_{v,r}$ is a vector of length $n_{\text{vars}}$ (here 2: x, y) that answers one question:

> *"When latent pattern $r$ is active, how is it distributed across the measured variables?"*

### Interpretation rules

| $c_{x,r}$ | $c_{y,r}$ | Meaning |
|-----------|-----------|---------|
| $+1$ | $\approx 0$ | Pattern $r$ is a **pure horizontal** movement; y barely responds |
| $\approx 0$ | $+1$ | Pattern $r$ is a **pure vertical** movement |
| $+0.7$ | $+0.7$ | Pattern $r$ moves **diagonally up-right** (x and y coupled, same direction) |
| $+0.7$ | $-0.7$ | Pattern $r$ moves **diagonally down-right** (x and y coupled, opposite) |
| $+1$ | $+1$ | Both variables express the temporal shape $b_{t,r}$ identically (e.g. isotropic expansion) |

- **Magnitude** → how much that variable contributes to this factor.
- **Sign** → whether the pattern moves variables in the *same* or *opposite* direction.
- **Ratio** $c_{y,r}/c_{x,r}$ → the "slope" or coupling angle in variable space.

### Concrete example: writing "fda"

Suppose Factor 2 has $c_{x,2} = 0.9,\; c_{y,2} = 0.1$. Its time-profile $b_{t,2}$ might show a sharp bump around $t \approx 0.4$. Interpretation: *"there is a brief, large horizontal acceleration of the pen at 40 % through the word, with almost no vertical component"* — plausibly the horizontal bar of the letter **f**.

Factor 3 with $c_{x,3} = 0.2,\; c_{y,3} = 0.9$ and a bump at $t \approx 0.7$ would be: *"a strong downward stroke with little lateral movement"* — perhaps the descender of **d**.

### Why this is richer than per-variable PCA

If you ran PCA on x(t) alone and y(t) alone, you'd get two unrelated sets of components. You could *post-hoc* compare them, but nothing guarantees that PC-1-of-x and PC-1-of-y describe the **same** event in the pen stroke. PARAFAC forces a **shared temporal shape** $b_{t,r}$ to appear in *both* variables simultaneously, with the variable-mode vector telling you how strongly each one participates. A factor where $c_x \gg c_y$ is the model telling you: "this temporal event is essentially a 1-D x phenomenon that barely affects y."

### Contrast: growth data (height, weight)

Same logic, different labels:

- $c_{\text{height}} = 0.8,\; c_{\text{weight}} = 0.6$ → "size factor": tall kids are also heavier (positive coupling).
- $c_{\text{height}} = +1,\; c_{\text{weight}} = -0.3$ → "slender factor": growing taller *relative* to weight.

### Practical check in your notebook

```python
print("Factor  x-load  y-load  dominant axis")
for _k in range(hw_Nf):
    _cx, _cy = hw_var_factors[0, _k], hw_var_factors[1, _k]
    _dom = "x" if abs(_cx) > abs(_cy) else "y"
    print(f"F{_k+1}     {_cx:+.3f}   {_cy:+.3f}   → {_dom}-weighted")
```

This gives you a one-line-per-factor summary of whether each latent shape is primarily a horizontal, vertical, or diagonal pen phenomenon.
