# P1 system-mention annotation guide (as given to the AI coders)

Provenance: AI-assisted reference labels (coder A = sonnet, coder B = fable, independent and blind; blind adjudicator = opus on
disagreements, seeing anonymised and shuffled labels). **Not human gold.** Coders saw only `id + text`: no detector output,
stratum or app name. Registry shown = configs/systems.yaml v1 (ids, Arabic/English names, aliases).

Task: list which REGISTERED digital systems the text EXPLICITLY NAMES as a system (app / platform / e-service).
1. Count a system only if its name appears in the text AND is used as the name of the digital system. Spelling variants, missing
   hamza (ابشر/أبشر), attached prefixes (وأبشر, بتوكلنا, لنفاذ) and Latin spellings count.
2. Do NOT count the ordinary-word meaning: "ابشر" = "sure/good news", "توكلنا على الله", "صحتي" = "my health", "موعد" = "an
   appointment", "اقوى/قوى" = "strong/forces", "سكني" = "my housing", "وطني" = "national", "اعتماد" = "approval", "سداد" =
   "repayment", "مقيم" = "a resident", "موارد" = "resources", "بلدي" = "my country", "إحسان" = "kindness".
3. Generic references ("التطبيق", "البرنامج", "the app") are NOT a system. Do not guess the system from the topic.
4. Undecidable -> `uncertain_ids` (not `systems`).
5. Names of other apps/services not in the registry -> `unregistered` (free text).
Output per item: `{id, systems, uncertain_ids, unregistered}`.
