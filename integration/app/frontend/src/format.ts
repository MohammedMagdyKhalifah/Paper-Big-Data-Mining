// Use English digits in either UI language; Arabic content and Riyadh time stay intact.
export const number=(n:number)=>new Intl.NumberFormat('en-US').format(n)
export const percent=(n:number)=>new Intl.NumberFormat('en-US',{style:'percent',maximumFractionDigits:1}).format(n)
export const stamp=(s:string|null)=>s?new Intl.DateTimeFormat('ar-SA',{numberingSystem:'latn',dateStyle:'medium',timeStyle:'short',calendar:'gregory',timeZone:'Asia/Riyadh'}).format(new Date(s)):'غير متاح'
export const score=(n:number|null)=>n===null?'غير متاحة':number(n)
