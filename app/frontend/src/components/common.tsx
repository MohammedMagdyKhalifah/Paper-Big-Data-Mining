import {createContext,useContext} from 'react'
import {AlertCircle,ArrowUpLeft,Inbox,SlidersHorizontal,RotateCcw,CalendarDays} from 'lucide-react'
import {Link} from 'react-router-dom'
import type {Category,Complaint,Filters,ModelInfo} from '../types'
import {categories} from '../types'
import {useLanguage} from '../i18n'
export const Workspace=createContext<{filters:Filters;setFilters:(f:Filters)=>void;info:ModelInfo}>({filters:{},setFilters:()=>{},info:{} as ModelInfo})
export const useWorkspace=()=>useContext(Workspace)
// Analytical content stays Arabic in both interface languages.
export const number=(n:number)=>new Intl.NumberFormat('ar-SA').format(n)
export const percent=(n:number)=>new Intl.NumberFormat('ar-SA',{style:'percent',maximumFractionDigits:1}).format(n)
export const stamp=(s:string|null)=>s?new Intl.DateTimeFormat('ar-SA',{dateStyle:'medium',timeStyle:'short',calendar:'gregory',timeZone:'Asia/Riyadh'}).format(new Date(s)):'غير متاح'
export const score=(n:number|null)=>n===null?'غير متاحة':number(n)
export function Badge({category}:{category:Category|null}){return <span lang="ar" dir="rtl" className={`badge cat-${category||'none'}`}>{category?categories[category]:'دون فئة'}</span>}
export function ErrorBox({error}:{error:unknown}){const {t}=useLanguage();return <div role="alert" className="error-box"><AlertCircle size={18}/><span dir="auto">{error instanceof Error?t(error.message):t('حدث خطأ أثناء تحميل البيانات')}</span></div>}
export function Empty({text='لا توجد بيانات في هذا النطاق'}:{text?:string}){const {t}=useLanguage();return <div className="empty"><div className="empty-icon"><Inbox size={25}/></div><h3>{t(text)}</h3><p>{t('أضف رسالة أو عدّل الفلاتر لعرض النتائج.')}</p><Link className="text-link" to="/analyze">{t('تحليل رسالة جديدة')}<ArrowUpLeft size={16}/></Link></div>}
export function Loading(){const {t}=useLanguage();return <div className="loading" role="status"><span className="spinner"/>{t('جارٍ تحميل البيانات…')}</div>}
export function PageTitle({title,description,eyebrow='مساحة العمل'}:{title:string;description:string;eyebrow?:string}){const {t}=useLanguage();return <header className="page-title"><div className="eyebrow"><span/>{t(eyebrow)}</div><h1>{t(title)}</h1><p>{t(description)}</p></header>}
function dateKey(date:Date){return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Riyadh',year:'numeric',month:'2-digit',day:'2-digit'}).format(date)}
export function FilterBar(){
 const {t}=useLanguage();const {filters,setFilters}=useWorkspace()
 const set=(key:string,value:string)=>setFilters({...filters,[key]:value})
 const range=(days:number)=>{const now=new Date();setFilters({...filters,date_to:dateKey(now),date_from:dateKey(new Date(now.getTime()-(days-1)*86400000))})}
 const dirty=Boolean(filters.source||filters.date_from||filters.date_to)
 return <section className="filter-surface" aria-label={t('الفلاتر')}>
 <div className="filter-topline"><div><SlidersHorizontal size={15}/><strong>{t('الفلاتر')}</strong><span className={filters.data_scope==='demo'?'scope-pill demo':'scope-pill'}>{filters.data_scope==='demo'?'DEMO':'REAL'}</span></div><div className="range-shortcuts"><CalendarDays size={14}/><button onClick={()=>range(7)}>{t('آخر 7 أيام')}</button><button onClick={()=>range(30)}>{t('آخر 30 يومًا')}</button><button onClick={()=>setFilters({...filters,date_from:'',date_to:''})}>{t('كل الفترات')}</button>{dirty&&<button className="reset-button" onClick={()=>setFilters({...filters,source:'',date_from:'',date_to:''})}><RotateCcw size={12}/>{t('مسح الفلاتر')}</button>}</div></div>
 <div className="filter-bar">
 <label>{t('نطاق البيانات')}<select aria-label={t('نطاق البيانات')} value={filters.data_scope} onChange={e=>set('data_scope',e.target.value)}><option value="demo">{t('تجريبي / DEMO')}</option><option value="real">{t('البيانات الحقيقية')}</option></select></label>
 <label>{t('المصدر')}<select value={filters.source} onChange={e=>set('source',e.target.value)}><option value="">{t('كل المصادر')}</option><option value="text">{t('إدخال نصي')}</option><option value="csv">{t('ملف CSV')}</option></select></label>
 <label>{t('أساس التاريخ')}<select aria-label={t('أساس التاريخ')} value={filters.time_basis} onChange={e=>set('time_basis',e.target.value)}><option value="event">{t('تاريخ النشر الأصلي')}</option><option value="import">{t('وقت الاستيراد')}</option></select></label>
 <label>{t('من')}<input aria-label={t('من تاريخ')} type="date" value={filters.date_from} onChange={e=>set('date_from',e.target.value)}/></label>
 <label>{t('إلى')}<input aria-label={t('إلى تاريخ')} type="date" value={filters.date_to} onChange={e=>set('date_to',e.target.value)}/></label>
 </div></section>
}
export function PredictionCard({message}:{message:Complaint}){const {t}=useLanguage();return <section className="panel result-card" aria-label={t('نتيجة التحليل')}>
 <div className="panel-heading"><h2>{t('نتيجة التحليل')}</h2><span className={message.is_demo?'mode-tag':'real-tag'}>{message.is_demo?'DEMO / MOCK':t('نموذج حقيقي')}</span></div>
 <div className="result-primary"><Badge category={message.category}/><strong>{t(message.is_complaint?'تتضمن شكوى تقنية':'لا تتضمن شكوى تقنية')}</strong></div>
 <dl className="facts"><div><dt>{t('النظام المرتبط')}</dt><dd dir="auto">{message.system_name||t('غير محدد')}</dd></div><div><dt>{t('مصدر اسم النظام')}</dt><dd>{t(message.system_reviewed?'تصحيح بشري':message.system_evidence==='source_metadata'?'بيانات المصدر':'لا يوجد دليل')}</dd></div><div><dt>{t('درجة كشف الشكوى الأصلية')}</dt><dd>{t(score(message.original_prediction.complaint_score))}</dd></div><div><dt>{t('درجة الفئة الأصلية')}</dt><dd>{t(score(message.original_prediction.category_score))}</dd></div><div><dt>{t('المراجعة البشرية')}</dt><dd>{t(message.needs_review?'مطلوبة':'مكتملة')}</dd></div><div><dt>{t('نسخة النموذج')}</dt><dd dir="ltr">{message.model_version}</dd></div></dl>
 <p className="helper">{t('الدرجات تخص التوقع الأصلي، ولا تمثل دقة علمية مقاسة.')}</p>
 </section>}
