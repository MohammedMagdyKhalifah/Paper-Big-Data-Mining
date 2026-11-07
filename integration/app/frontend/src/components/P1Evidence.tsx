import type {P1Analysis} from '../types'
import {useLanguage} from '../i18n'
import {number,score} from '../format'
export default function P1Evidence({analysis:a}:{analysis:P1Analysis}){
 const {t}=useLanguage()
 return <div className="p1-evidence">
 {a.signals.needs_user_context&&<div role="status" className="p1-warning">{t('الصورة تعرض إشارة خطأ. أضف وصفًا لما كنت تحاول فعله؛ هذه الإشارة ليست تشخيصًا لعطل مؤكد.')}</div>}
 {a.signals.ocr_needs_review&&<p className="p1-warning">{t('درجة OCR منخفضة؛ راجع النص المستخرج بعناية.')}</p>}
 {!a.prediction&&<p role="status" className="p1-warning">{t('لم يُصنّف أي نص ولم تُحفظ شكوى. صحّح النص أو أضف وصفًا للمشكلة.')}</p>}
 <h3>{t('الأنظمة المذكورة وأدلتها')}</h3>
 <p className="helper">{t('الأسماء مستخرجة بقواعد من النص؛ ذكر النظام لا يثبت أنه سبب المشكلة. الأسماء المحتملة لا تُحسب كنظام مؤكد.')}</p>
 {a.systems?.systems.length ? a.systems.systems.map(s=><div className="p1-system" key={s.system_id}><strong lang="ar" dir="rtl">{s.name_ar}</strong><ul>{s.mentions.map((m,i)=><li key={i}><q dir="auto">{m.text}</q> <small dir="ltr">[{number(m.start)}, {number(m.end)}) · {m.basis}</small></li>)}</ul></div>):<p>{t('لم يُحدد نظام مؤكد من النص.')}</p>}
 {!!a.systems?.possible_mentions.length&&<div className="p1-warning"><strong>{t('أسماء محتملة تحتاج تأكيدًا بشريًا')}</strong><ul>{a.systems.possible_mentions.map((m,i)=><li dir="auto" key={i}>{m.text} <small dir="ltr">[{number(m.start)}, {number(m.end)})</small></li>)}</ul></div>}
 {!!a.systems?.generic_references.length&&<p className="helper">{t('إشارات عامة لا تحدد اسم نظام:')} <bdi>{a.systems.generic_references.map(m=>m.text).join('، ')}</bdi></p>}
 {a.systems&&<p className="helper">{t('نسخة سجل الأنظمة:')} <bdi>{a.systems.registry_version}</bdi></p>}
 <details><summary>{t('النص المستخدم وتفاصيل OCR')}</summary>
 <h4>{t('النص الفعلي المرسل للنموذج')}</h4><blockquote className="complaint-text" dir="auto">{a.input.classified_text||t('لا يوجد نص')}</blockquote>
 {a.ocr&&<><h4>{t('النص المستخرج الأصلي')}</h4><pre className="p1-text" dir="auto">{a.ocr.text||t('لا يوجد نص')}</pre>{a.ocr.corrected_text!==null&&a.ocr.corrected_text!==undefined&&<><h4>{t('نص OCR بعد التصحيح')}</h4><pre className="p1-text" dir="auto">{a.ocr.corrected_text}</pre></>}
 <p className="helper"><bdi>{a.ocr.engine}</bdi> · {t('درجة المحرك:')} {t(score(a.ocr.mean_confidence))}</p><p className="helper">{t('درجات OCR غير معايرة ولا تمثل دقة مقاسة. لا تُحفظ الصورة الأصلية.')}</p></>}
 {!!a.signals.error_message_cues.length&&<p>{t('عبارات الخطأ في الصورة:')} <bdi>{a.signals.error_message_cues.map(c=>c.text).join('، ')}</bdi></p>}
 </details></div>
}
