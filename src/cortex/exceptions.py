class CortexError(Exception):
    """Base exception for Cortex Mentor"""
    pass

class PipelineError(CortexError):
    """Error in pipeline execution"""
    pass

class ProcessorError(PipelineError):
    """Error during processor execution"""
    pass

class ServiceError(CortexError):
    """Error in service layer"""
    pass

class WebsocketError(ServiceError):
    """Error in websocket communication"""
    pass

class ConfigurationError(CortexError):
    """Configuration or environment error"""
    pass





