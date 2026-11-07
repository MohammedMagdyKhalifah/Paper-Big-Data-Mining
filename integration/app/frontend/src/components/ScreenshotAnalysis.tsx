import {useEffect,useState} from 'react'
import {useMutation,useQueryClient} from '@tanstack/react-query'
import {ImagePlus,ScanText,Send,X} from 'lucide-react'
import {api} from '../api'
import type {OCRDraft} from '../types'
import {useLanguage} from '../i18n'
import {ErrorBox,PredictionCard,score} from './common'
import P1Evidence from './P1Evidence'
export default function ScreenshotAnalysis(){
 const {t}=useLanguage();const client=useQueryClient()
 const [file,setFile]=useState<File|null>(null),[preview,setPreview]=useState(''),[draft,setDraft]=useState<OCRDraft|null>(null)
 const [edited,setEdited]=useState(''),[context,setContext]=useState(''),[demo,setDemo]=useState(false),[error,setError]=useState('')
 const extract=useMutation({mutationFn:(f:File)=>api.extractImage(f),onSuccess:d=>{setDraft(d);setEdited(d.ocr.text)}})
 const analyze=useMutation({mutationFn:(body:unknown)=>api.analyzeP1(body),onSuccess:()=>{void client.invalidateQueries()}})
 const busy=extract.isPending||analyze.isPending
 useEffect(()=>{if(!file){setPreview('');return}const url=URL.createObjectURL(file);setPreview(url);return()=>URL.revokeObjectURL(url)},[file])
 const select=(next:File|null)=>{setDraft(null);setEdited('');setError('');extract.reset();analyze.reset();setFile(null)
  if(next&&(!/\.(png|jpe?g)$/i.test(next.name)||!['image/png','image/jpeg',''].includes(next.type))){setError('اختر صورة PNG أو JPG أو JPEG');return}
  if(next&&next.size>10*1024*1024){setError('حجم الصورة يتجاوز 10MB');return}setFile(next)
 }
 const submit=()=>{if(!draft)return
  if(!edited.trim()&&draft.ocr.text.trim()){setError('نص OCR المصحح فارغ');return}
  if(!edited.trim()&&!context.trim()){setError('لم يظهر نص؛ اكتب النص الصحيح أو أضف وصفًا للمشكلة');return}
  setError('');analyze.mutate({text:context.trim(),draft_id:draft.draft_id,corrected_text:edited===draft.ocr.text?null:edited.trim()||null,is_demo:demo})
 }
 return <section className="panel screenshot-panel"><div className="panel-heading"><h2><ImagePlus size={19}/>{t('تحليل لقطة شاشة')}</h2><span className="subtle-tag">PNG / JPG / JPEG</span></div>
 <p className="helper">{t('ارفع الصورة، راجع النص وصحّحه، ثم أرسله للتحليل الحقيقي. تُعالج الصورة محليًا ولا تُحفظ.')}</p>
 <label className="file-zone">{t('اختر لقطة شاشة')}<input aria-label={t('لقطة الشاشة')} disabled={busy} type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" onChange={e=>select(e.target.files?.[0]||null)}/></label>
 <p className="helper">{t('حتى 10MB و40MP. استخدم صورة واضحة واقصص البيانات غير اللازمة.')}</p>
 {preview&&<div className="screenshot-preview"><img src={preview} alt={t('معاينة لقطة الشاشة')}/><button type="button" className="secondary-button" disabled={busy} onClick={()=>select(null)}><X size={15}/>{t('إزالة الصورة')}</button></div>}
 {error&&<p role="alert" className="field-error">{t(error)}</p>}
 {extract.error&&<ErrorBox error={extract.error}/>}
 <button type="button" className="secondary-button" disabled={!file||busy} onClick={()=>{setDraft(null);analyze.reset();setError('');if(file)extract.mutate(file)}}><ScanText size={17}/>{extract.isPending?t('جارٍ استخراج النص…'):t('استخراج النص من الصورة')}</button>
 {draft&&<div className="ocr-review"><h3>{t('راجع النص قبل التحليل')}</h3>
 <p className="helper"><bdi>{draft.ocr.engine}</bdi> · {t('درجة المحرك:')} {t(score(draft.ocr.mean_confidence))}</p>
 {draft.ocr.low_confidence&&<p role="status" className="p1-warning">{t('درجة OCR منخفضة؛ راجع النص المستخرج بعناية.')}</p>}
 {draft.ocr.status==='empty'&&<p role="status" className="p1-warning">{t('لم يظهر نص؛ اكتب النص الصحيح أو أضف وصفًا للمشكلة')}</p>}
 <details><summary>{t('النص المستخرج الأصلي')}</summary><pre className="p1-text" dir="auto">{draft.ocr.text||t('لا يوجد نص')}</pre></details>
 <label>{t('نص OCR القابل للتصحيح')}<textarea dir="auto" lang="ar" rows={6} maxLength={20000} value={edited} disabled={busy} onChange={e=>{setEdited(e.target.value);analyze.reset()}}/></label>
 <label>{t('وصفك للمشكلة (اختياري)')}<textarea dir="auto" lang="ar" rows={3} maxLength={20000} value={context} disabled={busy} onChange={e=>{setContext(e.target.value);analyze.reset()}}/></label>
 <p className="helper">{t('أضف ما كنت تحاول فعله إذا كانت الصورة تعرض رسالة خطأ فقط. تُحجب بيانات الاتصال والهوية قبل الحفظ والتحليل.')}</p>
 <label className="checkbox-label"><input type="checkbox" checked={demo} disabled={busy} onChange={e=>{setDemo(e.target.checked);analyze.reset()}}/>{t('صورة اصطناعية أو مخصصة للاختبار (تُستبعد من البيانات الحقيقية)')}</label>
 <p className="helper">{t('درجات OCR غير معايرة ولا تمثل دقة مقاسة. لا تُحفظ الصورة الأصلية.')}</p>
 <button type="button" className="primary-button" disabled={busy} onClick={submit}><Send size={16}/>{analyze.isPending?t('جارٍ التحليل…'):t('تأكيد النص وتحليله وحفظه')}</button>
 </div>}
 {analyze.error&&<ErrorBox error={analyze.error}/>}
 {analyze.data&&(analyze.data.message?<><p role="status" className="success-note">{t(analyze.data.duplicate?'هذه الرسالة موجودة بالفعل؛ لم يتضاعف العدد.':'تم حفظ الرسالة ونتيجة التحليل.')}</p><PredictionCard message={analyze.data.message}/></>:<P1Evidence analysis={analyze.data.analysis}/>)}
 </section>
}
