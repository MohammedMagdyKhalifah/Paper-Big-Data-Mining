# Annotation Guide — Arabic Technical-Complaint Taxonomy

**Version:** v1.1 (FROZEN 2026-10-30 for A4, before any A4 labeling). v1.0 was used for the v1 labels. Definitions of the six categories are unchanged; v1.1 only adds clarifications (§ Code-switching, rules 12–14).
**Unit:** one app-review text. **Coders see only** an opaque id and the privacy-masked text (no app name, rating, sentiment, or source label).
Placeholders such as `[URL] [EMAIL] [PHONE] [NUM] [USER]` replace masked personal data.

For every item you must decide five fields:

| field | values |
|---|---|
| `is_complaint` | `yes` / `no` / `unclear` |
| `category` | `AUTH` `AVAIL` `PERF` `TRANS` `UX` `OTHER`. Required when `is_complaint=yes`, otherwise `null` |
| `multi_issue` | `true` if the text reports **two or more independent technical problems** |
| `negation` | `true` if a problem is negated, resolved, or hypothetical (e.g. "ما فيه أي مشكلة", "كان يعلق والحين تمام") |
| `uncertain` | `true` if you are not confident in your decision (any field) |

---

## Q1. Is it a technical complaint? (`is_complaint`)

**`yes`** means the writer reports a **current, concrete difficulty using the app or digital service**: something fails, blocks, errors, is slow, is missing, or is hard to use. It can be short ("ما يفتح", "التطبيق لا يعمل").

**`no`** covers:
- Praise, thanks, or a general rating without a concrete problem: "تطبيق رائع", "جزاكم الله خير", "سيء جدا", "اسوأ تطبيق".
  A **bare negative opinion with no stated difficulty is `no`**, because it gives no actionable problem.
- Feature requests or suggestions **without** a reported failure: "ياليت تضيفون الوضع الليلي".
- Complaints about **non-technical** matters: prices, policy, content, other users, ads as content, game difficulty, customer-service behaviour, delivery driver late, food quality, government rules/decisions ("رفضوا طلبي لأن الشروط ما تنطبق" = policy, not technical).
- Religious or other off-topic text, questions without a reported problem, spam.
- A problem that is explicitly **resolved or negated** ("كان فيه مشكلة في الدخول وانحلت، شكرا") → `no` with `negation=true`.

**`unclear`** means the text **hints at a possible technical problem** but you cannot tell what or whether (garbled or truncated mid-problem). Use it sparingly.
- Insults or bare negativity with no stated difficulty ("زباله", "برنامج زبال", "فاشل") → `no`, **not** `unclear`.
- Gibberish, emoji-only praise, jokes, or off-topic text → `no`, **not** `unclear`.

Borderline rules:
- Ads that **block use** of the app (popups that prevent using it, crashes due to ads) → `yes`. Simply "كثير اعلانات" → `no` (content/business complaint).
- A suggestion that **implies a failure** ("ياليت تصلحون مشكلة الدخول") → `yes`.
- "التطبيق لا يعمل" / "ما يشتغل" / "خربان" → `yes` (category per Q2, usually `AVAIL` or `OTHER`, see below).
- A data or account state problem caused by the system ("بياناتي ما تحدثت", "الطلب معلق من شهر") → `yes`.
- A service or feature **not offered in my country/region/city** ("الخدمة غير متوفرة في منطقتي", "ما يدعم دولتي") → `no` (coverage/policy, not a technical failure).
- **No reply from staff or the agency** to a request or report ("رفعت طلب وما احد رد") → `no` (organisational). It is `yes` only if the system itself fails to submit, record, or update the request.
- Refunds of the app's **purchase price** or subscription disputes → `no` (business), unless a payment flow technically failed.

## Q2. Primary category (`category`). Exactly one.

Label the **stated symptom**, never a guessed root cause.

| code | meaning | typical cues (Arabic) | examples |
|---|---|---|---|
| `AUTH` | Login, registration, identity verification, OTP/SMS code, password, account locked/suspended, Nafath/Absher linking | دخول، تسجيل، رمز التحقق، كود، OTP، كلمة المرور، نفاذ، الحساب موقوف، ما يقبل الهوية | "كل ما أدخل يرفض رمز التحقق", "ما يوصلني الكود", "نسيت كلمة السر وما يرسل رابط" |
| `AVAIL` | The app or service **does not open, crashes, freezes, closes, shows a blocking error, or the server/service is down** | يقفل، يطلع من التطبيق، ما يفتح، يعلق، خطأ، الخدمة متوقفة، الخادم، لا يعمل بعد التحديث، شاشة بيضاء | "التطبيق يقفل فجأة لما أفتح الطلب", "يطلع خطأ في الاتصال بالخادم", "ما يفتح بعد التحديث" |
| `PERF` | Slowness, long loading, lag, delays **in the app's response** | بطيء، يحمل، تحميل طويل، ثقيل، يتأخر، لاق | "الصفحة تحمل وقت طويل جدا", "التطبيق ثقيل وبطيء" |
| `TRANS` | Payment fails, money charged but service/request not completed, a transaction/request/booking cannot be submitted or is stuck, a refund isn't processed **by the system** | الدفع، خصم المبلغ، سداد، فاتورة، الطلب ما اكتمل، ما قدرت أحجز، المعاملة معلقة، تحويل | "خصم المبلغ وما اكتمل الطلب", "ما أقدر أسدد الفاتورة يطلع خطأ", "الموعد ما ينحجز" |
| `UX` | Interface, navigation, layout, missing or hidden buttons, confusing design, language/font/display issues, a bad update to the design, accessibility | ما ألقى، الزر، الواجهة، التصميم، معقد، الخط، اللغة، ما يظهر، الشاشة مقطوعة | "ما أقدر ألاقي زر حجز الموعد", "التصميم الجديد معقد", "الكلام بالانجليزي" |
| `OTHER` | Technical complaint that does not clearly fit the above: generic "doesn't work" with no symptom detail, wrong data shown, notifications, location/GPS, update won't install, device compatibility, missing data | الخدمة ما ضبطت، البيانات غلط، الاشعارات، الموقع، ما يدعم جهازي، ما يتحدث | "الخدمة ما ضبطت معي", "الموقع غلط دايم", "ما يدعم جهازي" |

Precedence and ambiguity rules:
1. **First blocking failure wins.** If the text reports a chain of problems, choose the **first clearly stated problem that blocks task completion**. If none is blocking, choose the **most emphasised** one. If no category is defensible, use `OTHER`.
2. "لا يعمل / ما يشتغل / خربان" **alone** (no further detail) → `AVAIL` only if it clearly means the app won't open or run at all ("التطبيق لا يعمل نهائيا", "ما يفتح"). If it refers to a **specific service or feature** not working ("خدمة التجديد ما تشتغل") → `TRANS` if it is a transaction or request flow, otherwise `OTHER`.
3. Freezing / "يعلق": **stuck and unusable** → `AVAIL`. Merely slow → `PERF`.
4. Login fails **because of an error screen or crash** → `AUTH` (the user's goal was access). Crash on opening before any login → `AVAIL`.
5. Booking, appointment, or request cannot be **submitted/completed** → `TRANS`. Cannot **find** where to do it → `UX`.
6. Update broke the app → by symptom (crash → `AVAIL`, design worse → `UX`).
7. `OTHER` is a content class for real technical complaints. It is **not** a bin for `no` or `unclear`.
8. "لا يستجيب / ما يستجيب / معلق كل شوي" (the app is unresponsive or hangs) → `AVAIL`. Only explicit slowness wording → `PERF`.
9. **Data validation rejection during login, registration, activation, or identity checks** ("يرفض تاريخ الميلاد", "يطلب التأكد من البيانات رغم انها صحيحة" when signing in or registering, "يطلع لي ادخل بريدك" in a loop) → `AUTH`. Validation that blocks submitting a request/payment form → `TRANS`. Elsewhere → `OTHER`.
10. Cannot **download, install, or update** the app ("ما ينزل عندي", "التحديث ما يكتمل") → `OTHER`.
11. A specific **feature** inside the app is broken (maps, filters, camera) without crashing the app → `OTHER`, or `UX` if it is a display or navigation problem.

### Code-switching (Arabic + English) — v1.1
English or transliterated technical words carry the same meaning as their Arabic equivalents: OTP / code / login / sign in / password / account → AUTH cues; crash / error / not working / server down / stuck → AVAIL cues; slow / loading / lag → PERF; payment / pay / refund / transaction / booking failed → TRANS; button / interface / design / layout / dark mode → UX. A mixed sentence is labelled with exactly the same rules as an Arabic one; the presence of English is **never** by itself a reason for `unclear`.
Examples: "الـ OTP ما يوصلني" → AUTH · "the app keeps crashing بعد التحديث" → AVAIL · "الـ payment ما يكتمل" → TRANS · "ما ألقى زر الحجز" → UX.

12. **Payment succeeded but the digital service/order/record was not completed** ("انخصم المبلغ وما تحدث الطلب", "حولت رصيد وما وصلتني العملات", "الفاتورة معلقة ما تتسدد") → `TRANS`. Physical fulfilment problems by a merchant or courier (late delivery, wrong item, food quality) with no failing digital step → `no`.
13. **Process too long / too many steps / confusing flow** ("خطوات كثيرة", "معقد", "ما عرفت كيف أقدم") → `UX`. **Cannot find** a feature or option → `UX`.
14. An app that **opens a different page/app or loses typed input** → `OTHER` unless it blocks the whole app (→ `AVAIL`).

## Q3. `multi_issue`
`true` when two or more **independent** technical problems are reported (e.g., "بطيء وكمان رمز التحقق ما يوصل"). The primary category still follows rule 1.

## Q4. `negation`
`true` if the text contains a negated, resolved, or hypothetical problem ("ما فيه أي مشكلة", "ما يعلق أبدا", "انحلت المشكلة", "لو يصير فيه خلل"). Negation particles such as `لا، ما، مش، مو، ليس، مافي` change meaning: "ما يفتح" is a complaint, while "ما فيه مشاكل" is not.

## Q5. `uncertain`
`true` whenever you hesitated, for example between two categories, or when the text is too short or sarcastic. Do not use it to avoid a decision. Still give your best label.

---

## Output format (one JSON object per input line)
```json
{"id": "A0001", "is_complaint": "yes", "category": "AUTH", "multi_issue": false, "negation": false, "uncertain": false}
{"id": "A0002", "is_complaint": "no", "category": null, "multi_issue": false, "negation": false, "uncertain": false}
```

## Never
- Infer server root causes, or use star ratings, app identity, or sentiment to decide.
- Label from another coder's output.
- Invent a category outside the six.

## Changelog
- v1.0-draft: initial guide derived from the proposal (Table 1, Appendix A) and CLAUDE_CODE_ML_RESEARCH_PLAN.md §1.
- v1.1 (2026-10-30, A4): code-switching section and rules 12–14, derived from the v1 train/val label-issue review and from developer probes — NOT from any evaluation data. Category definitions unchanged.
- v1.0 (frozen after the 100-item pilot; pilot κ complaint 0.74 / joint 0.67 / category 0.69): clarified `unclear` vs `no` for insults and gibberish; added rules for regional coverage, agency non-response, purchase refunds, unresponsive app → AVAIL, validation at login/registration → AUTH, download/install → OTHER, broken feature → OTHER/UX. The pilot items are re-resolved by the adjudicator under v1.0.
