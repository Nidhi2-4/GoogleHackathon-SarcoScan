"""
Download NHANES and build clean tabular datasets for the SARCOPENIA and OSTEOPOROSIS risk models
(Decision Tree / Random Forest / XGBoost on patient medical history).

Works in Google Colab or locally:
    pip install pandas numpy requests
    python build_nhanes_dataset.py                 # 2013-2014 + 2011-2012 cycles
    python build_nhanes_dataset.py --cycles 2013   # only 2013-2014

Output (data/nhanes/):
    raw/*.xpt                    downloaded NHANES files (re-used on the next run)
    nhanes_final.csv             everyone, all cleaned features + all labels
    sarcopenia_dataset.csv       adults with grip strength AND whole-body DXA   (sarcopenia labels)
    osteoporosis_dataset.csv     adults 50+ with hip DXA                          (osteoporosis labels)
    data_dictionary.csv          what every column means and where it came from

Labels
    Sarcopenia (AWGS 2019, Asian criteria):
        low_grip          max grip < 28 kg (men) / < 18 kg (women)
        low_muscle_mass   DXA appendicular lean mass / height^2 < 7.0 (men) / < 5.4 (women)
        sarcopenia        low_grip AND low_muscle_mass
    Osteoporosis (WHO, femoral-neck T-score vs NHANES III young white women: mean 0.858, SD 0.120):
        bone_status       0 = Normal (T >= -1), 1 = Osteopenia (-2.5 < T < -1), 2 = Osteoporosis (T <= -2.5)
        bone_loss         1 if Osteopenia or Osteoporosis

Leakage protection
    - DXA values (lean mass, BMD, T-score, % fat) are LABEL sources -> never in the feature lists
    - "Doctor told you that you have osteoporosis" and treatment questions are NOT used
Limitations (state them)
    - Whole-body DXA in these cycles covers ages 8-59 only -> sarcopenia dataset is age 20-59
    - Grip strength exists only in 2011-2012 and 2013-2014
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# ======================= settings =======================
OUT_DIR = Path("data/nhanes")
CYCLES = {"2013": "H", "2011": "G"}            # cycle start year -> NHANES file letter
FILES = ["DEMO", "BMX", "MGX", "DXX", "DXXFEM", "OSQ", "MCQ", "DIQ", "BPQ", "SMQ", "PAQ", "KIQ_U"]
URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}_{letter}.xpt"

GRIP_CUT = {"male": 28.0, "female": 18.0}     # AWGS 2019, kg
ASMI_CUT = {"male": 7.0, "female": 5.4}       # AWGS 2019, DXA, kg/m^2
TSCORE_REF_MEAN, TSCORE_REF_SD = 0.858, 0.120 # NHANES III femoral neck, young white women (Looker 1998)
SARCO_MIN_AGE, OSTEO_MIN_AGE = 20, 50

# clinic-available features (no DXA) used by the models
FEATURES_COMMON = [
    "age", "sex_male", "race_eth", "height_cm", "weight_kg", "bmi", "waist_cm", "arm_circ_cm",
    "grip_max_kg", "grip_combined_kg",
    "diabetes", "prediabetes", "hypertension", "high_cholesterol", "arthritis", "heart_failure",
    "coronary_heart_disease", "heart_attack", "stroke", "liver_condition", "cancer", "gout", "weak_kidneys",
    "smoker_ever", "smoker_current", "vigorous_recreation", "moderate_recreation", "sedentary_min_per_day",
]
FEATURES_OSTEO_EXTRA = ["prior_hip_fracture", "prior_wrist_fracture", "prior_spine_fracture",
                        "any_prior_fracture", "steroid_use", "parent_hip_fracture"]
SARCO_LABELS = ["low_grip", "low_muscle_mass", "sarcopenia", "asmi", "alm_kg"]
OSTEO_LABELS = ["bone_status", "bone_loss", "femneck_tscore", "femneck_bmd", "total_hip_bmd"]

DICTIONARY = {
    "id": ("NHANES SEQN with cycle prefix", "DEMO.SEQN"),
    "cycle": ("Survey cycle start year", "-"),
    "exam_weight": ("MEC exam weight (only for population estimates, not needed for ML)", "DEMO.WTMEC2YR"),
    "age": ("Age in years (80 = 80+)", "DEMO.RIDAGEYR"),
    "sex_male": ("1 = male, 0 = female", "DEMO.RIAGENDR"),
    "race_eth": ("Race/ethnicity code (1 Mex-Am, 2 Other Hisp, 3 White, 4 Black, 6 Asian, 7 Other)", "DEMO.RIDRETH3"),
    "height_cm": ("Standing height", "BMX.BMXHT"),
    "weight_kg": ("Weight", "BMX.BMXWT"),
    "bmi": ("Body mass index", "BMX.BMXBMI"),
    "waist_cm": ("Waist circumference", "BMX.BMXWAIST"),
    "arm_circ_cm": ("Arm circumference", "BMX.BMXARMC"),
    "grip_max_kg": ("Highest of up to 6 grip trials (AWGS uses max grip)", "MGX.MGXH1T1-3, MGXH2T1-3"),
    "grip_combined_kg": ("Sum of best reading of each hand", "MGX.MGDCGSZ"),
    "diabetes": ("Doctor-diagnosed diabetes", "DIQ.DIQ010 == 1"),
    "prediabetes": ("Borderline diabetes", "DIQ.DIQ010 == 3"),
    "hypertension": ("Ever told high blood pressure", "BPQ.BPQ020"),
    "high_cholesterol": ("Ever told high cholesterol", "BPQ.BPQ080"),
    "arthritis": ("Ever told arthritis", "MCQ.MCQ160A"),
    "heart_failure": ("Congestive heart failure", "MCQ.MCQ160B"),
    "coronary_heart_disease": ("Coronary heart disease", "MCQ.MCQ160C"),
    "heart_attack": ("Heart attack", "MCQ.MCQ160E"),
    "stroke": ("Stroke", "MCQ.MCQ160F"),
    "liver_condition": ("Any liver condition", "MCQ.MCQ160L"),
    "cancer": ("Ever told cancer", "MCQ.MCQ220"),
    "gout": ("Gout", "MCQ.MCQ160N"),
    "weak_kidneys": ("Ever told weak/failing kidneys", "KIQ_U.KIQ022"),
    "smoker_ever": ("Smoked 100+ cigarettes in life", "SMQ.SMQ020"),
    "smoker_current": ("Smokes now (every day / some days)", "SMQ.SMQ040"),
    "vigorous_recreation": ("Vigorous recreational activity", "PAQ.PAQ650"),
    "moderate_recreation": ("Moderate recreational activity", "PAQ.PAQ665"),
    "sedentary_min_per_day": ("Minutes sitting per day", "PAQ.PAD680"),
    "prior_hip_fracture": ("Ever broken hip", "OSQ.OSQ010A"),
    "prior_wrist_fracture": ("Ever broken wrist", "OSQ.OSQ010B"),
    "prior_spine_fracture": ("Ever broken spine", "OSQ.OSQ010C"),
    "any_prior_fracture": ("Any of hip / wrist / spine fracture", "OSQ.OSQ010A-C"),
    "steroid_use": ("Ever took prednisone/cortisone daily", "OSQ.OSQ130"),
    "parent_hip_fracture": ("Mother or father broke hip", "OSQ.OSQ170, OSQ200"),
    "alm_kg": ("LABEL SOURCE - DXA appendicular lean mass (arms + legs, excl. bone)", "DXX.DXDLALE+DXDRALE+DXDLLLE+DXDRLLE"),
    "asmi": ("LABEL SOURCE - ALM / height^2 (kg/m^2)", "derived"),
    "low_grip": ("LABEL - AWGS 2019 low grip", "derived"),
    "low_muscle_mass": ("LABEL - AWGS 2019 low DXA muscle mass", "derived"),
    "sarcopenia": ("LABEL - low grip AND low muscle mass", "derived"),
    "femneck_bmd": ("LABEL SOURCE - femoral neck BMD g/cm^2", "DXXFEM.DXXNKBMD"),
    "total_hip_bmd": ("LABEL SOURCE - total femur BMD g/cm^2", "DXXFEM.DXXOFBMD"),
    "femneck_tscore": ("LABEL SOURCE - femoral neck T-score", "derived"),
    "bone_status": ("LABEL - 0 Normal / 1 Osteopenia / 2 Osteoporosis", "derived"),
    "bone_loss": ("LABEL - Osteopenia or Osteoporosis", "derived"),
}


# ======================= download =======================
def download_all(cycles, raw_dir):
    import requests
    raw_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    for year in cycles:
        letter = CYCLES[year]
        for name in FILES:
            dest = raw_dir / f"{name}_{letter}.xpt"
            if dest.exists() and dest.stat().st_size > 1000:
                print(f"  have   {dest.name}")
                continue
            url = URL.format(year=year, name=name, letter=letter)
            try:
                r = requests.get(url, headers=headers, timeout=180)
                ok = r.status_code == 200 and r.content[:14] == b"HEADER RECORD*"
            except Exception as e:
                ok, r = False, None
                print(f"  ERROR  {dest.name}: {e}")
            if ok:
                dest.write_bytes(r.content)
                print(f"  got    {dest.name} ({len(r.content) / 1e6:.1f} MB)")
            else:
                code = r.status_code if r is not None else "-"
                print(f"  MISSING {dest.name} (HTTP {code}) - skipped. If the site blocks scripts, "
                      f"download it in a browser (Ctrl+S) into {raw_dir}/")


def load_tables(year, raw_dir):
    letter = CYCLES[year]
    tables = {}
    for name in FILES:
        p = raw_dir / f"{name}_{letter}.xpt"
        if p.exists() and p.stat().st_size > 1000:
            tables[name] = pd.read_sas(p, format="xport")
    return tables


# ======================= cleaning helpers =======================
def col(df, name):
    """Column as float Series, or all-NaN if the variable doesn't exist in this cycle."""
    return df[name].astype(float) if name in df.columns else pd.Series(np.nan, index=df.index)


def yes_no(s):
    """NHANES coding: 1 = yes, 2 = no, 7/9 = refused/don't know -> NaN."""
    return s.map({1.0: 1.0, 2.0: 0.0})


def clean_minutes(s):
    return s.where(s < 7777)


def any_yes(*series):
    df = pd.concat(series, axis=1)
    out = df.max(axis=1)
    return out.where(df.notna().any(axis=1))


# ======================= build one cycle =======================
def build_cycle(year, tables):
    if "DEMO" not in tables:
        raise SystemExit(f"DEMO file missing for cycle {year} - can't build without it.")
    df = tables["DEMO"].copy()
    for name, t in tables.items():
        if name != "DEMO":
            df = df.merge(t, on="SEQN", how="left", suffixes=("", f"_{name}"))

    out = pd.DataFrame(index=df.index)
    out["id"] = f"{year}_" + df["SEQN"].astype(int).astype(str)
    out["cycle"] = int(year)
    out["exam_weight"] = col(df, "WTMEC2YR")

    # demographics + body measures
    out["age"] = col(df, "RIDAGEYR")
    out["sex_male"] = col(df, "RIAGENDR").map({1.0: 1.0, 2.0: 0.0})
    out["race_eth"] = col(df, "RIDRETH3")
    out["height_cm"] = col(df, "BMXHT")
    out["weight_kg"] = col(df, "BMXWT")
    out["bmi"] = col(df, "BMXBMI")
    out["waist_cm"] = col(df, "BMXWAIST")
    out["arm_circ_cm"] = col(df, "BMXARMC")

    # grip strength
    trials = pd.concat([col(df, f"MGXH{h}T{t}") for h in (1, 2) for t in (1, 2, 3)], axis=1)
    out["grip_max_kg"] = trials.max(axis=1)
    out["grip_combined_kg"] = col(df, "MGDCGSZ")

    # medical history
    dq = col(df, "DIQ010")
    out["diabetes"] = dq.map({1.0: 1.0, 2.0: 0.0, 3.0: 0.0})
    out["prediabetes"] = dq.map({1.0: 0.0, 2.0: 0.0, 3.0: 1.0})
    out["hypertension"] = yes_no(col(df, "BPQ020"))
    out["high_cholesterol"] = yes_no(col(df, "BPQ080"))
    for feat, var in [("arthritis", "MCQ160A"), ("heart_failure", "MCQ160B"),
                      ("coronary_heart_disease", "MCQ160C"), ("heart_attack", "MCQ160E"),
                      ("stroke", "MCQ160F"), ("liver_condition", "MCQ160L"), ("cancer", "MCQ220"),
                      ("gout", "MCQ160N"), ("weak_kidneys", "KIQ022")]:
        out[feat] = yes_no(col(df, var))

    # lifestyle
    out["smoker_ever"] = yes_no(col(df, "SMQ020"))
    now = col(df, "SMQ040").map({1.0: 1.0, 2.0: 1.0, 3.0: 0.0})
    out["smoker_current"] = now.where(out["smoker_ever"] != 0, 0.0)
    out["vigorous_recreation"] = yes_no(col(df, "PAQ650"))
    out["moderate_recreation"] = yes_no(col(df, "PAQ665"))
    out["sedentary_min_per_day"] = clean_minutes(col(df, "PAD680"))

    # osteoporosis history (not the diagnosis itself -> no leakage)
    out["prior_hip_fracture"] = yes_no(col(df, "OSQ010A"))
    out["prior_wrist_fracture"] = yes_no(col(df, "OSQ010B"))
    out["prior_spine_fracture"] = yes_no(col(df, "OSQ010C"))
    out["any_prior_fracture"] = any_yes(out["prior_hip_fracture"], out["prior_wrist_fracture"],
                                        out["prior_spine_fracture"])
    out["steroid_use"] = yes_no(col(df, "OSQ130"))
    out["parent_hip_fracture"] = any_yes(yes_no(col(df, "OSQ170")), yes_no(col(df, "OSQ200")))

    # ---------- sarcopenia labels (AWGS 2019) ----------
    lean = pd.concat([col(df, v) for v in ("DXDLALE", "DXDRALE", "DXDLLLE", "DXDRLLE")], axis=1)
    alm = lean.sum(axis=1, min_count=4) / 1000.0
    if "DXAEXSTS" in df.columns:
        alm = alm.where(col(df, "DXAEXSTS") == 1)            # only completed, valid scans
    out["alm_kg"] = alm
    out["asmi"] = alm / (out["height_cm"] / 100.0) ** 2

    male = out["sex_male"] == 1
    grip_cut = np.where(male, GRIP_CUT["male"], GRIP_CUT["female"])
    asmi_cut = np.where(male, ASMI_CUT["male"], ASMI_CUT["female"])
    sex_known = out["sex_male"].notna()
    out["low_grip"] = (out["grip_max_kg"] < grip_cut).astype(float).where(out["grip_max_kg"].notna() & sex_known)
    out["low_muscle_mass"] = (out["asmi"] < asmi_cut).astype(float).where(out["asmi"].notna() & sex_known)
    both = out["low_grip"].notna() & out["low_muscle_mass"].notna()
    out["sarcopenia"] = ((out["low_grip"] == 1) & (out["low_muscle_mass"] == 1)).astype(float).where(both)

    # ---------- osteoporosis labels (WHO T-score, femoral neck) ----------
    out["femneck_bmd"] = col(df, "DXXNKBMD")
    out["total_hip_bmd"] = col(df, "DXXOFBMD")
    t = (out["femneck_bmd"] - TSCORE_REF_MEAN) / TSCORE_REF_SD
    out["femneck_tscore"] = t
    out["bone_status"] = np.select([t <= -2.5, t < -1.0], [2.0, 1.0], default=0.0)
    out.loc[t.isna(), "bone_status"] = np.nan
    out["bone_loss"] = (out["bone_status"] >= 1).astype(float).where(t.notna())
    return out


# ======================= reporting =======================
def summarize(name, df, features, labels):
    print(f"\n----- {name}: {len(df)} people -----")
    for lab in labels:
        if lab in ("bone_status",):
            vc = df[lab].value_counts().sort_index()
            names = {0.0: "Normal", 1.0: "Osteopenia", 2.0: "Osteoporosis"}
            print("  " + ", ".join(f"{names[k]} {int(v)} ({v / len(df):.1%})" for k, v in vc.items()))
        elif set(df[lab].dropna().unique()) <= {0.0, 1.0}:
            print(f"  {lab:<16}: {int(df[lab].sum())} positive ({df[lab].mean():.1%})")
    miss = df[features].isna().mean().sort_values(ascending=False)
    miss = miss[miss > 0.05]
    if len(miss):
        print("  features with >5% missing (XGBoost handles NaN; impute for DT/RF):")
        for f, m in miss.items():
            print(f"    {f:<24} {m:.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", nargs="+", default=list(CYCLES), choices=list(CYCLES))
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--skip-download", action="store_true", help="only use files already in raw/")
    args = ap.parse_args()
    out_dir = Path(args.out)
    raw = out_dir / "raw"

    if not args.skip_download:
        print("Downloading NHANES files ...")
        download_all(args.cycles, raw)

    parts = []
    for year in args.cycles:
        tables = load_tables(year, raw)
        print(f"\nCycle {year}: loaded {sorted(tables)}")
        if "DEMO" not in tables:
            print(f"  skipping cycle {year} (no DEMO file)")
            continue
        parts.append(build_cycle(year, tables))
    if not parts:
        raise SystemExit("No data loaded. Check the downloads in " + str(raw))
    final = pd.concat(parts, ignore_index=True)

    sarco = final[(final["age"] >= SARCO_MIN_AGE) & final["sarcopenia"].notna()]
    sarco = sarco[["id", "cycle"] + FEATURES_COMMON + SARCO_LABELS].reset_index(drop=True)
    osteo = final[(final["age"] >= OSTEO_MIN_AGE) & final["bone_status"].notna()]
    osteo = osteo[["id", "cycle"] + FEATURES_COMMON + FEATURES_OSTEO_EXTRA + OSTEO_LABELS].reset_index(drop=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    final.to_csv(out_dir / "nhanes_final.csv", index=False)
    sarco.to_csv(out_dir / "sarcopenia_dataset.csv", index=False)
    osteo.to_csv(out_dir / "osteoporosis_dataset.csv", index=False)
    pd.DataFrame([{"column": k, "description": v[0], "source": v[1]} for k, v in DICTIONARY.items()]) \
        .to_csv(out_dir / "data_dictionary.csv", index=False)

    print(f"\nAll people: {len(final)}")
    summarize(f"SARCOPENIA dataset (age {SARCO_MIN_AGE}+, grip + whole-body DXA)", sarco, FEATURES_COMMON,
              ["low_grip", "low_muscle_mass", "sarcopenia"])
    summarize(f"OSTEOPOROSIS dataset (age {OSTEO_MIN_AGE}+, hip DXA)", osteo,
              FEATURES_COMMON + FEATURES_OSTEO_EXTRA, ["bone_status", "bone_loss"])
    print(f"\nSaved to {out_dir}/: nhanes_final.csv, sarcopenia_dataset.csv, "
          f"osteoporosis_dataset.csv, data_dictionary.csv")
    print("Model features : FEATURES_COMMON (+ FEATURES_OSTEO_EXTRA for osteoporosis), listed at the top")
    print("Never use as features: alm_kg, asmi, femneck_bmd, total_hip_bmd, femneck_tscore (they ARE the labels)")


if __name__ == "__main__":
    main()