import { useLanguage } from '../i18n';
import { Cpu, FileCheck2, ShieldCheck } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';
import { categories } from '../types';
import { PageTitle, useWorkspace } from '../components/common';
export default function Model() {
    const { t } = useLanguage();
    const { info: initial } = useWorkspace();
    const { data } = useQuery({ queryKey: ['model'], queryFn: api.info });
    const info = data || initial;
    return <><PageTitle title={t("معلومات النموذج")} description={t("حالة التكامل ونسخة النموذج وحدود تفسير النتائج في مكان واحد.")}/>
 <div className="model-grid"><section className="panel"><div className="panel-heading"><h2><Cpu size={20}/>{t(" محرك التحليل")}</h2><span className={info.mode === 'mock' ? 'mode-tag' : 'real-tag'}>{info.mode === 'mock' ? 'DEMO / MOCK' : 'REAL'}</span></div><dl className="facts"><div><dt>{t("نوع المحرك")}</dt><dd>{info.mode === 'mock' ? t("Mock ثابت للاختبار") : t("نموذج Claude المحلي")}</dd></div><div><dt>{t("نسخة النموذج")}</dt><dd dir="ltr">{info.model_version || t("لم تُرصد بعد")}</dd></div><div><dt>{t("حالة التكامل")}</dt><dd>{({ mock: t("تجريبي"), verified: t("تم استدعاؤه بنجاح"), not_tested: t("لم يُختبر بعد"), error: t("خطأ تكامل") } as Record<string, string>)[info.status] || info.status}</dd></div><div><dt>{t("نسخ مرصودة في السجلات")}</dt><dd>{info.observed_versions.join(t("، ")) || t("لا توجد سجلات")}</dd></div></dl>
 {info.integration_error && <div className="error-box">{info.integration_error}</div>}<div className="info-strip">{info.mode === 'mock' ? t("النتائج ثابتة ومصطنعة لاختبار تدفق التطبيق. ليست استدلالًا حقيقيًا أو نتائج بحثية.") : t("يستدعي التطبيق ml.infer.predict_text محليًا، ولا يقوم بتدريب النموذج.")}</div></section>
 <section className="panel"><h2><ShieldCheck size={19}/>{t(" حدود الاستخدام")}</h2><ul className="readable-list"><li>{t("التصنيف يصف أعراضًا وردت في الرسالة، ولا يثبت سبب العطل.")}</li><li>{t("اسم النظام مصدره بيانات الرسالة أو المراجعة البشرية.")}</li><li>{t("التصحيحات لا تغيّر أوزان النموذج أو توقعاته الأصلية.")}</li><li>{t("الدرجة غير المتاحة لا تعني صفرًا، ولا تمثل دقة مقاسة.")}</li></ul></section></div>
 <section className="panel"><div className="panel-heading"><h2>{t("الفئات المدعومة")}</h2><span className="subtle-tag">{t("تصنيف رئيسي واحد")}</span></div><div className="taxonomy">{Object.entries(categories).map(([code, label]) => <div key={code}><code>{code}</code><span>{label}</span></div>)}</div></section>
 <section className="panel"><div className="panel-heading"><h2><FileCheck2 size={19}/>{t(" نتائج التقييم البحثي")}</h2><span className="subtle-tag">{t("تقارير المصدر فقط")}</span></div>{info.evaluation_available ? <><p className="helper">{t("تقرير محلي لنسخة ")}{info.evaluation_model_version}{t("، دون تعديل أو توليد أرقام من التطبيق.")}</p><pre className="evaluation-report" dir="auto">{info.evaluation_report}</pre></> : <div className="evaluation-empty"><FileCheck2 size={28}/><h3>{t("نتائج التقييم غير متاحة")}</h3><p>{t("ستُعرض عند توفير تقرير حقيقي مرتبط بنسخة الموديل المستخدمة. لا توجد درجات علمية لبيانات Mock.")}</p></div>}</section></>;
}
