# Stage 03: Model Training (Kaggle & Local GPU)

This directory contains resources to train and export the **YOLOv8 Nano** black balloon detector.

---

## 📁 Files

- **`train_balloon_detector.ipynb`** — Complete Jupyter Notebook configured for Kaggle GPU (T4 / P100) or Google Colab.
- **`train_kaggle_api.py`** — CLI tool to automate dataset upload, kernel dispatch, and weight download using the official Kaggle API.
- **`03-model-training.md`** — Engineering rules, evaluation targets (Precision $\ge 0.97$), and failure mode criteria.

---

## 🚀 Method 1: Train in Kaggle Web UI (Recommended & Visual)

1. **Upload Dataset**:
   - Go to [kaggle.com/datasets](https://www.kaggle.com/datasets) $\rightarrow$ **New Dataset**.
   - Upload `agesis_balloon_dataset_kaggle.zip` (located in project root).
   - Name it `agesis-balloon-dataset` and click **Create**.

2. **Create Notebook**:
   - In Kaggle, go to **Code** $\rightarrow$ **New Notebook**.
   - Click **File** $\rightarrow$ **Upload Notebook** and select `train_balloon_detector.ipynb`.
   - In the right-hand panel:
     - Under **Settings**, set **Accelerator** to **GPU T4 x2** (or P100).
     - Under **Input**, click **+ Add Input** and add your `agesis-balloon-dataset`.

3. **Run All Cells**:
   - Trains for 80 epochs at `imgsz=320`.
   - Generates PR curve, confusion matrix, and held-out test split evaluation.
   - Automatically exports `best.pt` and `best.onnx` into `agesis_model_weights.zip`.

4. **Download Weights**:
   - Download `agesis_model_weights.zip` from the right-hand **Output** panel.

---

## ⚡ Method 2: Fully Automated via Kaggle API CLI

If you have a Kaggle API token (`kaggle.json` from [kaggle.com/settings](https://www.kaggle.com/settings)):

```powershell
# 1. Store your credentials:
python "Model Training/train_kaggle_api.py" --setup --username YOUR_USERNAME --key YOUR_API_KEY

# 2. Upload dataset:
python "Model Training/train_kaggle_api.py" --upload-dataset

# 3. Submit GPU training job:
python "Model Training/train_kaggle_api.py" --train

# 4. Check status while it trains:
python "Model Training/train_kaggle_api.py" --status

# 5. Download trained weights (best.pt, best.onnx) to local disk:
python "Model Training/train_kaggle_api.py" --download-output
```
All downloaded weights will be saved to `Model Training/trained_weights/` ready for Stage 04 Laptop Inference!
