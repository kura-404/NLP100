import numpy as np
import matplotlib.pyplot as plt

# パラメータ
h = 0.001        # 時間ステップ
T = 5            # シミュレーション時間（秒）
N = int(T / h)   # ステップ数

# 初期値（任意）
z1 = 1.0         # x(0)
z2 = 0.0         # x'(0)

# 配列初期化
t = np.linspace(0, T, N+1)
x = np.zeros(N+1)
v = np.zeros(N+1)

x[0] = z1
v[0] = z2

# Euler法による更新
for k in range(N):
    z1_new = z1 + h * z2
    z2_new = z2 + h * (-3 * z2 - z1)
    z1, z2 = z1_new, z2_new
    x[k+1] = z1
    v[k+1] = z2

# グラフ表示
plt.figure(figsize=(6, 5))
plt.plot(x, v)
plt.xlabel('$x_k$')
plt.ylabel('$\dot{x}_k$')
plt.title('')
plt.grid(True)
plt.axis('equal')
plt.show()