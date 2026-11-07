import {lazy,Suspense,useEffect,useState} from 'react'
import {NavLink,Route,Routes,useLocation} from 'react-router-dom'
import {useQuery} from '@tanstack/react-query'
import {Activity,ArrowUpLeft,ChartColumnIncreasing,ClipboardCheck,Cpu,LayoutDashboard,Layers3,Menu,MessageSquareText,PanelRightClose,Search,Server,FlaskConical,Globe2,ArrowRight} from 'lucide-react'
import {api} from './api'
import {ErrorBox,FilterBar,Loading,Workspace} from './components/common'
import {LanguageProvider,useLanguage} from './i18n'
import Analyze from './pages/Analyze'
import Explorer from './pages/Explorer'
import Systems from './pages/Systems'
import Model from './pages/Model'
import type {Filters} from './types'
const Dashboard=lazy(()=>import('./pages/Dashboard'))
const nav=[{to:'/',label:'لوحة المؤشرات',icon:LayoutDashboard},{to:'/analyze',label:'تحليل شكوى',icon:MessageSquareText},{to:'/complaints',label:'مستكشف الشكاوى',icon:Search},{to:'/systems',label:'تحليلات الأنظمة',icon:Layers3},{to:'/review',label:'طابور المراجعة',icon:ClipboardCheck},{to:'/model',label:'معلومات النموذج',icon:Cpu}]
function AppContent(){
 const {language,setLanguage,t}=useLanguage()
 const model=useQuery({queryKey:['model'],queryFn:api.info})
 const [filters,setFilters]=useState<Filters>({data_scope:'real',source:'',time_basis:'event',date_from:'',date_to:''})
 const [initialized,setInitialized]=useState(false)
 const [mobile,setMobile]=useState(false)
 const location=useLocation()
 useEffect(()=>{if(model.data&&!initialized){setFilters(f=>({...f,data_scope:model.data.mode==='mock'?'demo':'real'}));setInitialized(true)}},[model.data,initialized])
 useEffect(()=>{setMobile(false);window.scrollTo({top:0,left:0,behavior:'instant'})},[location.pathname])
 return <div className="app-shell">
  <aside className={`sidebar ${mobile?'open':''}`}>
   <div className="brand"><div className="brand-mark"><ChartColumnIncreasing size={25}/></div><div><strong>{t('مرصد')}<span>{t('الشكاوى الرقمية')}</span></strong></div><button className="mobile-close icon-button" aria-label={t('إغلاق القائمة')} onClick={()=>setMobile(false)}><PanelRightClose/></button></div>
   <div className="nav-section-label">{t('مساحة التحليل')}</div>
   <nav aria-label={t('التنقل الرئيسي')}>{nav.map(({to,label,icon:Icon},index)=><NavLink key={to} to={to} end={to==='/'} className={({isActive})=>isActive?'active':''}><Icon size={19}/><span>{t(label)}</span><span className="nav-index">0{index+1}</span></NavLink>)}</nav>
   <div className="sidebar-bottom"><div className="research-card"><div className="research-card-label"><FlaskConical size={17}/><span>{t('مشروع بحثي')}</span></div><strong>{language==='ar'?'كل رسالة تحمل إشارة.':'Every message holds a signal.'}</strong><p>{t('تحليل شكاوى الخدمات الرقمية باللغة العربية')}</p><NavLink to="/model">{t('معلومات النموذج')}<ArrowUpLeft size={14}/></NavLink></div><div className="local-indicator"><span/>{t('تشغيل محلي')}<Server size={14}/></div></div>
  </aside>
  {mobile&&<button className="sidebar-backdrop" aria-label={t('إغلاق التنقل')} onClick={()=>setMobile(false)}/>}
  <main className="main-content">
   <div className="topbar"><div className="breadcrumb"><button className="mobile-menu icon-button" aria-label={t('فتح القائمة')} aria-expanded={mobile} onClick={()=>setMobile(true)}><Menu/></button><span>{t('مساحة البحث')}</span><span className="breadcrumb-separator">/</span><strong>{t(nav.find(n=>n.to===location.pathname)?.label||'الصفحة')}</strong></div>
   <div className="topbar-meta"><div className="language-switch" role="group" aria-label={t('اللغة')}><Globe2 size={15}/><button className={language==='ar'?'selected':''} aria-label="تصفح بالعربية" aria-pressed={language==='ar'} onClick={()=>setLanguage('ar')}>عربي</button><button className={language==='en'?'selected':''} aria-label="Browse in English" aria-pressed={language==='en'} onClick={()=>setLanguage('en')}>EN</button></div><span className="local-tag"><span/>{t('محلي')}</span><span className="avatar">M</span></div></div>
   <div className="content-wrap">
    {model.error?<><ErrorBox error={model.error}/><button className="secondary-button" onClick={()=>void model.refetch()}>{t('إعادة الاتصال')}</button></>:!model.data||!initialized?<Loading/>:<Workspace.Provider value={{filters,setFilters,info:model.data}}>
    {model.data.mode==='mock'?<div className="demo-banner"><FlaskConical size={17}/><div><strong>{t('وضع تجريبي — DEMO / MOCK')}</strong><span>{t('النتائج غير حقيقية، ولا تدخل ضمن النتائج البحثية.')}</span></div><code>{model.data.model_version||'mock-v1'}</code></div>:<div className="real-banner"><Activity size={18}/>{t('وضع النموذج الحقيقي •')} {model.data.model_version||t('الاستدلال لم يُختبر بعد')}</div>}
    {['/','/complaints','/review','/systems'].includes(location.pathname)&&<FilterBar/>}
    <Suspense fallback={<Loading/>}><Routes><Route path="/" element={<Dashboard/>}/><Route path="/analyze" element={<Analyze/>}/><Route path="/complaints" element={<Explorer/>}/><Route path="/review" element={<Explorer reviewOnly/>}/><Route path="/systems" element={<Systems/>}/><Route path="/model" element={<Model/>}/><Route path="*" element={<div className="panel"><h1>{t('الصفحة غير موجودة')}</h1><NavLink className="text-link" to="/">{t('العودة إلى لوحة المؤشرات')}<ArrowRight size={16}/></NavLink></div>}/></Routes></Suspense>
    </Workspace.Provider>}
    <footer className="footer"><span>{t('مرصد الشكاوى الرقمية')} <b>© 2026</b></span><span>{t('الأعراض الواردة في الشكاوى لا تثبت أعطال الأنظمة.')}</span></footer>
   </div>
  </main>
 </div>
}
export default function App(){return <LanguageProvider><AppContent/></LanguageProvider>}
