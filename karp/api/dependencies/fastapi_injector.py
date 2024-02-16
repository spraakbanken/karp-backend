from fastapi import Request  # noqa: D100


def inject_from_req(inject_cls):  # noqa: ANN201, D103
    def _inject_from_req(request: Request):  # noqa: ANN202
        return request.state.container.get(inject_cls)

    return _inject_from_req
