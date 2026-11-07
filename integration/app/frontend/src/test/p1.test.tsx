import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {vi,beforeEach,it,expect} from 'vitest'
import ScreenshotAnalysis from '../components/ScreenshotAnalysis'
import P1Evidence from '../components/P1Evidence'
import {LanguageProvider} from '../i18n'
import {api} from '../api'
import type {Complaint,OCRDraft,P1Analysis} from '../types'
// Recorded real local pipeline output on a synthetic fixture; UI rendering only.
import recorded from './fixtures/p1_analysis.json'
vi.mock('../api',()=>({api:{extractImage:vi.fn(),analyzeP1:vi.fn()}}))
const analysis=recorded.image as P1Analysis
const draft:OCRDraft={draft_id:'00000000-0000-4000-8000-000000000001',expires_at:'2026-11-01T10:00:00Z',ocr:analysis.ocr!}
const message:Complaint={...analysis.prediction!,id:2,source:'image',source_id:null,source_app:null,original_event_time:null,imported_at:'2026-10-31T00:00:00Z',text_redacted:analysis.input.classified_text!,system_name:null,system_evidence:'unknown',is_demo:true,original_prediction:analysis.prediction!,original_system_name:null,system_reviewed:false,corrections:[],p1_analysis:analysis}
function show(element=<ScreenshotAnalysis/>){const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}});return render(<LanguageProvider><QueryClientProvider client={client}>{element}</QueryClientProvider></LanguageProvider>)}
beforeEach(()=>{vi.resetAllMocks();localStorage.clear();vi.mocked(api.extractImage).mockResolvedValue(draft);vi.mocked(api.analyzeP1).mockResolvedValue({message,duplicate:false,analysis})})
async function upload(){await userEvent.upload(screen.getByLabelText('لقطة الشاشة'),new File(['image bytes'],'screen.png',{type:'image/png'}));await userEvent.click(screen.getByRole('button',{name:'استخراج النص من الصورة'}));await screen.findByLabelText('نص OCR القابل للتصحيح')}
it('previews and extracts without auto-classifying; explicitly confirms corrected text',async()=>{
 show();await upload();expect(screen.getByAltText('معاينة لقطة الشاشة')).toHaveAttribute('src','blob:preview-test')
 expect(api.analyzeP1).not.toHaveBeenCalled();expect(screen.getByLabelText('نص OCR القابل للتصحيح')).toHaveValue(draft.ocr.text)
 await userEvent.clear(screen.getByLabelText('نص OCR القابل للتصحيح'));await userEvent.type(screen.getByLabelText('نص OCR القابل للتصحيح'),'تطبيق نفاذ لا يفتح')
 await userEvent.type(screen.getByLabelText('وصفك للمشكلة (اختياري)'),'من أمس أحاول الدخول')
 await userEvent.click(screen.getByLabelText('صورة اصطناعية أو مخصصة للاختبار (تُستبعد من البيانات الحقيقية)'))
 await userEvent.click(screen.getByRole('button',{name:'تأكيد النص وتحليله وحفظه'}))
 expect(api.analyzeP1).toHaveBeenCalledWith({draft_id:draft.draft_id,corrected_text:'تطبيق نفاذ لا يفتح',text:'من أمس أحاول الدخول',is_demo:true})
 expect(await screen.findByText('تم حفظ الرسالة ونتيجة التحليل.')).toBeInTheDocument()
 expect(screen.getByText(/الصورة تعرض إشارة خطأ/)).toBeInTheDocument()
})
it('invalidates OCR approval when a different image is selected',async()=>{
 show();await upload();await userEvent.upload(screen.getByLabelText('لقطة الشاشة'),new File(['new'],'second.jpg',{type:'image/jpeg'}))
 expect(screen.queryByLabelText('نص OCR القابل للتصحيح')).not.toBeInTheDocument()
 expect(screen.queryByRole('button',{name:'تأكيد النص وتحليله وحفظه'})).not.toBeInTheDocument();expect(api.analyzeP1).not.toHaveBeenCalled()
})
it('shows extraction failure and never enables classification',async()=>{
 vi.mocked(api.extractImage).mockRejectedValue(new Error('OCR unavailable'));show()
 await userEvent.upload(screen.getByLabelText('لقطة الشاشة'),new File(['x'],'x.png',{type:'image/png'}));await userEvent.click(screen.getByRole('button',{name:'استخراج النص من الصورة'}))
 expect(await screen.findByRole('alert')).toHaveTextContent('OCR unavailable');expect(screen.queryByLabelText('نص OCR القابل للتصحيح')).not.toBeInTheDocument()
})
it('does not restore original OCR when the user deletes the corrected text',async()=>{
 show();await upload();await userEvent.clear(screen.getByLabelText('نص OCR القابل للتصحيح'));await userEvent.click(screen.getByRole('button',{name:'تأكيد النص وتحليله وحفظه'}))
 expect(screen.getByRole('alert')).toHaveTextContent('نص OCR المصحح فارغ');expect(api.analyzeP1).not.toHaveBeenCalled()
})
it('handles empty OCR without inventing a prediction',async()=>{
 vi.mocked(api.extractImage).mockResolvedValue({...draft,ocr:{...draft.ocr,status:'empty',text:'',lines:[],mean_confidence:null}});show();await upload()
 await userEvent.click(screen.getByRole('button',{name:'تأكيد النص وتحليله وحفظه'}));expect(api.analyzeP1).not.toHaveBeenCalled()
 expect(screen.getByRole('alert')).toHaveTextContent('لم يظهر نص')
})
it('offers English navigation and keeps Arabic OCR/model content intact',async()=>{
 localStorage.setItem('marsad.language','en');show()
 await userEvent.upload(screen.getByLabelText('Screenshot file'),new File(['x'],'x.jpg',{type:'image/jpeg'}));await userEvent.click(screen.getByRole('button',{name:'Extract text from image'}))
 expect(await screen.findByLabelText('Editable OCR text')).toHaveValue(draft.ocr.text);expect(document.documentElement).toHaveAttribute('dir','ltr')
})
it('keeps ambiguous names separate from confirmed names',()=>{
 show(<P1Evidence analysis={analysis}/>);expect(screen.getByText('أسماء محتملة تحتاج تأكيدًا بشريًا')).toBeInTheDocument()
 expect(screen.getByText('لم يُحدد نظام مؤكد من النص.')).toBeInTheDocument();expect(screen.getByText(/ذكر النظام لا يثبت/)).toBeInTheDocument()
})
it('blocks pending duplicate extraction and analysis submissions',async()=>{
 let resolve:(d:OCRDraft)=>void=()=>{};vi.mocked(api.extractImage).mockReturnValue(new Promise(r=>{resolve=r}));show()
 await userEvent.upload(screen.getByLabelText('لقطة الشاشة'),new File(['x'],'x.png',{type:'image/png'}));await userEvent.click(screen.getByRole('button',{name:'استخراج النص من الصورة'}))
 expect(screen.getByRole('button',{name:'جارٍ استخراج النص…'})).toBeDisabled();expect(screen.getByLabelText('لقطة الشاشة')).toBeDisabled()
 resolve(draft);await waitFor(()=>expect(screen.getByLabelText('لقطة الشاشة')).toBeEnabled())
})
