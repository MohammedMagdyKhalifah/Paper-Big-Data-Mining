import {createContext,useContext,useLayoutEffect,useState} from 'react'
import type {ReactNode} from 'react'
import {english} from './translations'
export type Language='ar'|'en'
export const LANGUAGE_KEY='marsad.language'
function storedLanguage():Language{try{return localStorage.getItem(LANGUAGE_KEY)==='en'?'en':'ar'}catch{return 'ar'}}
function lookup(text:string,language:Language){
 const key=text.trim();const translated=language==='en'?(english[key]??key):key
 return `${/^\s/.test(text)?' ':''}${translated}${/\s$/.test(text)?' ':''}`
}
const LanguageContext=createContext<{language:Language;setLanguage:(language:Language)=>void;t:(text:string)=>string}>({language:'ar',setLanguage:()=>{},t:text=>lookup(text,'ar')})
export function LanguageProvider({children}:{children:ReactNode}){
 const [language,setLanguage]=useState<Language>(storedLanguage)
 useLayoutEffect(()=>{document.documentElement.lang=language;document.documentElement.dir=language==='ar'?'rtl':'ltr';document.title=language==='ar'?'مرصد | تحليل شكاوى الخدمات الرقمية':'Marsad | Digital Service Complaint Analytics';try{localStorage.setItem(LANGUAGE_KEY,language)}catch{/* Private browsing may restrict storage. */}},[language])
 return <LanguageContext.Provider value={{language,setLanguage,t:text=>lookup(text,language)}}>{children}</LanguageContext.Provider>
}
export const useLanguage=()=>useContext(LanguageContext)
