from rest_framework.renderers import JSONRenderer

class CustomJSONRenderer(JSONRenderer):
    """
    标准化 JSON 响应格式
    {
        "code": 200,
        "msg": "success",
        "data": ...
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context:
            response = renderer_context['response']
            code = response.status_code
            msg = "success"
            
            if code >= 400:
                msg = "error"
                # 尝试提取更友好的错误信息
                if isinstance(data, dict) and 'detail' in data:
                    msg = str(data['detail'])
                elif isinstance(data, (list, dict)):
                     msg = str(data)
                
            formatted_data = {
                "code": code,
                "msg": msg,
                "data": data
            }
            
            return super().render(formatted_data, accepted_media_type, renderer_context)
        
        return super().render(data, accepted_media_type, renderer_context)
