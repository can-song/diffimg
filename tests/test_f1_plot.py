import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from sklearn.metrics import f1_score

# Generate some random data for precision and recall
precision_values = np.linspace(0, 1, 100)
recall_values = np.linspace(0, 1, 100)
precision, recall = np.meshgrid(precision_values, recall_values)

# Calculate the F1 score for each precision-recall pair
betas = list(range(1, 6, 2))
betas = list(range(1, 4, 1))
betas =  [1, 2, 3]
fig = plt.figure()
fig.subplots_adjust(hspace=0.4)
vmax = 0.02
for i in range(2):
    beta = betas[i]
    f1_scores = (
        (1 + beta**2) * precision * recall / (beta**2 * precision + recall + 1e-8)
    )

    # Create the 3D plot
    # ax = fig.add_subplot(111, projection='3d')
    # ax.plot_surface(precision, recall, f1_scores, cmap='viridis')
    ax = fig.add_subplot(2, 3, i * 3 + 1)
    im = ax.matshow(f1_scores, cmap="viridis")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    # ax.set_xticks(precision_values)
    # ax.set_yticks(recall_values)
    # ax.plot(precision_values, recall_values, f1_scores)
    ax.set_xlabel("Precision")
    ax.set_ylabel("Recall")
    ax.set_title("F1 score for beta = {}".format(beta))

    # ax.set_zlabel('F1 score')

    # show gradient map of f1 score
    f1_grads = np.gradient(f1_scores)
    # f1_grads = [np.log(f) for f in f1_grads]
    ax = fig.add_subplot(2, 3, i * 3 + 2)
    # f1_grad = np.sqrt(f1_grads[0]**2 + f1_grads[1]**2)
    # f1_grad = np.log(f1_grad)
    im = ax.matshow(f1_grads[0], cmap="viridis")
    im.set_clim(vmax=vmax)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("y gradient for beta = {}".format(beta))

    ax = fig.add_subplot(2, 3, i * 3 + 3)
    im = ax.matshow(f1_grads[1], cmap="viridis")
    im.set_clim(vmax=vmax)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("x gradient for beta = {}".format(beta))


plt.show()
