import { useLanguage } from '../i18n';
import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Search, X, Save, History } from 'lucide-react';
import { api } from '../api';
import {useSearchParams} from 'react-router-dom';
import { categories } from '../types';
import type { Category, Complaint, Review } from '../types';
import { Badge, Empty, ErrorBox, Loading, number, PageTitle, PredictionCard, stamp, useWorkspace } from '../components/common';
export function ReviewEditor({ message, onSaved }: {
    message: Complaint;
    onSaved: () => void;
}) {
    const { t } = useLanguage();
    const [form, setForm] = useState<Review>({ is_complaint: message.is_complaint, category: message.category, system_name: message.system_name, needs_review: false });
    const client = useQueryClient();
    const save = useMutation({ mutationFn: (body: Review) => api.review(message.id, body), onSuccess: () => { void client.invalidateQueries(); onSaved(); } });
    return <section className="panel review-editor"><h2>{t("المراجعة البشرية")}</h2><p className="helper">{t("يُحفظ التصحيح منفصلًا عن توقع النموذج الأصلي، ولا يعيد تدريب النموذج.")}</p>
 <form onSubmit={e => { e.preventDefault(); save.mutate(form); }}><div className="form-grid">
 <label>{t("هل تحتوي شكوى تقنية؟")}<select value={String(form.is_complaint)} onChange={e => setForm({ ...form, is_complaint: e.target.value === 'true', category: e.target.value === 'false' ? null : form.category })}><option value="true">{t("نعم")}</option><option value="false">{t("لا")}</option></select></label>
 <label>{t("التصنيف المصحح")}<select aria-label={t("التصنيف المصحح")} disabled={!form.is_complaint} value={form.category || ''} onChange={e => setForm({ ...form, category: (e.target.value || null) as Category | null })}><option value="">{t("غير محدد")}</option>{Object.entries(categories).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label></div>
 <label>{t("اسم النظام المصحح")}<input aria-label={t("اسم النظام المصحح")} value={form.system_name || ''} maxLength={200} placeholder={t("اتركه فارغًا عند غياب الدليل")} onChange={e => setForm({ ...form, system_name: e.target.value || null })}/></label>
 <label className="checkbox-label"><input type="checkbox" checked={form.needs_review} onChange={e => setForm({ ...form, needs_review: e.target.checked })}/>{t("يحتاج مراجعة إضافية")}</label>
 {save.error && <ErrorBox error={save.error}/>}{save.isSuccess && <p role="status" className="success-note">{t("تم حفظ التصحيح وسجل التعديل.")}</p>}
 <button className="primary-button" disabled={save.isPending}><Save size={16}/>{save.isPending ? t("جارٍ الحفظ…") : t("حفظ التصحيح")}</button></form></section>;
}
function Details({ id, onClose }: {
    id: number;
    onClose: () => void;
}) {
    const { t } = useLanguage();
    const panel = useRef<HTMLElement>(null);
    useEffect(() => { panel.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' }); }, [id]);
    const result = useQuery({ queryKey: ['detail', id], queryFn: () => api.detail(id) });
    useEffect(() => { const fn = (e: KeyboardEvent) => { if (e.key === 'Escape')
        onClose(); }; window.addEventListener('keydown', fn); return () => window.removeEventListener('keydown', fn); }, [onClose]);
    return <section ref={panel} className="details" aria-label={t("تفاصيل الرسالة")}><div className="panel-heading"><h2>{t("تفاصيل الرسالة #")}{number(id)}</h2><button className="icon-button" aria-label={t("إغلاق التفاصيل")} onClick={onClose}><X size={20}/></button></div>
 {result.error ? <ErrorBox error={result.error}/> : !result.data ? <Loading /> : <><blockquote className="complaint-text" dir="auto" lang="ar">{result.data.text_redacted}</blockquote><div className="metadata-row"><span>{t("النشر: ")}{stamp(result.data.original_event_time)}</span><span>{t("الاستيراد: ")}{stamp(result.data.imported_at)}</span></div><PredictionCard message={result.data}/><section className="original-note"><h3>{t("التوقع الأصلي المحفوظ")}</h3><p>{result.data.original_prediction.is_complaint ? t("شكوى تقنية") : t("غير شكوى")} • {result.data.original_prediction.category ? categories[result.data.original_prediction.category] : t("دون فئة")}{t(" • النظام الأصلي: ")}{result.data.original_system_name || t("غير محدد")}</p></section><ReviewEditor key={`${id}-${result.data.corrections.length}`} message={result.data} onSaved={() => { }}/>
 <section className="panel"><h2><History size={18}/>{t(" سجل التصحيحات")}</h2>{!result.data.corrections.length ? <p className="helper">{t("لا توجد تصحيحات محفوظة لهذه الرسالة.")}</p> : <ol className="audit-list">{result.data.corrections.map(c => <li key={c.id}><strong>{({ category: t("التصنيف"), system_name: t("اسم النظام"), is_complaint: t("وجود شكوى"), needs_review: t("حالة المراجعة") } as Record<string, string>)[c.field_name] || c.field_name}</strong><p><bdi>{String(c.old_value ?? t("غير محدد"))}</bdi> ← <bdi>{String(c.new_value ?? t("غير محدد"))}</bdi></p><small>{stamp(c.corrected_at)}</small></li>)}</ol>}</section></>}
 </section>;
}
export default function Explorer({ reviewOnly = false }: {
    reviewOnly?: boolean;
}) {
    const { t } = useLanguage();
    const { filters } = useWorkspace();
    const [params]=useSearchParams();
    const [q, setQ] = useState(params.get('q')||'');
    const [category, setCategory] = useState(params.get('category')||'');
    const [system, setSystem] = useState(params.get('system')||'');
    const [complaint, setComplaint] = useState(params.get('is_complaint')||'');
    const [review, setReview] = useState('');
    const [page, setPage] = useState(1);
    const [selected, setSelected] = useState<number | null>(null);
    useEffect(() => { setPage(1); setSelected(null); }, [filters, q, category, system, complaint, review, reviewOnly]);
    const f = { ...filters, q, category, system, is_complaint: complaint, needs_review: reviewOnly ? 'true' : review, page: String(page) };
    const rows = useQuery({ queryKey: ['complaints', f], queryFn: () => api.list(f) });
    const systems = useQuery({ queryKey: ['systems', filters], queryFn: () => api.systems(filters) });
    return <><PageTitle title={reviewOnly ? t("طابور المراجعة") : t("مستكشف الشكاوى")} description={reviewOnly ? t("راجع القرارات غير المؤكدة واحفظ تصحيحك مع الحفاظ على التوقع الأصلي.") : t("ابحث في الرسائل المحفوظة واستعرض نتائج التحليل وسجل المراجعات.")}/>
 <section className="panel explorer-panel"><div className="explorer-filters"><label className="search-field"><Search size={17}/><input aria-label={t("البحث في الرسائل")} placeholder={t("البحث في نص الرسالة…")} value={q} onChange={e => setQ(e.target.value)}/></label><select aria-label={t("فلتر الفئة")} value={category} onChange={e => setCategory(e.target.value)}><option value="">{t("كل الفئات")}</option>{Object.entries(categories).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select><select aria-label={t("فلتر النظام")} value={system} onChange={e => setSystem(e.target.value)}><option value="">{t("كل الأنظمة")}</option><option value="__unknown__">{t("غير محدد")}</option>{systems.data?.items.filter(s => s.name).map(s => <option key={s.name} value={s.name!}>{s.name}</option>)}</select><select aria-label={t("فلتر وجود شكوى")} value={complaint} onChange={e => setComplaint(e.target.value)}><option value="">{t("كل الرسائل")}</option><option value="true">{t("شكوى تقنية")}</option><option value="false">{t("غير شكوى")}</option></select>{!reviewOnly && <select aria-label={t("فلتر المراجعة")} value={review} onChange={e => setReview(e.target.value)}><option value="">{t("كل حالات المراجعة")}</option><option value="true">{t("تحتاج مراجعة")}</option><option value="false">{t("مكتملة")}</option></select>}</div>
 {rows.error ? <ErrorBox error={rows.error}/> : !rows.data ? <Loading /> : !rows.data.items.length ? <Empty text={reviewOnly ? t("لا توجد رسائل تنتظر المراجعة") : t("لا توجد رسائل تطابق الفلاتر")}/> : <><div className="table-scroll"><table><thead><tr><th>{t("الرسالة")}</th><th>{t("النظام")}</th><th>{t("الفئة الرئيسية")}</th><th>{t("تاريخ النشر")}</th><th>{t("الحالة")}</th><th><span className="sr-only">{t("التفاصيل")}</span></th></tr></thead><tbody>{rows.data.items.map(m => <tr key={m.id}><td><span className="row-id">#{number(m.id)} • {m.source === 'csv' ? 'CSV' : t("إدخال نصي")}{m.is_demo ? ' • DEMO' : ''}</span><p className="row-text" dir="auto" lang="ar">{m.text_redacted}</p></td><td>{m.system_name || t("غير محدد")}</td><td>{m.is_complaint ? <Badge category={m.category}/> : <span className="subtle-tag">{t("غير شكوى")}</span>}</td><td className="nowrap">{stamp(m.original_event_time)}</td><td><span className={`review-state ${m.needs_review ? 'pending' : ''}`}>{m.needs_review ? t("تحتاج مراجعة") : t("مكتملة")}</span></td><td><button className="text-link" onClick={() => setSelected(m.id)}>{t("استعراض")}</button></td></tr>)}</tbody></table></div><div className="pagination"><span>{number(rows.data.total)}{t(" رسالة • صفحة ")}{number(page)}</span><div><button className="icon-button" aria-label={t("الصفحة السابقة")} disabled={page === 1} onClick={() => setPage(page - 1)}><ChevronRight size={18}/></button><button className="icon-button" aria-label={t("الصفحة التالية")} disabled={page * 20 >= rows.data.total} onClick={() => setPage(page + 1)}><ChevronLeft size={18}/></button></div></div></>}
 </section>{selected !== null && <Details id={selected} onClose={() => setSelected(null)}/>}</>;
}
