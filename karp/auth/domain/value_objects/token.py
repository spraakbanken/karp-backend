import typing  # noqa: D100

import pydantic


class AccessToken(pydantic.BaseModel):  # noqa: D101
    access_token: str
    token_type: str

    def as_header(self) -> typing.Dict[str, str]:  # noqa: D102
        return {
            "Authorization": f"{self.token_type} {self.access_token}",
        }
