from importlib import import_module
from ..schemas import Prediction

MOCK_EXAMPLES={
    'رمز التحقق لا يصل عند تسجيل الدخول':'AUTH',
    'التطبيق لا يفتح ويغلق فجأة':'AVAIL',
    'التطبيق بطيء':'PERF',
    'خصم المبلغ ولم يكتمل الطلب':'TRANS',
    'زر التأكيد لا يظهر':'UX',
    'الخدمة فيها مشكلة':'OTHER',
    'شكرا التطبيق ممتاز':None,
}

class IntegrationError(RuntimeError): pass

class MockPredictor:
    mode='mock'
    last_version='mock-v1'
    last_error=None
    def predict(self, text):
        if not text.strip(): raise ValueError('النص فارغ')
        category=MOCK_EXAMPLES.get(text.strip(),'OTHER')
        return Prediction(is_complaint=category is not None, complaint_score=None, category=category,
                          category_score=None, needs_review=True, model_version=self.last_version)

class RealPredictor:
    mode='real'
    last_version=None
    last_error=None
    def __init__(self, function=None): self._function=function
    def predict(self,text):
        if not text.strip(): raise ValueError('النص فارغ')
        try:
            if self._function is None:
                self._function=import_module('ml.infer').predict_text
            result=Prediction.model_validate(self._function(text))
            self.last_version=result.model_version
            self.last_error=None
            return result
        except Exception as error:
            self.last_error=f'{type(error).__name__}: {error}'
            raise IntegrationError(f'تعذر تشغيل النموذج الحقيقي — {self.last_error}') from error

def get_predictor(mode):
    if mode=='mock': return MockPredictor()
    if mode=='real': return RealPredictor()
    raise ValueError('APP_ML_MODE must be mock or real')
