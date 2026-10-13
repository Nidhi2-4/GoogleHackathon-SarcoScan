# Machine learning

Owner: Pravesh. Last updated: 2026-10-04.

Status: four models are connected to the app. Two DenseNet121 classifiers read the X-ray (osteoporosis, KL grade) through `ml/predict.py`. Two models read body measurements and medical history (low muscle mass, bone loss) through `ml/tabular.py`. The training scripts are in `ml/training/` and `ml/predict.py` uses the same preprocessing (pad to square, 224 px, mirror-averaged). Neither model has an external test. The scripts include exact and near-duplicate checks and keep both knees of one image in the same split; the counts they found are not recorded here. Muscle ratios, overlay, and Grad-CAM are not built.

## What the product needs from ML

| Output | In the spec | Approach | Training data | Status |
|---|---|---|---|---|
| Osteoporosis risk: probability and tier (low, moderate, high) | Must-have 10 | Image classifier (fine-tuned CNN) on the knee X-ray | `osteoporosis/main`, tested on `osteoporosis/external` | done (internal test only) |
| KL osteoarthritis grade, 0 to 4 | Should-have, bonus only | Image classifier (fine-tuned CNN) | `kl_grade/main`, tested on `external` and `cgmh` | done (internal test only) |
| Muscle proxy: four soft-tissue-to-bone ratios, with an overlay | Must-have 5 and 6 | Image processing in `ml/muscle.py`: bone edges, joint line, widths at two levels. No trained model | none needed | done as an estimate; shown, not used in the stage |
| Sarcopenia stage (none, possible, probable, severe) | Must-have 9 | AWGS rules on grip and chair stand, with low muscle mass from a model on body measurements | NHANES 2011 to 2014 (US) | done; muscle evidence is not from the X-ray yet |
| X-ray quality check | Must-have 4 | Simple rules first | none needed | planned |
| Heatmap (Grad-CAM) | Must-have 11 | `pytorch-grad-cam` on the osteoporosis CNN | none needed | planned |

Order of work: osteoporosis first (it is a must-have and has data), then the muscle ratios and sarcopenia rules (the product's headline), then KL grade (bonus).

## Datasets

All five are from Kaggle. Unzip each into its folder under `ml/data/`. Git ignores the contents.

| Task | Folder | Dataset | Download | Use |
|---|---|---|---|---|
| Osteoporosis | `osteoporosis/main/` | [mohamedgobara/multi-class-knee-osteoporosis-x-ray-dataset](https://www.kaggle.com/datasets/mohamedgobara/multi-class-knee-osteoporosis-x-ray-dataset) | 1.17 GB | Train and validate |
| Osteoporosis | `osteoporosis/external/` | [majesticd/osteoporosis-x-ray](https://www.kaggle.com/datasets/majesticd/osteoporosis-x-ray) | 182 MB | Test only |
| KL grade | `kl_grade/main/` | [shashwatwork/knee-osteoarthritis-dataset-with-severity](https://www.kaggle.com/datasets/shashwatwork/knee-osteoarthritis-dataset-with-severity) | 204 MB | Train and validate |
| KL grade | `kl_grade/external/` | [peymannejat/osail-knee-osteoarthritis-kl-scoring-dataset](https://www.kaggle.com/datasets/peymannejat/osail-knee-osteoarthritis-kl-scoring-dataset) | 402 MB | Test only |
| KL grade | `kl_grade/cgmh/` | [tommyngx/cgmh-oa](https://www.kaggle.com/datasets/tommyngx/cgmh-oa) | 582 MB | Test only (hospital data, doctor-graded) |

### What the public pages say

Checked on 2026-10-04 from each dataset's published metadata. Nobody has opened the image folders for this file yet.

- **Osteoporosis main:** JPG and PNG images. The description says it is the data of the paper "Knee Osteoporosis Diagnosis Based on Deep Learning" (DOI 10.1007/s44196-024-00615-4) and was "gathered from various sources". It gives no image count.
- **Osteoporosis external:** JPG images plus one Excel file. No description.
- **KL main:** PNG images, organised from the Osteoarthritis Initiative, originally published by Chen (2018) on Mendeley. Made for knee joint detection and KL grading.
- **KL external (OSAIL):** PNG images. No description.
- **CGMH:** PNG images from Chang Gung Memorial Hospital, KL graded.

### The likely common source

The [Knee X-ray Osteoporosis Database](https://data.mendeley.com/datasets/fxjm8fb6mw/2) on Mendeley (Wani and Arora, 2021). Its README states:

- 240 subjects and 239 X-ray images: 36 normal, 154 osteopenia, 49 osteoporosis.
- An Excel sheet with each participant's clinical details and a T-score "obtained from Quantitative Ultrasound System".
- For research use only.

The external osteoporosis set is almost certainly a copy of this database. Both hold JPG images plus an Excel sheet, and the archives are the same size: the Mendeley zip is 190,531,319 bytes, which is 181.7 MiB, the figure Kaggle shows for the external set. If so, the external test set has only 239 images.

The main set was gathered from several sources and probably includes this database as well. Treat overlap between `main` and `external` as likely until the check below says otherwise.

### Things to check before trusting any number

1. **Overlap between `main` and `external`.** If the external set contains images that are also in the training set, the test score will look far better than it is. Run this once per task:

   ```python
   import hashlib, pathlib

   def hashes(folder):
       out = {}
       for p in pathlib.Path(folder).rglob("*"):
           if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
               out.setdefault(hashlib.md5(p.read_bytes()).hexdigest(), []).append(p)
       return out

   main = hashes("ml/data/osteoporosis/main")
   ext = hashes("ml/data/osteoporosis/external")
   print(len(set(main) & set(ext)), "files appear in both sets")
   ```

   This finds exact copies only. Resized or augmented copies need a perceptual hash (the `imagehash` package). Remove every overlapping image from the test set, and write the count in the Results notes.

2. **Augmented copies inside one dataset.** If file names show that one original was turned into several variants, keep all variants of one original on the same side of the train/validation split.

3. **Where the labels came from.** In the Mendeley database the classes come from a T-score measured by quantitative ultrasound, not by DEXA. The spec's target is "AUC against DXA labels". State this difference in the limits; do not call the model DEXA-validated.

4. **Uneven classes.** The Mendeley source has 36 normal, 154 osteopenia, and 49 osteoporosis images. A model that always answers "osteopenia" already scores 64% accuracy on it. Accuracy alone says little; report recall per class.

5. **No patient-level split.** The spec asks for a patient-level split with no leakage (page 7). A dataset merged from several sources does not say which images belong to the same patient, so that cannot be guaranteed. Say so.

6. **Cropped images.** The main KL dataset was made for joint detection and grading and is understood to be small crops of the knee joint. Crops like that have no soft-tissue edge, so they cannot be used for the muscle ratios. Check which datasets show the full width of the leg before building the ratio pipeline on them.

### Links that do not work

A longer dataset list went round the team on 2026-10-04. These entries were checked and are wrong; do not spend time on them:

| Link | What is there |
|---|---|
| `kaggle.com/datasets/mohamedgobara/knee-osteoporosis-dataset-multiclasses` | Page not found |
| `kaggle.com/datasets/thedevastator/osteoporosis-knee-xray-dataset` | Page not found. A dataset with a similar name exists at `stevepython/osteoporosis-knee-xray-dataset`; its contents have not been checked. |
| `kaggle.com/datasets/vigneshbaskar/bone-xray-image-dataset` | Page not found |
| `zenodo.org/records/6641975` | An unrelated software package for tracking objects in drone videos |
| `oai.ucsf.edu` | The address does not exist. OAI data is at https://nda.nih.gov/oai and needs an NDA account and acceptance of its data-use terms. |

The same list gave image counts and class counts for the Mendeley database (350 images, 120/110/120) and called its T-scores a DEXA proxy. The database's own README says otherwise; use the figures above.

## Training

- **Images go to a CNN.** Fine-tune a pretrained ResNet18 or EfficientNet-B0. Do not feed flattened pixels to a plain fully connected network (ANN) or to XGBoost; both throw away the image structure. X-rays are greyscale; repeat the channel three times to fit the pretrained input.
- **XGBoost is for tables**, such as the fusion step in the spec (ratios, grip, age, sex, BMI, SARC-F, chair stand). That step needs sarcopenia labels, which do not exist yet, so it is not trained in the hackathon build.
- Use mild augmentation only: small rotations, brightness and contrast changes, horizontal flip.
- Classes are uneven. Use class weights in the loss.
- Stop on validation loss, not training loss.

### What to report for each classifier

Report on the internal test split and on the external dataset separately:

- Accuracy and macro-F1
- Recall per class (recall of the osteoporosis class matters most for screening)
- AUC, one class against the rest
- The confusion matrix

Then add a row to the Results table. A model with no row there does not get mentioned on a slide.

### Use the heatmap as a check

Grad-CAM is in the spec as an explanation for doctors. It is also the quickest way to catch a model that cheats. Look at the heatmaps for about 20 test images. If they light up on image corners, text markers, or borders instead of bone, the model has learned a shortcut and its score cannot be trusted.

## Muscle ratios

From the spec (page 6):

1. Segment the image into three classes: 0 background, 1 bone, 2 soft tissue.
2. Find the joint line: the row with the fewest bone pixels in the middle of the image.
3. Measure the tibial plateau width. It is the ruler.
4. Go 0.6 times the plateau width above the joint (thigh level) and below it (calf level). Count bone and soft-tissue pixels on those rows.
5. Output `thigh_soft_to_bone`, `calf_soft_to_bone`, `soft_to_plateau`, `soft_area_ratio`.
6. Save an overlay image: the mask and the measurement lines drawn on the X-ray.

There are no labelled masks to train a U-Net on. Start with thresholds: air is dark, soft tissue is mid-grey, bone is bright, so `skimage.filters.threshold_multiotsu` with three classes gives a rough mask. Call it a heuristic everywhere it is described. Replace it with a trained segmentation model only if someone labels masks.

Thresholding does not work on every image. It fails on white borders, text burned into the picture, very dark or very bright exposures, and images where the other leg is in frame. Reject those at the quality check instead of returning wrong ratios.

### What was built (2026-10-04)

`ml/muscle.py`, called from `ml/predict.py`. It grew out of Pravesh's `ml/training/muscle_measure.py`, which used one brightness threshold and painted most of the leg as bone, and returned ratios like 117 on images it could not read. The current version finds the bone from its edges in each row, finds the joint as the dark gap where the bone is widest, measures at the two levels, and refuses when the result does not look like a leg.

Seen on 24 test X-rays (2 local, 22 from Wikimedia Commons, none labelled): 16 measured, 8 refused (joint line not found, or the leg edge cut off). The overlays were checked by eye: the joint line was in the right place on every measured image; the bone outline was right on most and blocky on a few shafts. About 70 ms per image. No number here has been compared with DXA or any other muscle measurement.

The ratios and the overlay are shown on the result and in the report. They do not change the sarcopenia stage: no cutoff for them exists, so `low_muscle` is not returned.

## Sarcopenia stage

No public knee X-ray dataset with sarcopenia labels was found, so no model can be trained for this now. The stage comes from rules.

Reference cutoffs:

| Measure | Low when | Source |
|---|---|---|
| Handgrip | below 28 kg (men), below 18 kg (women) | Spec FR-6, AWGS 2019 |
| 5-chair-stand time | 12 seconds or more | AWGS 2019 |
| SARC-F | 4 or more | AWGS 2019 |
| Calf circumference | below 34 cm (men), below 33 cm (women) | AWGS 2019 |

The spec states only the grip cutoff. Check the other three against the AWGS 2019 consensus paper before quoting them.

Proposed rule (prototype, team to confirm):

| Stage | Condition |
|---|---|
| none | Grip normal and chair stand normal |
| possible | Low grip, or slow chair stand |
| probable | Possible, and low muscle proxy from the X-ray |
| severe | Low grip, slow chair stand, and low muscle proxy |

Three honest limits:

- **The cutoff for "low muscle proxy" is not validated.** No study gives a threshold for these X-ray ratios. Whatever value is chosen is a prototype setting and must be described that way.
- **Rules give no probability.** Leave `sarcopenia_prob` empty. Do not show a percentage that was not computed from data. Show the stage and each input next to its cutoff.
- **SHAP does not apply.** SHAP explains a trained tabular model. With rules, the explanation is the table of inputs next to their cutoffs, which is already clearer than a SHAP chart.

## Handing models to the backend

- Put the final model files in `ml/models/`: `osteoporosis_best.pt`, `arthritis_best.pt`, `sarcopenia_ANN_1.joblib`, `osteoporosis_XGBoost_1.joblib`. Git ignores `*.pt`, so they are not in the repo; each teammate copies them in by hand from the team's Drive folder: https://drive.google.com/drive/folders/1Zxi-auctfcBx3Jhcx89zlIls5CgT20VN Without them (or without torch) the app runs and shows "AI model: not connected". The `*_last.pt` files are training checkpoints and are not needed.
- Write the inference code in `ml/predict.py`. The backend already calls it (`backend/analysis.py`), so the name and arguments are fixed:

  ```python
  def analyze(image_path: str, age: int, sex: str, bmi: float) -> dict:
  ```

  `sex` is `"male"`, `"female"`, or `"other"`. The image is a PNG or JPG in the uploads folder.

  Return a dict with any of these keys. Leave out, or set to `None`, whatever is not ready:

  | Key | Value |
  |---|---|
  | `model_version` | Short text naming the models used, for example `"osteo-resnet18-0.1"`. Always include it. |
  | `osteoporosis_prob` | Number from 0 to 1 |
  | `osteoporosis_tier` | `"low"`, `"moderate"`, or `"high"` |
  | `thigh_soft_to_bone`, `calf_soft_to_bone`, `soft_to_plateau`, `soft_area_ratio` | Numbers |
  | `low_muscle` | `True` or `False`: is the muscle measure below the prototype threshold |
  | `kl_grade` | 0 to 4 |
  | `overlay_path`, `gradcam_path` | Paths of images written into the same folder as the input image |

  The backend works out the sarcopenia stage itself from grip, chair stand, and `low_muscle`. The model does not return a stage.

  - Load each model once, when the module is imported, not on every call.
  - Raise a clear exception when the image cannot be analysed. The backend turns it into an error message.
  - Until this file exists, the backend stores the rule-based stage and leaves every image-based field empty.
- Any package `ml/predict.py` imports must also be in `backend/requirements.txt`.
- The spec's target is under 5 seconds per study on a CPU with no GPU. Measure it on a laptop and record it.

## Results

Figures are copied from Pravesh's training reports (`ml/reports/*_report.json`). They were not re-measured.

| Model | Date | Trained on | Internal test | External test | Notes |
|---|---|---|---|---|---|
| Osteoporosis, DenseNet121, 3 classes (`osteoporosis_best.pt`) | 2026-10-04 | 544 train, 69 validation images; started from the KL model's weights | 68 images: accuracy 0.765, macro-F1 0.765, AUC (one-vs-rest) 0.892. Normal vs bone loss: sensitivity 0.915 (43/47), specificity 0.762 (16/21) | not run | Small test set, so wide error margins. Score uses mirror-averaging, as the app does. Duplicate checks exist in `ml/training/` but their counts are not recorded. Which Kaggle set the 681 images came from is not recorded. |
| KL grade, DenseNet121, 5 classes (`arthritis_best.pt`) | 2026-10-04 | 8800 train, 1100 validation images | 1100 images: accuracy 0.735, macro-F1 0.752, quadratic kappa 0.862, within one grade 0.955. KL1 recall 0.545 | not run | Random split; images of the same patient may be on both sides. |

How the app uses them: the tier is the predicted class (Normal = low, Osteopenia = moderate, Osteoporosis = high) and `osteoporosis_prob` is the probability of the Osteoporosis class. CPU time on Anish's laptop: about 170 ms per image for both models, about 10 s to load at startup.

### Tabular models (connected 2026-10-04)

Pravesh also shared three models that use numbers, not the image. The two in use sit in `ml/models/` next to the X-ray weights; all of them are in the Drive folder. `ml/tabular.py` loads the two that are in use (`python -m ml.tabular` checks them) and the analyze endpoint calls both.

How the app uses them: "low muscle mass" from the first model is the muscle evidence in the sarcopenia stage rule, so the stage can now reach probable and severe. "Bone loss" from the second is shown as a separate line next to the X-ray result and changes nothing else. Waist, arm circumference, and the history answers are optional; what is missing the model fills in with typical values, and the result says so. The US ethnicity code is never sent.

Seen on five made-up patients on 2026-10-04: the muscle model separated thin from heavy people as expected. The bone-loss model answered "likely" for all five, including a fit 62-year-old man (probability 0.41, cutoff 0.32), which fits its low specificity. Pravesh says `sarcopenia_model.joblib` and `sarcopenia_ann.keras` are not used. Scores stored inside the files (5-fold cross-validation on NHANES, not re-measured): muscle model ROC-AUC 0.954, sensitivity 0.851, specificity 0.904; bone-loss model ROC-AUC 0.791, sensitivity 0.851, specificity 0.551.

| File | Predicts | Inputs |
|---|---|---|
| `sarcopenia_ann.keras`, `sarcopenia_ANN_1.joblib`, `sarcopenia_model.joblib` | Low muscle mass (yes or no) | age, sex, race/ethnicity code, height, weight, BMI, waist, arm circumference, best grip, combined grip |
| `osteoporosis_XGBoost_1.joblib` | Bone loss (yes or no) | the same, plus about 25 questionnaire answers (diabetes, fractures, smoking, steroid use, and others) |

From `ml/training/build_nhanes_dataset.py`: the data is NHANES 2011 to 2014 (US survey). "Low muscle mass" is DXA appendicular lean mass divided by height squared, below 7.0 (men) or 5.4 (women), the AWGS 2019 cutoffs. Bone loss is a femoral-neck T-score below -1. DXA values are kept out of the inputs. The ROC plot is titled "5-fold CV" and shows AUC 0.954 for the muscle model; no report file came with it.

Limits: whole-body DXA in these years covers ages 20 to 59 only, so the muscle model never saw the elderly patients this tool is for; the people are from the US, with US ethnicity codes; the label uses height, and weight and BMI are inputs, so part of the score is arithmetic; the app does not collect waist, arm circumference, ethnicity, or the questionnaire.

## Limits to state in the pitch

- No sarcopenia-labelled data: the stage is rule-based and the muscle proxy is unvalidated.
- Osteoporosis labels come from public datasets whose known source used ultrasound T-scores, not DEXA.
- Small, uneven public datasets, no patient-level split, no clinical validation.
- The source database is marked for research use only.
- It is a screening aid, not a diagnosis (spec page 1).
