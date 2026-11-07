export type Category='AUTH'|'AVAIL'|'PERF'|'TRANS'|'UX'|'OTHER'
export const categories: Record<Category,string>={AUTH:'الدخول والتحقق',AVAIL:'عدم الإتاحة',PERF:'البطء والتأخير',TRANS:'المعاملات والدفع',UX:'الواجهة والاستخدام',OTHER:'مشكلات أخرى'}
export interface Prediction {is_complaint:boolean; complaint_score:number|null;category:Category|null;category_score:number|null;needs_review:boolean;model_version:string}
export interface Correction {id:number;field_name:string;old_value:unknown;new_value:unknown;corrected_at:string}
export interface Complaint extends Prediction {p1_analysis?:P1Analysis|null;id:number;source:string;source_id:string|null;source_app:string|null;original_event_time:string|null;imported_at:string;text_redacted:string;system_name:string|null;system_evidence:string;is_demo:boolean;original_prediction:Prediction;original_system_name:string|null;system_reviewed:boolean;corrections:Correction[]}
export interface ModelInfo {mode:'mock'|'real';model_version:string|null;observed_versions:string[];status:string;integration_error:string|null;categories:Category[];evaluation_available:boolean;evaluation_report:string|null;evaluation_model_version:string|null}
export interface Overview {no_review_required_messages:number;known_system_complaints:number;dated_complaints:number;sources:{source:string;messages:number;complaints:number}[];comparison:{date_from:string;date_to:string;previous_complaints:number;current_complaints:number;complaint_delta:number;complaint_change_ratio:number|null}|null;total_messages:number;complaints:number;complaint_ratio:number;needs_review:number;categories:{category:Category;count:number}[];uncategorized_complaints:number}
export interface SystemItem {name:string|null;count:number;share:number;categories:Partial<Record<Category|'UNCLASSIFIED',number>>}
export interface Systems {total_complaints:number;items:SystemItem[]}
export interface Trends {time_basis:string;interval:string;missing_event_time:number;points:{date:string;count:number}[]}
export interface Listing {items:Complaint[];total:number;page:number;page_size:number}
export interface ImportResult {accepted:number;duplicates:number;failed:number;processed:number;errors:{row:number;reason:string}[];stopped:boolean;integration_error:string|null}
export interface Review {is_complaint:boolean;category:Category|null;system_name:string|null;needs_review:boolean}
export type Filters=Record<string,string>

export interface EvidenceSpan {text:string;start:number;end:number}
export interface OCRResult {status:'ok'|'empty'|'failed';text:string;lines:{text:string;confidence:number|null;bbox:number[]}[];mean_confidence:number|null;low_confidence:boolean;error:{code:string;message:string}|null;engine:string;image:{format:'PNG'|'JPEG';width:number;height:number}|null;elapsed_ms:number;corrected_text?:string|null;used_for_classification?:string|null}
export interface P1Analysis {schema_version:'p1-analysis-v1';analysis_kind:'complaint'|'not_complaint'|'error_screen_signal'|'no_text'|'ocr_failed';input:{has_user_text:boolean;has_image:boolean;text_source:string|null;classified_text:string|null};prediction:Prediction|null;systems:{status:'identified'|'ambiguous'|'unknown';systems:{system_id:string;name_ar:string;name_en:string;mentions:(EvidenceSpan&{basis:string})[]}[];possible_mentions:(EvidenceSpan&{system_id:string;reason:string})[];generic_references:EvidenceSpan[];registry_version:string;method:string}|null;signals:{error_message_cues:(EvidenceSpan&{cue:string})[];narrative_markers:string[];needs_user_context:boolean;ocr_needs_review:boolean};ocr:OCRResult|null;notes:string[];timing_ms:Record<string,number>}
export interface OCRDraft {draft_id:string;expires_at:string;ocr:OCRResult}
export interface P1Response {message:Complaint|null;duplicate:boolean;analysis:P1Analysis}
