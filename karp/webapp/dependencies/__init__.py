from karp.webapp.dependencies.lex_deps import (
    get_entry_diff,
    get_entry_history,
    get_history,
    get_lex_uc,
    get_resources_read_repo,
)
from karp.webapp.dependencies.auth_deps import (
    get_auth_service,
    get_user,
    get_user_optional,
    get_resource_permissions,
)
from karp.webapp.dependencies.fastapi_injector import inject_from_req
