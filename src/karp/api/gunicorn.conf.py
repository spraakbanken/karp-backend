def post_fork(server, worker):
    """
    When running gunicorn with the --preload option,
    use this file with the --config option to make each
    worker discard the connection pool and create its own
    otherwise bad stuff will happen
    """
    from karp.globals import _engine_ctx_var

    engine = _engine_ctx_var.get()
    engine.dispose()
