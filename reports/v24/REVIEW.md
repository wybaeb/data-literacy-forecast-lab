# Experiment duration trainer — review and gate
Adapted conceptual sequence from local A360 `a360/build/trainer_accum.py` and `a360/trainer_accum.html`. Original retrospective rule (boundary stays separated to end of observed future) is not reused as a prospective stopping procedure.

Known-variance normal independent samples; equal arms; two-sided alpha .05; predefined n and maturity horizon. Sample size independently checked against scipy normal quantiles. Outcome simulation reproducible; no premature decisions; interval of difference used at planned end. Enrollment and follow-up overlap; last-user maturation determines planned end in this fixed-lag model.

Five permanent tabs with active state; existing distribution trainer pointer, touch, undo, CSV and statistics pass. Browser tested slider changes, random rerun, zero effect, animation, method link, mobile overflow; zero console errors. Existing page URLs and models preserved.

Map: find A360 → T59 reference review complete; add duration trainer → T59 model/UI complete; all-tabs compatibility → T59 regression complete; publish → T60 pending public verification. No main merge.
