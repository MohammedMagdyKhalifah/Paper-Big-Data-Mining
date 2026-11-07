import type {Complaint,Filters,ImportResult,Listing,ModelInfo,Overview,Review,Systems,Trends} from './types'
export async function request<T>(path:string,options?:RequestInit):Promise<T>{
 let response:Response
 try{response=await fetch(`/api${path}`,options)}catch{throw new Error('تعذر الاتصال بالخادم. تأكد من تشغيل FastAPI محليًا.')}
 if(!response.ok){
  let message=`تعذر إتمام الطلب (${response.status})`
  try {const data=await response.json();message=typeof data.detail==='string'?data.detail:Array.isArray(data.detail)?data.detail.map((e:{msg:string})=>e.msg).join('؛ '):message}catch{/* Keep status message. */}
  throw new Error(message)
 }
 return response.json() as Promise<T>
}
export function qs(filters:Filters){return new URLSearchParams(Object.entries(filters).filter(([,v])=>v!=='')).toString()}
export const api={
 info:()=>request<ModelInfo>('/models/info'),
 overview:(f:Filters)=>request<Overview>(`/dashboard/overview?${qs(f)}`),
 systems:(f:Filters)=>request<Systems>(`/systems?${qs(f)}`),
 trends:(f:Filters)=>request<Trends>(`/dashboard/trends?${qs(f)}`),
 list:(f:Filters)=>request<Listing>(`/complaints?${qs(f)}`),
 detail:(id:number)=>request<Complaint>(`/complaints/${id}`),
 analyze:(body:unknown)=>request<{message:Complaint;duplicate:boolean}>('/complaints/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
 import:(file:File,isDemo=false)=>{const body=new FormData();body.append('file',file);body.append('is_demo',String(isDemo));return request<ImportResult>('/complaints/import',{method:'POST',body})},
 review:(id:number,body:Review)=>request<Complaint>(`/complaints/${id}/review`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
}
