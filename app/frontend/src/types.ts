export type Category='AUTH'|'AVAIL'|'PERF'|'TRANS'|'UX'|'OTHER'
export const categories: Record<Category,string>={AUTH:'الدخول والتحقق',AVAIL:'عدم الإتاحة',PERF:'البطء والتأخير',TRANS:'المعاملات والدفع',UX:'الواجهة والاستخدام',OTHER:'مشكلات أخرى'}
export interface Prediction {is_complaint:boolean; complaint_score:number|null;category:Category|null;category_score:number|null;needs_review:boolean;model_version:string}
export interface Correction {id:number;field_name:string;old_value:unknown;new_value:unknown;corrected_at:string}
export interface Complaint extends Prediction {id:number;source:string;source_id:string|null;source_app:string|null;original_event_time:string|null;imported_at:string;text_redacted:string;system_name:string|null;system_evidence:string;is_demo:boolean;original_prediction:Prediction;original_system_name:string|null;system_reviewed:boolean;corrections:Correction[]}
export interface ModelInfo {mode:'mock'|'real';model_version:string|null;observed_versions:string[];status:string;integration_error:string|null;categories:Category[];evaluation_available:boolean;evaluation_report:string|null;evaluation_model_version:string|null}
export interface Overview {no_review_required_messages:number;known_system_complaints:number;dated_complaints:number;sources:{source:string;messages:number;complaints:number}[];comparison:{date_from:string;date_to:string;previous_complaints:number;current_complaints:number;complaint_delta:number;complaint_change_ratio:number|null}|null;total_messages:number;complaints:number;complaint_ratio:number;needs_review:number;categories:{category:Category;count:number}[];uncategorized_complaints:number}
export interface SystemItem {name:string|null;count:number;share:number;categories:Partial<Record<Category|'UNCLASSIFIED',number>>}
export interface Systems {total_complaints:number;items:SystemItem[]}
export interface Trends {time_basis:string;interval:string;missing_event_time:number;points:{date:string;count:number}[]}
export interface Listing {items:Complaint[];total:number;page:number;page_size:number}
export interface ImportResult {accepted:number;duplicates:number;failed:number;processed:number;errors:{row:number;reason:string}[];stopped:boolean;integration_error:string|null}
export interface Review {is_complaint:boolean;category:Category|null;system_name:string|null;needs_review:boolean}
export type Filters=Record<string,string>
