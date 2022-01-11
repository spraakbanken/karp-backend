from dependency_injector import containers, providers

from karp.infrastructure.jwt import jwt_auth_service
from karp.main.containers import AppContainer


class WebAppContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    context = providers.Container(
        AppContainer,
        config=config,
    )

    jwt_authenticator = providers.Singleton(
        jwt_auth_service.JWTAuthenticator,
        pubkey_path=config.auth.jwt.pubkey_path,
        resource_uow=context.resource_uow,
    )

    auth_service = providers.Selector(
        config.auth.type,
        jwt_auth=jwt_authenticator
    )
