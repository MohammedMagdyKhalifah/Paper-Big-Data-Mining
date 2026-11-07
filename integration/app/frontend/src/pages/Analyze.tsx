import ScreenshotAnalysis from '../components/ScreenshotAnalysis';
import { useLanguage } from '../i18n';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FileUp, Send, TextCursorInput, Download } from 'lucide-react';
import { api } from '../api';
import type { Complaint } from '../types';
import { ErrorBox, number, PageTitle, PredictionCard, useWorkspace } from '../components/common';
export default function Analyze() {
    const { t } = useLanguage();
    const { info } = useWorkspace();
    const [isDemo, setIsDemo] = useState(false);
    const [csvDemo, setCsvDemo] = useState(false);
    const [text, setText] = useState('');
    const [sourceApp, setSourceApp] = useState('');
    const [sourceId, setSourceId] = useState('');
    const [date, setDate] = useState('');
    const [validation, setValidation] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const client = useQueryClient();
    const refresh = () => { void client.invalidateQueries(); };
    const analyze = useMutation<{message:Complaint|null;duplicate:boolean},Error,unknown>({ mutationFn: (body: unknown) => info.mode==='real' ? api.analyzeP1(body) : api.analyze(body), onSuccess: refresh });
    const upload = useMutation({ mutationFn: (file: File) => api.import(file, csvDemo), onSuccess: refresh });
    const submit = (event: FormEvent) => { event.preventDefault(); if (!text.trim()) {
        setValidation("اكتب نص الشكوى أولًا");
        return;
    } setValidation(''); analyze.mutate({ text: text.trim(), source_app: sourceApp || null, source_id: sourceId || null, original_event_time: date || null, is_demo: isDemo }); };
    return <><PageTitle title={t("تحليل شكوى جديدة")} description={t("أدخل رسالة عربية أو استورد مجموعة رسائل. تُحفظ النتائج تلقائيًا للمراجعة والاستعراض.")}/>
 <div className="analyze-grid"><section className="panel"><div className="panel-heading"><h2><TextCursorInput size={19}/>{t(" إدخال نص")}</h2><span className="subtle-tag">{t("عربي / نص مختلط")}</span></div>
 <form onSubmit={submit}><label>{t("نص الرسالة")}<textarea aria-label={t("نص الرسالة")} placeholder={t("اكتب الشكوى هنا… مثل: رمز التحقق لا يصل عند تسجيل الدخول")} maxLength={20000} rows={7} dir="auto" lang="ar" value={text} onChange={e => { setText(e.target.value); setValidation(''); }}/></label><p className="helper char-count">{number(text.length)} / {number(20000)}{t(" حرف")}</p>
 <div className="form-grid"><label>{t("اسم التطبيق من بيانات المصدر ")}<span>{t("(اختياري)")}</span><input value={sourceApp} maxLength={200} onChange={e => setSourceApp(e.target.value)} placeholder={t("مثال: صحتي")}/></label><label>{t("معرّف المصدر ")}<span>{t("(اختياري)")}</span><input value={sourceId} maxLength={200} onChange={e => setSourceId(e.target.value)} placeholder={t("معرّف ثابت لمنع تكرار الرسالة")}/></label></div>
 <label>{t("تاريخ الرسالة الأصلي ")}<span>{t("(اختياري، بتوقيت الرياض)")}</span><input type="datetime-local" value={date} onChange={e => setDate(e.target.value)}/></label>
 <p className="helper">{t("اترك التاريخ فارغًا إذا لم يكن معروفًا. اسم التطبيق هنا بيانات مصدر وليس استخراجًا من النص.")}</p>
 {info.mode === 'real' && <label className="checkbox-label"><input type="checkbox" checked={isDemo} onChange={e => setIsDemo(e.target.checked)}/>{t("نص اصطناعي أو مخصص للاختبار (يُستبعد من البيانات الحقيقية)")}</label>}{validation && <p role="alert" className="field-error">{t(validation)}</p>}{analyze.error && <ErrorBox error={analyze.error}/>}
 <button className="primary-button" disabled={analyze.isPending}><Send size={17}/>{analyze.isPending ? t("جارٍ التحليل…") : t("تحليل وحفظ الرسالة")}</button></form>
 </section><aside className="panel import-panel"><div className="upload-icon"><FileUp size={25}/></div><h2>{t("استيراد ملف CSV")}</h2><p>{t("أضف مجموعة رسائل في خطوة واحدة، مع تقرير للصفوف المقبولة والمكررة والفاشلة.")}</p><div className="code-note" dir="ltr">text, source_id, source_app,<br />original_event_time</div><p className="helper">{t("text مطلوب • UTF-8 • حتى 10MB و5,000 صف")}</p>
 <label className="file-zone">{t("اختر ملف CSV")}<input aria-label={t("ملف CSV")} type="file" accept=".csv,text/csv" onChange={e => { setFile(e.target.files?.[0] || null); upload.reset(); }}/></label>
 {info.mode === 'real' && <label className="checkbox-label"><input type="checkbox" checked={csvDemo} onChange={e => setCsvDemo(e.target.checked)}/>{t("ملف يحتوي بيانات اصطناعية / اختبار")}</label>}
 <button className="secondary-button w-full" disabled={!file || upload.isPending} onClick={() => file && upload.mutate(file)}><FileUp size={16}/>{upload.isPending ? t("جارٍ الاستيراد…") : t("استيراد الرسائل")}</button>
 <a href="/demo.csv" download className="text-link demo-download"><Download size={15}/>{t(" تنزيل عينة اصطناعية DEMO")}</a>
 {upload.error && <ErrorBox error={upload.error}/>}{upload.data && <div className="import-result" role="status"><h3>{t("تقرير الاستيراد")}</h3><p>{t("مقبول: ")}{number(upload.data.accepted)}{t(" • مكرر: ")}{number(upload.data.duplicates)}{t(" • فاشل: ")}{number(upload.data.failed)}</p>{upload.data.stopped && <p className="field-error">{t("توقف الاستيراد: ")}{upload.data.integration_error}</p>}{upload.data.errors.length > 0 && <ul>{upload.data.errors.map(e => <li key={e.row}>{t("الصف ")}{number(e.row)}: {e.reason}</li>)}</ul>}</div>}
 </aside></div>
 {info.mode==='real'&&<ScreenshotAnalysis/>}
 {analyze.data?.message && <><div className="success-note" role="status">{analyze.data.duplicate ? t("هذه الرسالة موجودة بالفعل؛ لم يتضاعف العدد.") : t("تم حفظ الرسالة ونتيجة التحليل.")}</div><PredictionCard message={analyze.data.message}/></>}
 </>;
}
