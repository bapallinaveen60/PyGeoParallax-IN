"""Train the precipitation-type U-Net on uncorrected (Model A) or parallax-corrected (Model B) INSAT input.

The network, loss, label mappings, optimiser and seed are those of the U-Net
notebooks in ``U_net_info/data_trs``:

- attention U-Net with LayerNormalization on 128 x 128 x 4 patches;
- inputs TIR1, TIR2, WV, MIR as ``(bt - 180) / 150`` clipped to [0, 1];
- Adam at 1e-6, class-weighted cross-entropy, and pixels without a GPM label
  ignored.

Model A and Model B see the same patches, labels, pixel mask, initial weights
and shuffle order, so only the input differs:

- A uses ``x_A``, the original patches;
- B uses ``x_B``, the parallax-corrected copies from ``build_unet_patches.py``.

Both come from the packed files written by ``pack_unet_dataset.py``. Labels are
already dropped there in both, where the corrected field had no data.

Tasks (labels from the patches' ``precip_type``):

- ``fourclass``: stratiform / deep convective / shallow isolated / shallow non-isolated (1, 3, 4, 5);
- ``stratconv``: stratiform (1) / convective (>= 2);
- ``rain``: no rain (-1) / rain (>= 1).

Splits are the notebooks' folders: train for training; test for the final
scores. The validation patches are a subset of test and are scored every
``--val-every`` epochs for the learning curve only. Nothing is selected on
them.

A checkpoint is written every epoch, so an interrupted run resumes.

Outputs in ``<out>/<task>_<model>/``:

- ``model.keras``;
- ``history.json``;
- ``test_metrics.json``;
- ``test_confusion_by_patch.npz``: per-patch confusion matrices, for the paired
  scene bootstrap in ``compare_unet_ab.py``.

Runs with TensorFlow 2.15 (Keras 2) or the TensorFlow / Keras 3 on Colab.

Usage:
    python scripts/train_unet_ab.py --model A --task fourclass --data <folder with train.npz, test.npz> \
        --out <runs folder> [--epochs 100] [--batch 1] [--lr 1e-6]
"""

from __future__ import annotations

import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import argparse  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import tensorflow as tf  # noqa: E402
from tensorflow.keras import layers, models  # noqa: E402

IGNORE_LABEL = -99
SEED = 42
TASKS = {
    "fourclass": (["Stratiform", "Deep Conv", "Shallow Iso", "Shallow NonIso"], [1.0, 2.0, 3.0, 3.0]),
    "stratconv": (["Stratiform", "Convective"], [1.0, 2.2]),
    "rain": (["No rain", "Rain"], [1.0, 3.0]),
}


def remap(y, task):
    """Notebook label mappings (to_multiclass, to_strat_conv, to_binary)."""
    ym = np.full_like(y, IGNORE_LABEL)
    if task == "fourclass":
        ym[y == 1], ym[y == 3], ym[y == 4], ym[y == 5] = 0, 1, 2, 3
    elif task == "stratconv":
        ym[y == 1], ym[y >= 2] = 0, 1
    else:
        ym[y >= 1], ym[y == -1] = 1, 0
    return ym


def load_split(data, split, model, task):
    """Inputs (N, 128, 128, 4) float16, labels (N, 128, 128) int32 and the packed file, from ``pack_unet_dataset.py``."""
    d = np.load(Path(data) / f"{split}.npz")
    return d[f"x_{model}"], remap(d["precip_type"].astype(np.int32), task), d


# ---------------------------------------------------------------- notebook model, unchanged
def attention_gate(g, s, inter_channels):
    Wg = layers.Conv2D(inter_channels, 1, padding="same")(g)
    Wg = layers.LayerNormalization()(Wg)
    Ws = layers.Conv2D(inter_channels, 1, padding="same")(s)
    Ws = layers.LayerNormalization()(Ws)
    out = layers.Activation("relu")(layers.Add()([Wg, Ws]))
    psi = layers.Conv2D(1, 1, padding="same")(out)
    psi = layers.Activation("sigmoid")(psi)
    return layers.Multiply()([s, psi])


def unet_model(input_shape=(128, 128, 4), num_classes=4):
    inputs = layers.Input(shape=input_shape)

    c1 = layers.Conv2D(32, (11, 11), padding="same", kernel_initializer="he_normal")(inputs)
    c1 = layers.LayerNormalization()(c1)
    c1 = layers.Activation("relu")(c1)
    c1_res = c1
    c1 = layers.Conv2D(32, (7, 7), padding="same", kernel_initializer="he_normal")(c1)
    c1 = layers.LayerNormalization()(c1)
    c1 = layers.Activation("relu")(c1)
    c1_plain = layers.Conv2D(32, (3, 3), padding="same")(c1)
    c1_plain = layers.LayerNormalization()(c1_plain)
    c1 = layers.Add()([c1, c1_res, c1_plain])
    c1 = layers.Activation("relu")(c1)
    c1 = layers.SpatialDropout2D(0.15)(c1)
    p1 = layers.MaxPooling2D(2)(c1)

    c2 = layers.Conv2D(64, (7, 7), padding="same", kernel_initializer="he_normal")(p1)
    c2 = layers.LayerNormalization()(c2)
    c2 = layers.Activation("relu")(c2)
    c2_res = c2
    c2 = layers.Conv2D(64, (5, 5), padding="same", kernel_initializer="he_normal")(c2)
    c2 = layers.LayerNormalization()(c2)
    c2 = layers.Activation("relu")(c2)
    c2 = layers.Add()([c2, c2_res])
    c2 = layers.Activation("relu")(c2)
    c2 = layers.SpatialDropout2D(0.15)(c2)
    p2 = layers.MaxPooling2D(2)(c2)

    c3 = layers.Conv2D(128, (5, 5), padding="same", kernel_initializer="he_normal")(p2)
    c3 = layers.LayerNormalization()(c3)
    c3 = layers.Activation("relu")(c3)
    c3_res = c3
    d1 = layers.LayerNormalization()(layers.Conv2D(32, (3, 3), padding="same")(c3))
    d2 = layers.LayerNormalization()(layers.Conv2D(32, (3, 3), padding="same")(c3))
    d3 = layers.LayerNormalization()(layers.Conv2D(32, (3, 3), padding="same")(c3))
    c3 = layers.Concatenate()([d1, d2, d3])
    c3 = layers.Conv2D(128, (1, 1), padding="same")(c3)
    c3 = layers.LayerNormalization()(c3)
    c3 = layers.Add()([c3, c3_res])
    c3 = layers.Activation("relu")(c3)
    c3 = layers.SpatialDropout2D(0.2)(c3)
    p3 = layers.MaxPooling2D(2)(c3)

    b = layers.SeparableConv2D(256, (3, 3), padding="same")(p3)
    b = layers.LayerNormalization()(b)
    b = layers.Activation("relu")(b)
    b = layers.Dropout(0.2)(b)
    b = layers.SeparableConv2D(256, (3, 3), padding="same")(b)
    b = layers.LayerNormalization()(b)
    b = layers.Activation("relu")(b)

    u3 = layers.Conv2DTranspose(128, (3, 3), strides=2, padding="same")(b)
    u3 = layers.Concatenate()([u3, attention_gate(u3, c3, 64)])
    u2 = layers.Conv2DTranspose(64, (2, 2), strides=2, padding="same")(u3)
    u2 = layers.Concatenate()([u2, attention_gate(u2, c2, 32)])
    u1 = layers.Conv2DTranspose(32, (2, 2), strides=2, padding="same")(u2)
    u1 = layers.Concatenate()([u1, attention_gate(u1, c1, 16)])
    outputs = layers.Conv2D(num_classes, (1, 1), activation="softmax")(u1)
    return models.Model(inputs, outputs)


def weighted_loss(weights):
    w = tf.constant(weights, dtype=tf.float32)

    def loss(y_true, y_pred):
        y_true = tf.cast(y_true, tf.int32)
        valid = tf.not_equal(y_true, IGNORE_LABEL)
        y_true_safe = tf.where(valid, y_true, 0)
        ce = tf.keras.losses.sparse_categorical_crossentropy(y_true_safe, y_pred)
        ce = ce * tf.gather(w, y_true_safe)
        ce = tf.where(valid, ce, 0.0)
        return tf.reduce_sum(ce) / (tf.reduce_sum(tf.cast(valid, tf.float32)) + 1e-6)

    return loss


def masked_accuracy(y_true, y_pred):
    # Same value as the notebook's boolean_mask version, but static shapes (XLA / Keras 3 safe).
    y_true = tf.cast(y_true, tf.int32)
    mask = tf.cast(tf.not_equal(y_true, IGNORE_LABEL), tf.float32)
    y_pred = tf.cast(tf.argmax(y_pred, axis=-1), tf.int32)
    hit = tf.cast(tf.equal(y_true, y_pred), tf.float32) * mask
    return tf.reduce_sum(hit) / tf.maximum(tf.reduce_sum(mask), 1.0)
# ----------------------------------------------------------------


def confusion_by_patch(model, X, Y, n_classes, batch=8):
    """(N, C, C) confusion matrices, rows true, columns predicted."""
    out = np.zeros((len(X), n_classes, n_classes), np.int64)
    for s in range(0, len(X), batch):
        pred = np.argmax(model.predict(X[s:s + batch].astype(np.float32), verbose=0), -1)
        for k, (y, p) in enumerate(zip(Y[s:s + batch], pred)):
            m = y != IGNORE_LABEL
            out[s + k] = np.bincount(y[m] * n_classes + p[m], minlength=n_classes ** 2).reshape(n_classes, n_classes)
    return out


def scores(cm, classes):
    """Accuracy and per-class precision, recall, F1 and CSI from a summed confusion matrix."""
    tp = np.diag(cm).astype(float)
    fp, fn = cm.sum(0) - tp, cm.sum(1) - tp
    with np.errstate(invalid="ignore", divide="ignore"):
        prec, rec, csi = tp / (tp + fp), tp / (tp + fn), tp / (tp + fp + fn)
        f1 = 2 * prec * rec / (prec + rec)
    per = {c: {"precision": prec[k], "recall": rec[k], "f1": f1[k], "csi": csi[k], "n_true": int(cm[k].sum())}
           for k, c in enumerate(classes)}
    return {"accuracy": float(tp.sum() / cm.sum()), "macro_f1": float(np.nanmean(f1)),
            "per_class": {c: {k: float(v) if k != "n_true" else v for k, v in d.items()} for c, d in per.items()},
            "confusion": cm.tolist()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--model", required=True, choices=["A", "B"])
    ap.add_argument("--task", required=True, choices=list(TASKS))
    ap.add_argument("--data", required=True, help="folder with train.npz and test.npz (pack_unet_dataset.py)")
    ap.add_argument("--out", required=True, help="runs folder; on Colab put it on Drive so runs survive disconnects")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--lr", type=float, default=1e-6)
    ap.add_argument("--val-every", type=int, default=5)
    ap.add_argument("--deterministic", action="store_true", help="deterministic ops (slower on GPU)")
    ap.add_argument("--max-train", type=int, help="use only the first N training patches (timing tests)")
    args = ap.parse_args(argv)

    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)
    if args.deterministic:
        tf.config.experimental.enable_op_determinism()
    print(f"TensorFlow {tf.__version__}, devices {[d.name for d in tf.config.list_physical_devices()]}", flush=True)

    classes, weights = TASKS[args.task]
    run = Path(args.out) / f"{args.task}_{args.model}"
    run.mkdir(parents=True, exist_ok=True)
    (run / "config.json").write_text(json.dumps(vars(args), indent=2))
    if (run / "test_metrics.json").exists():
        print(f"{run} is finished; delete test_metrics.json to redo the test scoring", flush=True)
        return

    X_tr, Y_tr, _ = load_split(args.data, "train", args.model, args.task)
    X_tr, Y_tr = X_tr[:args.max_train], Y_tr[:args.max_train]
    X_te, Y_te, te = load_split(args.data, "test", args.model, args.task)
    val = te["in_val"]
    print(f"{args.task} model {args.model}: {len(X_tr)} train, {int(val.sum())} val, {len(X_te)} test patches", flush=True)

    to_float = lambda x, y: (tf.cast(x, tf.float32), y)  # noqa: E731
    train_ds = (tf.data.Dataset.from_tensor_slices((X_tr, Y_tr))
                .shuffle(2048, seed=SEED, reshuffle_each_iteration=True)
                .batch(args.batch).map(to_float).prefetch(tf.data.AUTOTUNE))
    val_ds = tf.data.Dataset.from_tensor_slices((X_te[val], Y_te[val])).batch(8).map(to_float)

    ckpt, hist_path = run / "checkpoint.keras", run / "history.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else {"epoch": [], "loss": [], "acc": [], "val": [], "seconds": []}
    model = unet_model(num_classes=len(classes))
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=args.lr), loss=weighted_loss(weights),
                  metrics=[masked_accuracy])
    if ckpt.exists() and history["epoch"]:
        try:  # weights and optimizer state
            model = tf.keras.models.load_model(ckpt, custom_objects={"loss": weighted_loss(weights),
                                                                     "masked_accuracy": masked_accuracy})
        except Exception as e:  # noqa: BLE001
            print(f"full checkpoint load failed ({e}); restoring weights only", flush=True)
            model.load_weights(ckpt)
        print(f"resuming after epoch {history['epoch'][-1]}", flush=True)
    start = history["epoch"][-1] if history["epoch"] else 0

    for epoch in range(start + 1, args.epochs + 1):
        t0 = time.perf_counter()
        h = model.fit(train_ds, epochs=epoch, initial_epoch=epoch - 1, verbose=2)
        v = None
        if epoch % args.val_every == 0 or epoch == args.epochs:
            v = [float(x) for x in model.evaluate(val_ds, verbose=0)]
        history["epoch"].append(epoch)
        history["loss"].append(float(h.history["loss"][-1]))
        history["acc"].append(float(h.history["masked_accuracy"][-1]))
        history["val"].append(v)
        history["seconds"].append(time.perf_counter() - t0)
        tmp = run / "checkpoint_tmp.keras"  # write then rename, so a disconnect never leaves a broken checkpoint
        model.save(tmp)
        tmp.replace(ckpt)
        hist_path.write_text(json.dumps(history))
        print(f"epoch {epoch}: loss {history['loss'][-1]:.4f} acc {history['acc'][-1]:.4f} "
              f"val [loss, acc] {v} ({history['seconds'][-1]:.0f} s)", flush=True)

    model.save(run / "model.keras")
    del X_tr, Y_tr, train_ds
    cm = confusion_by_patch(model, X_te, Y_te, len(classes))
    np.savez_compressed(run / "test_confusion_by_patch.npz", confusion=cm, patches=te["patch"],
                        scene=te["scene"], in_val=val)
    metrics = {"task": args.task, "model": args.model, "test_patches": len(X_te), **scores(cm.sum(0), classes)}
    (run / "test_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({k: metrics[k] for k in ("accuracy", "macro_f1")}), flush=True)


if __name__ == "__main__":
    main()
