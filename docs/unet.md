# U-Net A/B experiment

This page describes the experiment that tests whether parallax correction helps a downstream precipitation product. An existing attention U-Net for precipitation type is trained twice:

- **Model A** on uncorrected INSAT-3DR input;
- **Model B** on the same input after PyGeoParallax-IN parallax correction.

Only the input differs. The network, loss, optimiser, seed, labels, pixel mask and train/test split are the same. There are three tasks, so six models in total.

The method is described in `08_manuscript/methods_draft.md` (Section 4.8) and the results in `08_manuscript/results_discussion_draft.md` (Section 6.8, Table 4). For the validation against GPM that motivated the experiment, see [validation.md](validation.md).

## Data

### Patches

The patches come from the research group's U-Net package, `U_net_info/data_trs/BT_patches/`. This folder is not in git (`.gitignore`: "Group U-Net package (models, 2.4 GB of patches)").

- Each patch is a 128 × 128 tile of the INSAT-3DR L1C Mercator grid, stored as `.npz`.
- It holds four brightness-temperature channels, in the order TIR1, TIR2, WV, MIR (`bt`, shape 4 × 128 × 128, in K), the tile offsets `i` and `j`, the pixel `lat` and `lon`, and `precip_type`.
- `precip_type` is the GPM DPR precipitation type of the footprint matched to each pixel's *navigated* position. −99 means no label.
- GPM positions are on the ground, so the labels are already at ground positions. Parallax displaces the input but not the labels.
- The network input is `(bt − 180) / 150`, clipped to [0, 1] (the patches' `bt_norm`).

### Splits

| Split | Folder | Patches | Scenes | Period |
| :--- | :--- | ---: | ---: | :--- |
| Train | `final_patches_train/` | 5,082 | 823 | 2018 and 2021–2023 |
| Test | `final_patches_test/` | 2,197 | 347 | September 2023 and 2024 |

No scene, day or GPM overpass appears in both splits. The group's `final_patches_val/` folder is not used: its patches are part of the test set (see [the no-validation rule](#no-validation-split)).

A scene is one INSAT/GPM pair. Its name is the patch file name before `_patch_`.

### Labels per task

`train_unet_ab.py` remaps `precip_type` for each task, as in the group's notebooks. Pixels not listed are ignored in the loss and in the scores.

| Task | Classes (`precip_type` values) | Class weights |
| :--- | :--- | :--- |
| `fourclass` | Stratiform (1), Deep Conv (3), Shallow Iso (4), Shallow NonIso (5) | 1, 2, 3, 3 |
| `stratconv` | Stratiform (1), Convective (≥ 2) | 1, 2.2 |
| `rain` | No rain (−1), Rain (≥ 1) | 1, 3 |

## Workflow

| Step | Script | Runs on | Output |
| :--- | :--- | :--- | :--- |
| 1. Correct the patches | `scripts/build_unet_patches.py` | the project machine | corrected `.npz` per patch, `manifest.csv` |
| 2. Pack for training | `scripts/pack_unet_dataset.py` | the project machine | `train.npz`, `test.npz` |
| 3. Train six models | `scripts/train_unet_ab.py` (via `run_unet_ab.py`, the Colab notebook or the GPU notebook) | a GPU | `runs/<task>_<model>/` |
| 4. Compare A and B | `scripts/compare_unet_ab.py` | anywhere | `runs/comparison_<task>.json` |
| 5. Plot training loss | `scripts/plot_unet_curves.py` | anywhere | `runs/training_curves.png` |

Steps 1 and 2 need `pygeoparallax` (see [installation.md](installation.md)). Steps 3–5 need only TensorFlow, NumPy and Matplotlib.

### 1. Building the corrected patches

`scripts/build_unet_patches.py` makes the Model B input. It corrects the patches on their own pixel grid, so A and B stay pixel-aligned with the labels.

Processing per scene (all tiles of one INSAT/GPM pair):

1. Mosaic the tiles at their (`i`, `j`) offsets. Fit the grid, which is regular in WGS84 Mercator northing and in longitude, from the tiles' `lat` and `lon`.
2. Compute cloud-top height from TIR1 with the AFGL tropical profile. The patches carry no clear-sky BT, so cloudy means BT < 270 K.
3. Parallax-correct every pixel by ellipsoid ray tracing for INSAT-3DR at 74° E. Resample onto the same pixel grid as in the main pipeline: the highest pixel wins a cell, and gaps of one cell are filled by inverse-distance weighting.
4. Cut the tiles back out.

Cells that receive no corrected pixel stay empty (`fill_flag` 2). Their input is filled with the nearest corrected value, so the network gets a complete image. `ignore` marks them, and their labels are dropped for both A and B.

| Option | Meaning |
| :--- | :--- |
| `--patches` | the `BT_patches` folder (required) |
| `--out` | output folder (required) |
| `-j`, `--jobs` | parallel processes [half the CPU count] |
| `--limit` | process only the first N scenes (testing) |
| `--height-scale` | correct with height-scale × cloud-top height − height-offset [1] |
| `--height-offset KM` | subtract this from the cloud-top height [0 km], e.g. 3 for an effective-height Model C |

Outputs:

- `<out>/train/<patch>.npz` and `<out>/test/<patch>.npz`, each with `bt` (corrected, float32), `fill_flag` (uint8), `shift_km` (float16) and `ignore` (bool);
- `<out>/manifest.csv`, one row per patch: `frac_cloudy`, `shift_median_km`, `shift_p95_km`, `frac_ignore`, `labels_valid`, `labels_ignored`, `frac_tir1_changed_1K`.

Existing outputs are kept, so an interrupted run resumes. A scene that fails is reported and retried on the next run.

```bash
python scripts/build_unet_patches.py --patches U_net_info/data_trs/BT_patches \
    --out D:/Projects/@GeoVision/Insat_data/unet_patches/corrected -j 6
```

From the methods draft: the grid is fitted to within 10⁻⁴ pixel; the correction moves cloud by a median of 4.4 km (about one pixel) and changes TIR1 by more than 1 K on 34 % of pixels; 0.06 % of labelled pixels are dropped as empty.

The same native-grid method is in the library as `correct_native` and `pygeoparallax l1c --native` (see [python_api.md](python_api.md) and [cli.md](cli.md)).

### 2. Packing the dataset

`scripts/pack_unet_dataset.py` packs the original patches (Model A input and labels) and the corrected copies (Model B input) into one file per split.

| Option | Meaning |
| :--- | :--- |
| `--patches` | the `BT_patches` folder (required) |
| `--corrected` | the output folder of `build_unet_patches.py` (required) |
| `--out` | output folder (required) |

It writes `<out>/train.npz` and `<out>/test.npz`, with:

| Array | Shape and type | Content |
| :--- | :--- | :--- |
| `x_A` | (N, 128, 128, 4) float16 | original input, `(bt − 180) / 150` clipped to [0, 1]; channels TIR1, TIR2, WV, MIR |
| `x_B` | (N, 128, 128, 4) float16 | corrected input, same scaling |
| `precip_type` | (N, 128, 128) int8 | GPM label; set to −99 where the corrected field had no data, so A and B are scored on the same pixels |
| `patch`, `scene` | (N,) | names |

float16 keeps the normalised BT to about 0.1 K. In the project the files were 1.4 GB (`train.npz`) and 0.6 GB (`test.npz`).

```bash
python scripts/pack_unet_dataset.py --patches U_net_info/data_trs/BT_patches \
    --corrected D:/Projects/@GeoVision/Insat_data/unet_patches/corrected \
    --out D:/Projects/@GeoVision/Insat_data/unet_colab/data
```

### 3. Training

`scripts/train_unet_ab.py` trains one model for one task. The network, loss, label mappings, optimiser and seed are those of the group's notebooks in `U_net_info/data_trs`:

- an attention U-Net with layer normalisation on 128 × 128 × 4 patches (about 1.1 million parameters);
- class-weighted sparse cross-entropy, with pixels labelled −99 ignored;
- Adam at a learning rate of 10⁻⁶, batch size 1, 100 epochs;
- seed 42 for Python, NumPy and TensorFlow, and a shuffle buffer of 2048 with that seed.

A and B therefore start from the same weights and see the patches in the same order.

| Option | Meaning |
| :--- | :--- |
| `--model` | `A` or `B` (required) |
| `--task` | `fourclass`, `stratconv` or `rain` (required) |
| `--data` | folder with `train.npz` and `test.npz` (required) |
| `--out` | runs folder (required); on Colab, put it on Drive so runs survive disconnects |
| `--epochs` | [100] |
| `--batch` | [1] |
| `--lr` | [1e-6] |
| `--deterministic` | deterministic TensorFlow ops (slower on GPU) |
| `--max-train` | use only the first N training patches (timing tests) |

The run folder is `<out>/<task>_<model>/`. It holds:

| File | Content |
| :--- | :--- |
| `config.json` | the options of the run |
| `checkpoint.keras` | model and optimiser state, written every epoch (via a temporary file, so a disconnect never leaves a broken checkpoint) |
| `history.json` | per epoch: `epoch`, `loss`, `acc` (masked training accuracy), `seconds` |
| `model.keras` | the final model |
| `test_metrics.json` | test accuracy, macro F1, and per-class precision, recall, F1, CSI and `n_true`; the summed confusion matrix |
| `test_confusion_by_patch.npz` | per-patch confusion matrices (`confusion`, rows true, columns predicted), `patches`, `scene` |

Behaviour:

- **Resume.** If `checkpoint.keras` and `history.json` exist, training continues after the last saved epoch.
- **Finished runs.** If `test_metrics.json` exists, the script stops at once. Delete that file to redo the test scoring.
- **Test set.** `test.npz` is read only after the last epoch.
- **Versions.** The script runs with TensorFlow 2.15 (Keras 2) and with TensorFlow / Keras 3 as on Colab. Runs started with an earlier version of the script recorded validation scores in `history.json`; these are dropped on resume.

```bash
python scripts/train_unet_ab.py --model A --task fourclass --data <folder with train.npz, test.npz> --out runs
```

### 4. Batch running

`scripts/run_unet_ab.py` trains all requested tasks and models one after another, each with its own log file. Then it runs `compare_unet_ab.py` for every task whose A and B runs are both finished, and `plot_unet_curves.py`. Finished runs are skipped and interrupted ones resume, so the script can simply be started again. If a training run fails, it stops and names the log.

| Option | Meaning |
| :--- | :--- |
| `--data` | folder with `train.npz` and `test.npz` [`<folder above scripts/>/data`] |
| `--out` | runs folder [`<folder above scripts/>/runs`] |
| `--tasks` | [fourclass stratconv rain] |
| `--models` | [A B] |
| `--epochs` | [100] |
| `--max-train` | first N training patches only (quick test) |

The defaults expect the layout of the GPU bundle (`scripts/` and `data/` side by side; see below). In the repository there is no `data/` folder, so pass `--data` and `--out`. Logs go to `<out>/logs/<task>_<model>.log`.

`scripts/plot_unet_curves.py` plots the training loss of each run, one panel per task, from `<runs>/<task>_<model>/history.json`. Only the training loss is shown, because the test set is not used during training.

| Option | Meaning |
| :--- | :--- |
| `--runs` | runs folder (required) |

Output: `<runs>/training_curves.png`.

### 5. Comparison

`scripts/compare_unet_ab.py` compares Model A and Model B for one task on the test patches.

| Option | Meaning |
| :--- | :--- |
| `--runs` | runs folder (required) |
| `--task` | task name (required) |

- It checks that A and B were scored on the same patches.
- It sums the per-patch confusion matrices per scene.
- **Scene bootstrap:** 2,000 times, it resamples the 347 test scenes with replacement (seed 2026), keeping all patches of a scene together, and recomputes every score for A and B on the same resample. This gives the distribution of B − A.
- Reported: B − A, its 95 % percentile interval, and a two-sided p-value, `2 × min(P(d ≤ 0), P(d ≥ 0))` from the bootstrap distribution.
- Scores: accuracy, macro F1, and per-class F1 and CSI, where CSI = TP / (TP + FP + FN).

Output: `<runs>/comparison_<task>.json` and a printed table. The number of resamples (2,000) and the seed are fixed in the script.

## Running the training

Training is slow on a CPU: each model is 100 epochs × 5,082 steps (batch size 1), about 37 h per model on a 6-core laptop CPU and a few hours on a modern GPU. The project used two routes.

### Colab

`colab/unet_ab_colab.ipynb` runs the training on Google Colab.

1. Make a folder `unet_colab` with `data/train.npz`, `data/test.npz`, `scripts/train_unet_ab.py`, `scripts/compare_unet_ab.py` and the notebook. Upload it to the top of Google Drive (`MyDrive/unet_colab`).
2. Open the notebook in Colab and choose **Runtime → Change runtime type → GPU** (a T4 is enough).
3. Run the cells from the top:
   - mount Drive, check the GPU, and copy the two `.npz` files to the Colab disk (`/content/data`), which is faster than reading from Drive;
   - **quick test:** one epoch of Model B, four-class task, on 50 patches into `/content/smoke`;
   - **train:** the six runs in turn, four-class first, written to `MyDrive/unet_colab/runs/`;
   - **compare:** `compare_unet_ab.py` for every task with both runs finished;
   - **curves:** the training loss, saved as `runs/training_curves.png`.
4. When Colab disconnects, reconnect and run all cells again. Training resumes from the last saved epoch and finished runs are skipped.

### GPU machine

For a machine with an NVIDIA GPU, the project assembled a folder `unet_gpu/` outside the repository (at `D:/Projects/@GeoVision/Insat_data/unet_gpu`). It is not in git. To rebuild it, copy the four U-Net scripts and the packed data:

```text
unet_gpu/
  data/train.npz, data/test.npz      (from pack_unet_dataset.py)
  scripts/train_unet_ab.py, run_unet_ab.py, compare_unet_ab.py, plot_unet_curves.py
  requirements.txt, environment.yml
  setup.sh, run_all.sh
  unet_ab_gpu.ipynb
```

Requirements: Linux with an NVIDIA GPU and driver (`nvidia-smi` must work), Python 3.9–3.11 for TensorFlow 2.15, about 4 GB of free disk and 8 GB of RAM or more. TensorFlow has no native GPU support on Windows after version 2.10, which is too old for these scripts; on Windows, use WSL2.

`requirements.txt`:

```text
tensorflow[and-cuda]==2.15.1
numpy<2
matplotlib
```

`tensorflow[and-cuda]` installs the CUDA and cuDNN libraries itself; only the NVIDIA driver is needed. `environment.yml` is the conda equivalent (environment `unet-ab`, Python 3.11).

#### From a terminal

`setup.sh` creates `.venv`, installs `requirements.txt` and fails if TensorFlow sees no GPU. `run_all.sh` sets `CUDA_VISIBLE_DEVICES` from `GPU` (default 0) and starts `scripts/run_unet_ab.py` in the background with `nohup`, passing on its arguments. The log is `runs/logs/run_all.log`.

```bash
cd unet_gpu
bash setup.sh                 # or: PYTHON=python3.11 bash setup.sh
bash run_all.sh               # all six models on GPU 0
tail -f runs/logs/run_all.log
tail -f runs/logs/fourclass_A.log
```

Variants:

```bash
GPU=1 bash run_all.sh                                # another GPU
bash run_all.sh --tasks fourclass --models A B       # selected models
GPU=0 bash run_all.sh --tasks fourclass              # one task per GPU, started separately
GPU=1 bash run_all.sh --tasks stratconv
.venv/bin/python scripts/run_unet_ab.py --out runs_test --tasks rain --epochs 1 --max-train 8   # check, about 1 min
```

Do not start the same task twice at once. Each start of `run_all.sh` writes `runs/logs/run_all.log` afresh, so with two parallel starts that file holds only the last one; the per-model logs are separate. If the machine stops, run `bash run_all.sh` again.

With conda instead of the venv:

```bash
conda env create -f environment.yml
conda activate unet-ab
python scripts/run_unet_ab.py
```

#### From Jupyter

`unet_ab_gpu.ipynb` runs the same steps in an existing environment (in the project, `td_gpu`). Install the packages there if needed:

```bash
pip install "tensorflow[and-cuda]==2.15.1" "numpy<2" matplotlib
```

Start Jupyter from that environment and open the notebook from inside `unet_gpu/`; it finds `data/` and `scripts/` next to itself. The cells:

1. set `GPU` (`CUDA_VISIBLE_DEVICES`) and check the files;
2. check that TensorFlow lists a GPU (if it shows `[]`, stop: training would run on the CPU);
3. quick test: one epoch on 50 patches into `runs_test/`;
4. train the six models, skipping finished ones; output is shown in the notebook and appended to `runs/logs/<task>_<model>.log`;
5. compare A and B;
6. plot the training curves.

If a cell stops, run it again; training resumes.

### What to bring back

Copy the `runs/` folder back. Per run keep `test_metrics.json`, `test_confusion_by_patch.npz`, `history.json` and `model.keras`, plus `comparison_<task>.json` and `training_curves.png`. The `checkpoint.keras` files can be left out. The project's comparison files are in `D:/Projects/@GeoVision/Insat_data/U_net_results/`.

## No validation split

The experiment uses two splits only: train for training, test for the final scores.

- **Why.** The group's validation patches (`final_patches_val/`) are part of the test set. Scoring them during training, for a learning curve, early stopping or model selection, would let test data influence the model.
- **What this means.** There is no early stopping and no model selection. Both models train for exactly 100 epochs. Only the training loss is recorded per epoch. The test set is read only after training has finished.
- **Why it is acceptable here.** Nothing is tuned: the network and its settings are fixed by the group's notebooks. The question is only whether the same model does better with corrected input, and A and B are treated identically.

`build_unet_patches.py` corrects only the train and test folders, and `pack_unet_dataset.py` packs only those two.

## Results

From `08_manuscript/results_discussion_draft.md`, Section 6.8. Test set: 2,197 patches from 347 scenes. B − A is given with its 95 % interval from the paired scene bootstrap; p is two-sided.

| Task | Score | A | B | B − A | 95 % interval | p |
| :--- | :--- | ---: | ---: | ---: | :--- | ---: |
| Four classes | Accuracy | 0.675 | 0.674 | −0.0004 | −0.0011 to +0.0004 | 0.290 |
| | Macro F1 | 0.421 | 0.420 | −0.0012 | −0.0024 to 0.0000 | 0.050 |
| | CSI stratiform | 0.700 | 0.701 | +0.0003 | −0.0004 to +0.0012 | 0.431 |
| | CSI deep convective | 0.041 | 0.038 | −0.0030 | −0.0055 to −0.0007 | 0.008 |
| | CSI shallow isolated | 0.265 | 0.264 | −0.0006 | −0.0019 to +0.0007 | 0.388 |
| | CSI shallow non-isolated | 0.221 | 0.222 | +0.0010 | −0.0001 to +0.0020 | 0.070 |
| Stratiform / convective | Accuracy | 0.709 | 0.709 | +0.0000 | −0.0012 to +0.0013 | 0.920 |
| | Macro F1 | 0.686 | 0.685 | −0.0004 | −0.0014 to +0.0007 | 0.494 |
| | CSI stratiform | 0.628 | 0.628 | +0.0006 | −0.0010 to +0.0022 | 0.481 |
| | CSI convective | 0.429 | 0.428 | −0.0012 | −0.0023 to −0.0001 | 0.039 |
| Rain / no rain | Accuracy | 0.863 | 0.863 | +0.0001 | −0.0002 to +0.0005 | 0.412 |
| | Macro F1 | 0.718 | 0.717 | −0.0002 | −0.0007 to +0.0002 | 0.329 |
| | CSI rain | 0.347 | 0.346 | −0.0005 | −0.0012 to +0.0001 | 0.120 |

**Correcting the input does not improve the classifier.**

- In all three tasks, accuracy and macro F1 of Model B are within 0.0012 of Model A.
- Only the convective classes change consistently, and they get slightly worse: deep convective CSI falls from 0.041 to 0.038 (p = 0.008), and convective CSI in the stratiform/convective task from 0.429 to 0.428 (p = 0.039).
- Stratiform scores and rain detection do not change significantly.

Qualifications:

- **Size.** The changes are small. The largest relative change, 7 % of deep convective CSI, is in a class the network barely detects with either input (F1 0.08).
- **Multiple tests.** With 22 scores tested, one or two p-values below 0.05 are expected by chance. None passes a Bonferroni correction (p < 0.002).
- **One run per model.** Each model was trained once. Run-to-run variation, for example from non-deterministic GPU operations, was not measured and may be of similar size.

The pattern is consistent with the GPM validation: uncorrected cold cores already sit on the GPM convective cells (see [validation.md](validation.md#what-the-results-show)), so moving them by the full infrared parallax pulls the cold signal away from the convective labels.

### Open points

From the revision notes of the results draft:

- The training-loss histories (`history.json`) were not returned with the results.
- Retraining each model with two or three more seeds would separate the A/B difference from run-to-run variation (`--deterministic` reduces GPU non-determinism).
- A Model C corrected with an effective height (lower than the infrared top) would test whether a lower height suits precipitation better. The library supports this (`effective_height`, `--height-offset`); `build_unet_patches.py` does not yet have such an option.

## See also

- [validation.md](validation.md): the GPM validation.
- [concepts.md](concepts.md): parallax, cloud-top height and resampling.
- [development.md](development.md): repository structure and tests.
