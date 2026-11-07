import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {MemoryRouter} from 'react-router-dom'
import {vi,beforeEach,describe,it,expect} from 'vitest'
import App from '../App'
import {ReviewEditor} from '../pages/Explorer'
import {PredictionCard,number,percent,stamp} from '../components/common'
import {api} from '../api'
import type {Complaint} from '../types'
// Snapshot of Claude's source card; Backend checks the live report byte-for-byte.
import a4ModelCard from './fixtures/a4_model_card.md?raw'
vi.mock('../api',()=>({api:{info:vi.fn(),analyze:vi.fn(),analyzeP1:vi.fn(),extractImage:vi.fn(),import:vi.fn(),review:vi.fn(),overview:vi.fn(),trends:vi.fn(),systems:vi.fn(),list:vi.fn(),detail:vi.fn()}}))
const message:Complaint={id:1,text_redacted:'التطبيق بطيء',source:'text',source_id:null,source_app:null,original_event_time:null,imported_at:'2026-10-29T12:00:00Z',is_complaint:true,category:'PERF',complaint_score:null,category_score:null,needs_review:true,model_version:'mock-v1',system_name:null,system_evidence:'unknown',is_demo:true,original_system_name:null,system_reviewed:false,corrections:[],original_prediction:{is_complaint:true,category:'PERF',complaint_score:null,category_score:null,needs_review:true,model_version:'mock-v1'}}
function wrapper(element:React.ReactNode){const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}});return render(<QueryClientProvider client={client}>{element}</QueryClientProvider>)}
function app(path='/analyze'){return wrapper(<MemoryRouter initialEntries={[path]}><App/></MemoryRouter>)}
// Observed local tfidf-baseline-v1 output, not an accuracy assertion or ML stub.
const realMessage:Complaint={...message,is_demo:false,model_version:'tfidf-baseline-v1',complaint_score:0.9045,category_score:0.4743,original_prediction:{...message.original_prediction,model_version:'tfidf-baseline-v1',complaint_score:0.9045,category_score:0.4743}}
function realInfo(){vi.mocked(api.info).mockResolvedValue({mode:'real',model_version:'tfidf-baseline-v1',observed_versions:[],status:'verified',integration_error:null,categories:['AUTH','AVAIL','PERF','TRANS','UX','OTHER'],evaluation_available:false,evaluation_report:null,evaluation_model_version:null})}
beforeEach(()=>{
 vi.clearAllMocks()
 localStorage.clear();document.documentElement.lang="ar";document.documentElement.dir="rtl"
 vi.mocked(api.info).mockResolvedValue({mode:'mock',model_version:'mock-v1',observed_versions:[],status:'mock',integration_error:null,categories:['AUTH','AVAIL','PERF','TRANS','UX','OTHER'],evaluation_available:false,evaluation_report:null,evaluation_model_version:null})
 vi.mocked(api.systems).mockResolvedValue({items:[],total_complaints:0})
})
describe('Arabic P0 interface',()=>{
 it('shows a permanent Mock banner and rejects blank text',async()=>{
  app();await screen.findByText('وضع تجريبي — DEMO / MOCK')
  await userEvent.click(screen.getByRole('button',{name:'تحليل وحفظ الرسالة'}))
  expect(screen.getByRole('alert')).toHaveTextContent('اكتب نص الشكوى أولًا')
  expect(api.analyze).not.toHaveBeenCalled()
 })
 it('sends a complaint and displays missing scores without inventing values',async()=>{
  vi.mocked(api.analyze).mockResolvedValue({message,duplicate:false});app()
  await userEvent.type(await screen.findByLabelText('نص الرسالة'),'التطبيق بطيء')
  await userEvent.click(screen.getByRole('button',{name:'تحليل وحفظ الرسالة'}))
  await screen.findByText('تم حفظ الرسالة ونتيجة التحليل.')
  expect(api.analyze).toHaveBeenCalledWith({text:'التطبيق بطيء',source_id:null,source_app:null,original_event_time:null,is_demo:false})
  expect(screen.getAllByText('غير متاحة')).toHaveLength(2)
  expect(screen.getByText('البطء والتأخير')).toBeInTheDocument()
 })
 it('reports duplicates clearly',async()=>{
  vi.mocked(api.analyze).mockResolvedValue({message,duplicate:true});app()
  await userEvent.type(await screen.findByLabelText('نص الرسالة'),'نص')
  await userEvent.click(screen.getByRole('button',{name:'تحليل وحفظ الرسالة'}))
  expect(await screen.findByText('هذه الرسالة موجودة بالفعل؛ لم يتضاعف العدد.')).toBeInTheDocument()
 })
 it('imports CSV and shows failed row reasons',async()=>{
  vi.mocked(api.import).mockResolvedValue({accepted:1,duplicates:1,failed:1,processed:3,errors:[{row:4,reason:'نص فارغ'}],stopped:false,integration_error:null});app()
  const input=await screen.findByLabelText('ملف CSV')
  await userEvent.upload(input,new File(['text\nنص'],'demo.csv',{type:'text/csv'}))
  await userEvent.click(screen.getByRole('button',{name:'استيراد الرسائل'}))
  expect(await screen.findByText('تقرير الاستيراد')).toBeInTheDocument()
  expect(screen.getByText(/نص فارغ/)).toBeInTheDocument()
  expect(api.import).toHaveBeenCalledOnce()
 })
 it('persists human corrections and invalidates cached data',async()=>{
  vi.mocked(api.review).mockResolvedValue({...message,category:'AUTH',needs_review:false})
  wrapper(<ReviewEditor message={message} onSaved={()=>{}}/>)
  await userEvent.selectOptions(screen.getByLabelText('التصنيف المصحح'),'AUTH')
  await userEvent.type(screen.getByLabelText('اسم النظام المصحح'),'منصة ألف')
  await userEvent.click(screen.getByRole('button',{name:'حفظ التصحيح'}))
  expect(await screen.findByRole('status')).toHaveTextContent('تم حفظ التصحيح')
  expect(api.review).toHaveBeenCalledWith(1,{is_complaint:true,category:'AUTH',system_name:'منصة ألف',needs_review:false})
 })
 it('does not fabricate evaluation results',async()=>{
  app('/model');expect(await screen.findByText('نتائج التقييم غير متاحة')).toBeInTheDocument()
 })
 it('shows connection errors and a retry action',async()=>{
  vi.mocked(api.info).mockRejectedValue(new Error('الخادم غير متاح'));app()
  expect(await screen.findByRole('alert')).toHaveTextContent('الخادم غير متاح')
  expect(screen.getByRole('button',{name:'إعادة الاتصال'})).toBeInTheDocument()
 })
 it('uses the demo scope explicitly for dashboard requests',async()=>{
  vi.mocked(api.overview).mockResolvedValue({total_messages:0,complaints:0,complaint_ratio:0,needs_review:0,categories:[],uncategorized_complaints:0,no_review_required_messages:0,known_system_complaints:0,dated_complaints:0,sources:[],comparison:null})
  vi.mocked(api.trends).mockResolvedValue({time_basis:'event',interval:'day',missing_event_time:0,points:[]})
  app('/')
  // Wait for the actual lazy route after the asynchronous model-info query.
  // dynamicImportSettled alone can run before React starts this import.
  await screen.findByRole('heading',{name:'تحليل عربي، رؤية أوضح.'},{timeout:15000})
  await waitFor(()=>expect(api.overview).toHaveBeenCalledWith(expect.objectContaining({data_scope:'demo',time_basis:'event'})))
  await userEvent.selectOptions(screen.getByLabelText('نطاق البيانات'),'real')
  await waitFor(()=>expect(api.overview).toHaveBeenCalledWith(expect.objectContaining({data_scope:'real'})))
 },20000)
})

describe('Bilingual workspace',()=>{
 it('switches navigation and forms to English, persists language and preserves Arabic input/results',async()=>{
  vi.mocked(api.analyze).mockResolvedValue({message,duplicate:false})
  const rendered=app()
  const original=await screen.findByLabelText('نص الرسالة')
  await userEvent.type(original,'التطبيق بطيء')
  await userEvent.click(screen.getByRole('button',{name:'Browse in English'}))
  expect(document.documentElement).toHaveAttribute('lang','en')
  expect(document.documentElement).toHaveAttribute('dir','ltr')
  expect(localStorage.getItem('marsad.language')).toBe('en')
  expect(screen.getByLabelText('Message text')).toHaveValue('التطبيق بطيء')
  await userEvent.click(screen.getByRole('button',{name:'Analyze & save'}))
  expect(await screen.findByText('Message and analysis saved.')).toBeInTheDocument()
  expect(screen.getByText('البطء والتأخير')).toHaveAttribute('dir','rtl')
  expect(screen.getByRole('link',{name:/Complaints explorer/})).toBeInTheDocument()
  rendered.unmount();app('/model')
  expect(await screen.findByText('Evaluation results are not available')).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Browse in English'})).toHaveAttribute('aria-pressed','true')
  await userEvent.click(screen.getByRole('button',{name:'تصفح بالعربية'}))
  expect(document.documentElement).toHaveAttribute('dir','rtl')
  expect(screen.getByRole('heading',{name:'معلومات النموذج'})).toBeInTheDocument()
 })
 it('opens analytics drilldowns with the correct category and system filter',async()=>{
  vi.mocked(api.list).mockResolvedValue({items:[message],total:1,page:1,page_size:20})
  app('/complaints?category=PERF&system=نظام%20ألف&is_complaint=true')
  await waitFor(()=>expect(api.list).toHaveBeenCalledWith(expect.objectContaining({category:'PERF',system:'نظام ألف',is_complaint:'true',data_scope:'demo'})))
  expect(screen.getByRole('combobox',{name:'فلتر الفئة'})).toHaveValue('PERF')
 })
 it('renders the system matrix and links counts to the underlying complaints',async()=>{
  vi.mocked(api.systems).mockResolvedValue({total_complaints:3,items:[{name:'نظام ألف',count:3,share:1,categories:{PERF:3}}]})
  app('/systems')
  const link=await screen.findByRole('link',{name:'نظام ألف · البطء والتأخير: 3'})
  expect(link).toHaveAttribute('href','/complaints?is_complaint=true&system=%D9%86%D8%B8%D8%A7%D9%85%20%D8%A3%D9%84%D9%81&category=PERF')
  await userEvent.click(screen.getByRole('button',{name:'عرض بطاقات'}))
  expect(screen.queryByRole('table')).not.toBeInTheDocument()
  expect(screen.getByText('البطء والتأخير')).toBeInTheDocument()
 })
})

it('offers actual import activity when publication dates are missing',async()=>{
 vi.mocked(api.overview).mockResolvedValue({total_messages:1,complaints:1,complaint_ratio:1,needs_review:1,categories:[{category:'PERF',count:1}],uncategorized_complaints:0,no_review_required_messages:0,known_system_complaints:0,dated_complaints:0,sources:[{source:'text',messages:1,complaints:1}],comparison:null})
 vi.mocked(api.trends).mockResolvedValue({time_basis:'event',interval:'day',missing_event_time:1,points:[]})
 app('/')
 await userEvent.click(await screen.findByRole('button',{name:'عرض نشاط الاستيراد'}))
 await waitFor(()=>expect(api.trends).toHaveBeenCalledWith(expect.objectContaining({time_basis:'import'})))
})

describe('Real model presentation',()=>{
 it('shows the actual version and scores through the same Analyze page',async()=>{
  realInfo();vi.mocked(api.analyzeP1).mockResolvedValue({message:realMessage,duplicate:false,analysis:{} as never});app()
  await userEvent.type(await screen.findByLabelText('نص الرسالة'),'التطبيق بطيء')
  await userEvent.click(screen.getByRole('button',{name:'تحليل وحفظ الرسالة'}))
  expect(await screen.findByText('نموذج حقيقي')).toBeInTheDocument()
  expect(screen.getByText('0.905')).toBeInTheDocument()
  expect(screen.queryByText('وضع تجريبي — DEMO / MOCK')).not.toBeInTheDocument()
  expect(api.analyzeP1).toHaveBeenCalledWith(expect.objectContaining({is_demo:false}))
 })
 it('defaults real dashboard queries to real records',async()=>{
  realInfo()
  vi.mocked(api.overview).mockResolvedValue({total_messages:0,complaints:0,complaint_ratio:0,needs_review:0,categories:[],uncategorized_complaints:0,no_review_required_messages:0,known_system_complaints:0,dated_complaints:0,sources:[],comparison:null})
  vi.mocked(api.trends).mockResolvedValue({time_basis:'event',interval:'day',missing_event_time:0,points:[]})
  app('/')
  await waitFor(()=>expect(api.overview).toHaveBeenCalledWith(expect.objectContaining({data_scope:'real'})))
  expect(api.overview).not.toHaveBeenCalledWith(expect.objectContaining({data_scope:'demo'}))
 })
 it('distinguishes synthetic real output from Mock and does not claim a human review',()=>{
  wrapper(<PredictionCard message={{...realMessage,is_demo:true,needs_review:false}}/>)
  expect(screen.getByText('DEMO')).toBeInTheDocument()
  expect(screen.queryByText('DEMO / MOCK')).not.toBeInTheDocument()
  expect(screen.getByText('لا تتطلب مراجعة إضافية')).toBeInTheDocument()
  expect(screen.queryByText('مكتملة')).not.toBeInTheDocument()
 })
})

it.each(['ar','en'])('uses English digits for counts, percentages, scores and dates in %s',async(language)=>{
 localStorage.setItem('marsad.language',language)
 realInfo();vi.mocked(api.analyzeP1).mockResolvedValue({message:realMessage,duplicate:false,analysis:{} as never});app()
 await userEvent.type(await screen.findByLabelText(language==='ar'?'نص الرسالة':'Message text'),'التطبيق بطيء')
 await userEvent.click(screen.getByRole('button',{name:language==='ar'?'تحليل وحفظ الرسالة':'Analyze & save'}))
 expect(await screen.findByText('0.905')).toBeInTheDocument()
 expect(screen.getByText('0.474')).toBeInTheDocument()
 expect(screen.getByText(/20,000/)).toBeInTheDocument()
 expect(number(1234)).toBe('1,234')
 expect(percent(.286)).toBe('28.6%')
 const displayedDate=stamp('2026-10-29T21:30:00Z')
 expect(displayedDate).toContain('2026')
 expect(displayedDate).toContain('12:30') // Riyadh time and Gregorian calendar preserved.
 expect(displayedDate).not.toMatch(/[\u0660-\u0669\u06f0-\u06f9]/)
 expect(stamp(null)).toBe('غير متاح')
 expect(document.documentElement).toHaveAttribute('dir',language==='ar'?'rtl':'ltr')
})

it('shows the A4 version and original evaluation with each dataset kept separate',async()=>{
 vi.mocked(api.info).mockResolvedValue({mode:'real',model_version:'a4-marbert-v1',observed_versions:['tfidf-baseline-v1','a4-marbert-v1'],status:'verified',integration_error:null,categories:['AUTH','AVAIL','PERF','TRANS','UX','OTHER'],evaluation_available:true,evaluation_report:a4ModelCard,evaluation_model_version:'a4-marbert-v1'})
 app('/model')
 const report=await screen.findByText(/# A4 model card/)
 expect(report.textContent).toBe(a4ModelCard)
 for(const label of ['holdout_all','holdout_random','holdout_enriched','holdout_codeswitch','external_aura_proxy','v1_test_NOT_BLIND','NON-BLIND','AI-assisted'])expect(report).toHaveTextContent(label)
 expect(report).toHaveTextContent('0.6896')
 expect(screen.getAllByText('a4-marbert-v1').length).toBeGreaterThan(0)
 expect(screen.queryByText('وضع تجريبي — DEMO / MOCK')).not.toBeInTheDocument()
})
