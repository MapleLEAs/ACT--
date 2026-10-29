from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    """
    自定义异常处理
    """
    response = exception_handler(exc, context)

    if response is not None:
        # 这里可以添加自定义的异常处理逻辑
        # 例如统一日志记录
        pass
        
    return response
