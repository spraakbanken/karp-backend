import pydantic


class AccessToken(pydantic.BaseModel):
    access_token: str
    token_type: str
