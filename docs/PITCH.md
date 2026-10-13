# Pitch and demo

Owner: Soham. Last updated: 2026-10-10.

Status: the deck is `HackPulse - Codesharks.pdf` in this folder (9 slides). This file holds the rules for what it may claim, and a review of the current version.

## The one rule

Judges trust a team that says exactly what it built. Every number and every "we have" on a slide must be true on the day.

- The spec's figures (85% sensitivity, osteoporosis AUC 0.80, under 5 seconds, under 5 minutes per patient) are **targets**. The spec says so itself on page 4. Write "target" next to them.
- A measured result goes on a slide only if it is in the Results table in `ML.md`.
- Say "prototype" for the sarcopenia stage and the muscle ratios. They are rule-based and unvalidated (`ML.md`).
- Do not show the Bluetooth dynamometer or its cost as something built. Spec version 2 moved handgrip to manual entry.
- Do not list a security feature that is still `planned` in the checklist in `SECURITY.md`.
- Say "built around DPDP principles", not "DPDP compliant". Say "append-only audit log", not "immutable" or "tamper-proof".
- Say "trained on public datasets labelled from ultrasound T-scores". Do not say "validated against DEXA".

## Review of the current deck

Checked on 2026-10-04 against what is built.

| Slide | What it says | Change to |
|---|---|---|
| 3, 6 | "Fusion of image + grip beats grip alone", "Our claim: fusion beats grip alone" | "Our hypothesis", with the validation plan from slide 8. Nothing has been measured. |
| 3 | "for web and mobile" | True if it means the web app on a phone. There is no separate mobile app. |
| 4 | "AI analysis (about 5 seconds)", "or auto-receive from PACS" | "Target: under 5 seconds". PACS is planned, not built. |
| 5 | Diagram with Nginx, Redis queue, Celery worker, MinIO, Orthanc, React Native app | Title it "Target architecture", or redraw what runs today: Next.js web app, FastAPI, PostgreSQL, file storage, model. |
| 5 | "DPDP compliant" | "Built around DPDP principles". Nobody has audited it. |
| 6 | U-Net segmentation and an XGBoost fusion model shown as the pipeline | "Planned approach". There is no labelled data for either yet. Today the stage comes from AWGS rules. |
| 7 | "FHIR export", "Explainable results (Grad-CAM)", "Segmentation overlay and muscle measurements", "Works offline on local network" | Keep only what works on demo day. FHIR is not built. Grad-CAM, overlay and measurements need the model. Offline has not been tested. |
| 9 | "Runs on one standard i5 / 16 GB computer, no GPU" | A target. Not measured. |

What the deck can say truthfully today: role-based login, patient registration and history, X-ray upload with a file check, handgrip against AWGS cutoffs, a rule-based sarcopenia stage, doctor review, PDF report, trend graph, encrypted patient name and phone, an append-only audit log.

## Slide outline

| # | Slide | Content | Source |
|---|---|---|---|
| 1 | Title | SarcoScan, team CodeSharks, one-line pitch | Spec page 1 |
| 2 | Problem | Sarcopenia is under-diagnosed: confirmation needs DEXA or CT, which smaller hospitals lack. Patients are found late, after falls or fractures. | Spec page 1 |
| 3 | Idea | Knee X-rays and handgrip tests are already routine. Combine them to flag risk. | Spec page 1 |
| 4 | How it works | The screening flow in 5 steps, with a screenshot of each | `ARCHITECTURE.md` |
| 5 | What the AI does | Osteoporosis classifier, muscle ratios, sarcopenia rules, overlay | `ML.md` |
| 6 | Architecture | One secure API, one UI, three ways to open it (web, mobile, desktop) | `ARCHITECTURE.md` |
| 7 | Security and privacy | On-premise, role-based access, audit log, what is built today | `SECURITY.md` |
| 8 | Results | Measured numbers only, with the dataset they were measured on | `ML.md` Results |
| 9 | Limits and validation plan | What is not validated, and how a hospital pilot would validate it | `ML.md`, spec page 7 |
| 10 | Next steps | Labelled data from a partner hospital, pilot, PACS integration | Spec page 4 |

## Prior work

One study supports the core idea that plain X-rays carry a muscle signal:

> Deep Learning-Based Muscle Segmentation and Quantification of Full-Leg Plain Radiograph for Sarcopenia Screening in Patients Undergoing Total Knee Arthroplasty. Journal of Clinical Medicine, 2022. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9267147/

Read the abstract and quote the paper's own numbers. Note the difference when citing it: that study used full-leg radiographs, and SarcoScan uses a knee view, which shows much less muscle.

## Demo script

Run it in this order. Each step should take a few seconds.

1. Log in as the demo doctor (one click on the sign-in page).
2. Search for a patient, then register a new one.
3. Start a screening. Enter clinical inputs.
4. Enter handgrip trials. Show the best value marked against the cutoff.
5. Upload a knee X-ray. Show the quality check passing.
6. Analyze. Show the results screen: stage, risk tier, overlay, values next to cutoffs.
7. Download the report.
8. Open the patient's history and show the trend graph.
9. Open the same screen on a phone, and as an installed desktop app.
10. Log in as the admin: every patient can be read, nothing can be changed. Each doctor sees only their own patients.

## Before the day

- Use only public dataset images and made-up patient names.
- Pick 3 to 5 X-rays that the system handles well, and one it rejects at the quality check.
- Record the whole script as a video once it works. If the live demo breaks, play the video.
- Rehearse with the internet off if the pitch says "works without internet".

## Questions judges are likely to ask

| Question | Honest answer |
|---|---|
| How accurate is it? | Give the measured numbers for the osteoporosis classifier and name the dataset. The sarcopenia stage is rule-based on published cutoffs; it has no accuracy figure yet. |
| Is it clinically validated? | No. It is a prototype. Validation needs X-rays paired with DEXA results from a partner hospital. |
| Why would a knee X-ray show muscle? | Soft tissue around the bone is visible on the image. Cite the prior work, and say the knee view is a weaker signal than a full leg. |
| Fat looks like muscle on an X-ray. | Correct, and the spec lists it as the first risk (page 4). That is why grip strength and BMI are part of the decision. |
| How is patient data protected? | It stays on the hospital's own server. List only the controls that are built. |
| Does it replace DEXA? | No. It decides who should be referred for DEXA. |
