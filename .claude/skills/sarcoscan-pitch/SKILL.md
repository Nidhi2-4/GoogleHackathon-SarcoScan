---
name: sarcoscan-pitch
description: Rules for anything SarcoScan says about itself to judges or readers (pitch deck slides, README claims, demo script, architecture or results summaries). Use whenever you write or edit slide text, a project description, a results statement, or answers to judge questions.
---

# SarcoScan pitch and claims

Read `docs/PITCH.md` first. It has the slide outline, the demo script, and likely judge questions. This skill is the rule set for what may be claimed.

Owner: Soham.

## Before writing a claim, check where it comes from

| Kind of statement | Allowed only if |
|---|---|
| An accuracy, AUC, sensitivity, or speed figure | It is a row in the Results table in `docs/ML.md`. Name the dataset next to it. |
| "The system does X" | The item is `done` in `docs/PLAN.md`, `docs/API.md`, or `docs/ARCHITECTURE.md`. |
| A security feature | Its row in the checklist in `docs/SECURITY.md` is `done`. |
| A figure from the spec (85% sensitivity, AUC 0.80, under 5 seconds, under 5 minutes) | It is labelled "target". |
| A statement about another study | It is quoted from the paper itself, with the link. |

If a statement fails its check, do not soften the wording to keep it. Either label it as planned, or leave it out.

## Words to use

- "Screening aid" and "refers patients for DEXA". Never "diagnoses" and never "replaces DEXA".
- "Prototype" for the sarcopenia stage and the muscle ratios. They are rule-based and unvalidated.
- "Target" for every figure taken from the spec.
- "Trained on public datasets" for the classifiers. Not "clinically validated".

## Things that must not appear as built

- The Bluetooth dynamometer or its cost. Spec version 2 moved handgrip to manual entry.
- A React Native mobile app. Mobile is the same web UI.
- Orthanc, FHIR, multi-language UI, patient login.
- Any figure for sarcopenia accuracy. There is no labelled data to measure it on.

## Demo data

Public dataset images and made-up patient names only. No real patient appears in a slide, a screenshot, or a video.

## Before you say it is done

Go through every number and every "we have" in the text and trace each to a doc as in the table above. List any you could not trace and tell the user.
