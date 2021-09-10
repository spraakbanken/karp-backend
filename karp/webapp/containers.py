from dependency_injector import containers, providers


class WebAppContainer(containers.DeclarativeContainer):

    context = providers.Dependency()
