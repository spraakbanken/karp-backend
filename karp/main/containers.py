from dependency_injector import containers, providers


class AppContainer(containers.DeclarativeContainer):

    config = providers.Configuration()
