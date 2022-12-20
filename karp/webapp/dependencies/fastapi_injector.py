from fastapi import Request


def inject_from_req(inject_cls):
    def _inject_from_req(request: Request):
        return request.state.container.get(inject_cls)

    return _inject_from_req
