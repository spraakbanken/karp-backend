import typing

import pydantic


class AccessToken(pydantic.BaseModel):
    access_token: str
    token_type: str

    def as_header(self) -> typing.Dict[str, str]:
        return {
            "Authorization": f"{self.token_type} {self.access_token}",
        }
