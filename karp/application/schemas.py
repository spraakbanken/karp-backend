from pydantic import BaseModel


class SystemResponse(BaseModel):
    message: str = "ok"

    def __bool__(self):
        return True


class SystemOk(SystemResponse):
    pass


class SystemNotOk(SystemResponse):
    def __bool__(self):
        return False


class SystemMonitorResponse(BaseModel):
    database: str
