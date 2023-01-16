# Development

`karp` is implemented according to Clean Architecture/Domain-Driven-Design.

The repo defines two apps:
- `karp.webapp`: the backend
- `karp.cliapp`: the `karp-cli` tool to manage the backend

The ambition is that the apps only depends on `karp.main`, `karp.lex`, `karp.search` och for the webapp also `karp.auth` and that `karp.main` holds the dependency injection stuff that binds implementations from `karp.lex_infrastructure`, `karp.auth_infrastructure` and `karp.search_infrastructure`.

This means that `karp.auth`, `karp.lex` and `karp.search` defines the `domain`, interfaces for needed functionality and the `buisness logic` of the apps.


# References

- [Clean Architecture]()
- [Domain-Driven Design]()
