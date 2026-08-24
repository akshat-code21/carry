➜  yt-chatter git:(feature/ph_2) ✗ uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
INFO:     Will watch for changes in these directories: ['/Users/akshatsipany/Work/yt-chatter']
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [36923] using WatchFiles
[transformers] PyTorch was not found. Models won't be available and only tokenizers, configuration and file/data utilities can be used.
INFO:     Started server process [36925]
INFO:     Waiting for application startup.
2026-08-24 19:30:03,581 | INFO    | src.main | TickerFlow initialised  provider=native_raw  plan=free
INFO:     Application startup complete.
2026-08-24 19:30:11,302 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-24 19:30:11,581 | INFO    | src.auth.dependencies | Session token carries no 'role' claim; syncing admin role via Clerk Backend API public metadata instead (Configure → Sessions → Customize session token → {"role": "{{user.public_metadata.role}}"} avoids the per-minute API lookup). Present claims: ['azp', 'exp', 'fva', 'iat', 'iss', 'nbf', 'sid', 'sts', 'sub', 'v']
2026-08-24 19:30:11,587 | WARNING | src.services.search_answer_service | search/answer: cache read failed: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedTableError'>: relation "search_answers" does not exist
[SQL: SELECT search_answers.query_hash, search_answers.query_text, search_answers.answer_json, search_answers.created_at
FROM search_answers
WHERE search_answers.query_hash = $1::VARCHAR]
[parameters: ('1d202d80d6fd75cafc2bf4537ada56fc66d43034b5485571a54c4c20115cdbe8',)]
(Background on this error at: https://sqlalche.me/e/20/f405)
2026-08-24 19:30:11,600 | ERROR   | src.main | Unhandled exception on /api/search/answer: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, videos.title, videos.youtube_video_id, channels.title AS title_1
FROM transcript_segments JOIN videos ON transcript_segments.video_id = videos.id JOIN channels ON videos.channel_id = channels.id
WHERE transcript_segments.id IN ($1::UUID, $2::UUID, $3::UUID, $4::UUID, $5::UUID, $6::UUID, $7::UUID, $8::UUID, $9::UUID, $10::UUID, $11::UUID, $12::UUID)]
[parameters: (UUID('e1bfe3e6-c155-4b06-aa38-03a33f49d448'), UUID('ce514ad2-0e9d-4f81-a680-63822523018e'), UUID('0d87217d-b62e-4a09-93ad-dc7d9b3f9a65'), UUID('5d45c7f9-eaac-42e9-b5be-a5a640e7df79'), UUID('40693411-60cb-475d-a5e0-b659a2278aef'), UUID('88e464a3-fa9c-4b86-a3c0-0925256f1fab'), UUID('dd79b880-8183-4e62-b59e-47a207aafea3'), UUID('91caf8a6-b723-4973-8f51-6e38dcf75cf8'), UUID('7dd1a063-2eb9-4025-8e0f-5cd1fb804f25'), UUID('2e344c47-73ff-4152-ba3b-676e489e5ffe'), UUID('1ed7a26f-57e1-4828-b66e-58680f633de5'), UUID('cd13c84a-c452-488a-8fbc-26a2acc55962'))]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
Traceback (most recent call last):                                                                                               File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in _prepare_and_execute
    prepared_stmt, attributes = await adapt_connection._prepare(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                 File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in _prepare
    prepared_stmt = await self._connection.prepare(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                              File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare
    return await self._prepare(
           ^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in _prepare       stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in _get_statement                                                                                                                                statement = await self._protocol.prepare(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.InFailedSQLTransactionError: current transaction is aborted, commands ignored until end of transaction block
The above exception was the direct cause of the following exception:

Traceback (most recent call last):                                                                                               File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute                                                                                                                   self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only                                                                                                                     return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^                                                                                                         File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)                                                                                                File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)                                                                              File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error: <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

                                                           Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__                                                                                                                             await self.app(scope, receive, _send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in __call__                                                                                                                               response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/analytics/middleware.py", line 43, in dispatch                                     response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^                                                                                          File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 88, in __call__
    await self.app(scope, receive, send)                                                                                         File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__                                                                                                                          await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)                                                     File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app                                                                                                                          await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)                                                                                         File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/routing.py", line 660, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2685, in app
    await route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1766, in handle
    await self.original_router.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2740, in handle
    await included_router._handle_selected(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1786, in _handle_selected                                                                                                                                await original_route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1265, in handle
    await app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 151, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app                                                                                                                          await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 137, in app
    response = await f(request)                                                                                                               ^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 691, in app
    raw_response = await run_endpoint_function(                                                                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 345, in run_endpoint_function                                                                                                                            return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/api/search.py", line 213, in search_answer
    result = await answer_service.get_or_create(q, ids, max_input=limit)                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_answer_service.py", line 202, in get_or_create
    segments = await self._resolve_segments(query, segment_ids, max_input)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                       File "/Users/akshatsipany/Work/yt-chatter/src/services/search_answer_service.py", line 254, in _resolve_segments
    res = await self.db.execute(stmt)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                            File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 448, in execute
    result = await greenlet_spawn(                                                                                                          ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn                                                                                                                 result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2373, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^                                                                                               File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2271, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                               File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^                                                                                                                 File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(                                                                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement                                                                                                                   ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e                                                                File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(                                                                                                     File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)                                                                                        File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(                                                                                               File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)                                                                              File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, videos.title, videos.youtube_video_id, channels.title AS title_1      FROM transcript_segments JOIN videos ON transcript_segments.video_id = videos.id JOIN channels ON videos.channel_id = channels.id
WHERE transcript_segments.id IN ($1::UUID, $2::UUID, $3::UUID, $4::UUID, $5::UUID, $6::UUID, $7::UUID, $8::UUID, $9::UUID, $10::UUID, $11::UUID, $12::UUID)]
[parameters: (UUID('e1bfe3e6-c155-4b06-aa38-03a33f49d448'), UUID('ce514ad2-0e9d-4f81-a680-63822523018e'), UUID('0d87217d-b62e-4a09-93ad-dc7d9b3f9a65'), UUID('5d45c7f9-eaac-42e9-b5be-a5a640e7df79'), UUID('40693411-60cb-475d-a5e0-b659a2278aef'), UUID('88e464a3-fa9c-4b86-a3c0-0925256f1fab'), UUID('dd79b880-8183-4e62-b59e-47a207aafea3'), UUID('91caf8a6-b723-4973-8f51-6e38dcf75cf8'), UUID('7dd1a063-2eb9-4025-8e0f-5cd1fb804f25'), UUID('2e344c47-73ff-4152-ba3b-676e489e5ffe'), UUID('1ed7a26f-57e1-4828-b66e-58680f633de5'), UUID('cd13c84a-c452-488a-8fbc-26a2acc55962'))]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
INFO:     127.0.0.1:63736 - "GET /api/search/answer?q=Anthropic%27s%20IPO%20in%202027&segment_ids=e1bfe3e6-c155-4b06-aa38-03a33f49d448%2Cce514ad2-0e9d-4f81-a680-63822523018e%2C0d87217d-b62e-4a09-93ad-dc7d9b3f9a65%2C5d45c7f9-eaac-42e9-b5be-a5a640e7df79%2C40693411-60cb-475d-a5e0-b659a2278aef%2C88e464a3-fa9c-4b86-a3c0-0925256f1fab%2Cdd79b880-8183-4e62-b59e-47a207aafea3%2C91caf8a6-b723-4973-8f51-6e38dcf75cf8%2C7dd1a063-2eb9-4025-8e0f-5cd1fb804f25%2C2e344c47-73ff-4152-ba3b-676e489e5ffe%2C1ed7a26f-57e1-4828-b66e-58680f633de5%2Ccd13c84a-c452-488a-8fbc-26a2acc55962 HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in _prepare_and_execute
    prepared_stmt, attributes = await adapt_connection._prepare(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in _prepare
    prepared_stmt = await self._connection.prepare(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare
    return await self._prepare(
           ^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in _prepare
    stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in _get_statement
    statement = await self._protocol.prepare(                                                                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.InFailedSQLTransactionError: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute                                                                                                                             cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(                                                                                               File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                      File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^                                                                                                         File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception                                                                                                         raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error: <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block

                                              The above exception was the direct cause of the following exception:

Traceback (most recent call last):                                                                                               File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 422, in run_asgi
    result = await app(  # type: ignore[func-returns-value]                                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 63, in __call__                                                                                                                         return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/applications.py", line 1163, in __call__    await super().__call__(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/applications.py", line 90, in __call__
    await self.middleware_stack(scope, receive, send)                                                                            File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc                                                                                                                    File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/analytics/middleware.py", line 43, in dispatch
    response = await call_next(request)                                                                                                       ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 88, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/routing.py", line 660, in __call__        await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2685, in app
    await route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1766, in handle
    await self.original_router.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2740, in handle
    await included_router._handle_selected(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1786, in _handle_selected
    await original_route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1265, in handle
    await app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 151, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 137, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 691, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 345, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/api/search.py", line 213, in search_answer
    result = await answer_service.get_or_create(q, ids, max_input=limit)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_answer_service.py", line 202, in get_or_create
    segments = await self._resolve_segments(query, segment_ids, max_input)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_answer_service.py", line 254, in _resolve_segments
    res = await self.db.execute(stmt)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 448, in execute
    result = await greenlet_spawn(
             ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2373, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2271, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, videos.title, videos.youtube_video_id, channels.title AS title_1
FROM transcript_segments JOIN videos ON transcript_segments.video_id = videos.id JOIN channels ON videos.channel_id = channels.id
WHERE transcript_segments.id IN ($1::UUID, $2::UUID, $3::UUID, $4::UUID, $5::UUID, $6::UUID, $7::UUID, $8::UUID, $9::UUID, $10::UUID, $11::UUID, $12::UUID)]
[parameters: (UUID('e1bfe3e6-c155-4b06-aa38-03a33f49d448'), UUID('ce514ad2-0e9d-4f81-a680-63822523018e'), UUID('0d87217d-b62e-4a09-93ad-dc7d9b3f9a65'), UUID('5d45c7f9-eaac-42e9-b5be-a5a640e7df79'), UUID('40693411-60cb-475d-a5e0-b659a2278aef'), UUID('88e464a3-fa9c-4b86-a3c0-0925256f1fab'), UUID('dd79b880-8183-4e62-b59e-47a207aafea3'), UUID('91caf8a6-b723-4973-8f51-6e38dcf75cf8'), UUID('7dd1a063-2eb9-4025-8e0f-5cd1fb804f25'), UUID('2e344c47-73ff-4152-ba3b-676e489e5ffe'), UUID('1ed7a26f-57e1-4828-b66e-58680f633de5'), UUID('cd13c84a-c452-488a-8fbc-26a2acc55962'))]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
INFO:     127.0.0.1:63743 - "GET /api/activity/unread-count HTTP/1.1" 200 OK
2026-08-24 19:30:11,637 | WARNING | src.services.search_coverage_service | search/coverage: cache read failed: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedTableError'>: relation "search_answers" does not exist
[SQL: SELECT search_answers.query_hash, search_answers.query_text, search_answers.answer_json, search_answers.created_at
FROM search_answers
WHERE search_answers.query_hash = $1::VARCHAR]
[parameters: ('1bdd4c809d247a718e8f7c3dd53d936b2615ab74286959635156685f2b2bdbb5',)]
(Background on this error at: https://sqlalche.me/e/20/f405)
2026-08-24 19:30:11,640 | WARNING | src.services.search_coverage_service | search/coverage: snippet query failed ((sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT DISTINCT ON (transcript_segments.video_id) transcript_segments.id, transcript_segments.video_id, transcript_segments.text, videos.title AS video_title, videos.youtube_video_id, channels.title AS channel_title, videos.published_at
FROM transcript_segments JOIN videos ON transcript_segments.video_id = videos.id JOIN channels ON videos.channel_id = channels.id
WHERE (to_tsvector($1::REGCONFIG, transcript_segments.text) @@ plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) AND videos.published_at IS NOT NULL AND videos.published_at >= $4::TIMESTAMP WITH TIME ZONE ORDER BY transcript_segments.video_id, ts_rank(to_tsvector($5::REGCONFIG, transcript_segments.text), plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) DESC]
[parameters: ('english', 'english', "Anthropic's IPO in 2027", datetime.datetime(2026, 8, 10, 14, 0, 11, 637305, tzinfo=datetime.timezone.utc), 'english')]
(Background on this error at: https://sqlalche.me/e/20/dbapi)); using fallback
2026-08-24 19:30:11,640 | INFO    | src.services.etf_mapping_service | Loaded 57 ETF mapping groups and 131 known ETF tickers from /Users/akshatsipany/Work/yt-chatter/data/etf_mappings.json
2026-08-24 19:30:11,643 | ERROR   | src.main | Unhandled exception on /api/search/coverage: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, ts_rank(to_tsvector($1::REGCONFIG, transcript_segments.text), plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) AS rank
FROM transcript_segments
WHERE to_tsvector($4::REGCONFIG, transcript_segments.text) @@ plainto_tsquery($2::REGCONFIG, $3::VARCHAR) ORDER BY rank DESC
 LIMIT $5::INTEGER OFFSET $6::INTEGER]
[parameters: ('english', 'english', "Anthropic's IPO in 2027", 'english', 100, 0)]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in _prepare_and_execute
    prepared_stmt, attributes = await adapt_connection._prepare(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in _prepare
    prepared_stmt = await self._connection.prepare(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare
    return await self._prepare(
           ^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in _prepare
    stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in _get_statement
    statement = await self._protocol.prepare(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.InFailedSQLTransactionError: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error: <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/analytics/middleware.py", line 43, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 88, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/routing.py", line 660, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2685, in app
    await route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1766, in handle
    await self.original_router.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2740, in handle
    await included_router._handle_selected(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1786, in _handle_selected
    await original_route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1265, in handle
    await app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 151, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 137, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 691, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 345, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/api/search.py", line 234, in search_coverage
    result = await coverage_service.get_or_create(q, ids, window_days=window_days)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 178, in get_or_create
    snippets = await self._resolve_video_snippets(query, segment_ids, window_days)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 269, in _resolve_video_snippets
    return await self._fallback_snippets(query, segment_ids, window_days)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 282, in _fallback_snippets
    results = await self._search_service.hybrid_search(query, limit=100)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_service.py", line 83, in hybrid_search
    keyword_segments = await self._keyword_search_segments(
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_service.py", line 366, in _keyword_search_segments
    result = await self.db.execute(stmt)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 448, in execute
    result = await greenlet_spawn(
             ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2373, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2271, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, ts_rank(to_tsvector($1::REGCONFIG, transcript_segments.text), plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) AS rank
FROM transcript_segments
WHERE to_tsvector($4::REGCONFIG, transcript_segments.text) @@ plainto_tsquery($2::REGCONFIG, $3::VARCHAR) ORDER BY rank DESC
 LIMIT $5::INTEGER OFFSET $6::INTEGER]
[parameters: ('english', 'english', "Anthropic's IPO in 2027", 'english', 100, 0)]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
INFO:     127.0.0.1:63737 - "GET /api/search/coverage?q=Anthropic%27s%20IPO%20in%202027&window_days=14&segment_ids=e1bfe3e6-c155-4b06-aa38-03a33f49d448%2Cce514ad2-0e9d-4f81-a680-63822523018e%2C0d87217d-b62e-4a09-93ad-dc7d9b3f9a65%2C5d45c7f9-eaac-42e9-b5be-a5a640e7df79%2C40693411-60cb-475d-a5e0-b659a2278aef%2C88e464a3-fa9c-4b86-a3c0-0925256f1fab%2Cdd79b880-8183-4e62-b59e-47a207aafea3%2C91caf8a6-b723-4973-8f51-6e38dcf75cf8%2C7dd1a063-2eb9-4025-8e0f-5cd1fb804f25%2C2e344c47-73ff-4152-ba3b-676e489e5ffe%2C1ed7a26f-57e1-4828-b66e-58680f633de5%2Ccd13c84a-c452-488a-8fbc-26a2acc55962 HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in _prepare_and_execute
    prepared_stmt, attributes = await adapt_connection._prepare(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in _prepare
    prepared_stmt = await self._connection.prepare(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare
    return await self._prepare(
           ^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in _prepare
    stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in _get_statement
    statement = await self._protocol.prepare(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.InFailedSQLTransactionError: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error: <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 422, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 63, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/applications.py", line 1163, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/applications.py", line 90, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/analytics/middleware.py", line 43, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 88, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/routing.py", line 660, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2685, in app
    await route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1766, in handle
    await self.original_router.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2740, in handle
    await included_router._handle_selected(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1786, in _handle_selected
    await original_route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1265, in handle
    await app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 151, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 137, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 691, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 345, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/api/search.py", line 234, in search_coverage
    result = await coverage_service.get_or_create(q, ids, window_days=window_days)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 178, in get_or_create
    snippets = await self._resolve_video_snippets(query, segment_ids, window_days)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 269, in _resolve_video_snippets
    return await self._fallback_snippets(query, segment_ids, window_days)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 282, in _fallback_snippets
    results = await self._search_service.hybrid_search(query, limit=100)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_service.py", line 83, in hybrid_search
    keyword_segments = await self._keyword_search_segments(
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_service.py", line 366, in _keyword_search_segments
    result = await self.db.execute(stmt)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 448, in execute
    result = await greenlet_spawn(
             ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2373, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2271, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, ts_rank(to_tsvector($1::REGCONFIG, transcript_segments.text), plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) AS rank
FROM transcript_segments
WHERE to_tsvector($4::REGCONFIG, transcript_segments.text) @@ plainto_tsquery($2::REGCONFIG, $3::VARCHAR) ORDER BY rank DESC
 LIMIT $5::INTEGER OFFSET $6::INTEGER]
[parameters: ('english', 'english', "Anthropic's IPO in 2027", 'english', 100, 0)]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
2026-08-24 19:30:12,218 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IK4dA0cY3VtImYcbaMX831HHfd "HTTP/1.1 200 OK"
2026-08-24 19:30:13,555 | INFO    | httpx | HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 400 Bad Request"
2026-08-24 19:30:13,559 | WARNING | src.services.query_router | Query classification failed, falling back to factual_search: Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}
2026-08-24 19:30:14,071 | INFO    | httpx | HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
INFO:     127.0.0.1:63735 - "GET /api/search?q=Anthropic%27s%20IPO%20in%202027&type=hybrid&sort=relevance&limit=20 HTTP/1.1" 200 OK
2026-08-24 19:30:14,678 | WARNING | src.services.search_coverage_service | search/coverage: cache read failed: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedTableError'>: relation "search_answers" does not exist
[SQL: SELECT search_answers.query_hash, search_answers.query_text, search_answers.answer_json, search_answers.created_at
FROM search_answers
WHERE search_answers.query_hash = $1::VARCHAR]
[parameters: ('1bdd4c809d247a718e8f7c3dd53d936b2615ab74286959635156685f2b2bdbb5',)]
(Background on this error at: https://sqlalche.me/e/20/f405)
2026-08-24 19:30:14,679 | WARNING | src.services.search_coverage_service | search/coverage: snippet query failed ((sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT DISTINCT ON (transcript_segments.video_id) transcript_segments.id, transcript_segments.video_id, transcript_segments.text, videos.title AS video_title, videos.youtube_video_id, channels.title AS channel_title, videos.published_at
FROM transcript_segments JOIN videos ON transcript_segments.video_id = videos.id JOIN channels ON videos.channel_id = channels.id
WHERE (to_tsvector($1::REGCONFIG, transcript_segments.text) @@ plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) AND videos.published_at IS NOT NULL AND videos.published_at >= $4::TIMESTAMP WITH TIME ZONE ORDER BY transcript_segments.video_id, ts_rank(to_tsvector($5::REGCONFIG, transcript_segments.text), plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) DESC]
[parameters: ('english', 'english', "Anthropic's IPO in 2027", datetime.datetime(2026, 8, 10, 14, 0, 14, 678259, tzinfo=datetime.timezone.utc), 'english')]
(Background on this error at: https://sqlalche.me/e/20/dbapi)); using fallback
2026-08-24 19:30:14,680 | WARNING | src.services.search_answer_service | search/answer: cache read failed: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedTableError'>: relation "search_answers" does not exist
[SQL: SELECT search_answers.query_hash, search_answers.query_text, search_answers.answer_json, search_answers.created_at
FROM search_answers
WHERE search_answers.query_hash = $1::VARCHAR]
[parameters: ('1d202d80d6fd75cafc2bf4537ada56fc66d43034b5485571a54c4c20115cdbe8',)]
(Background on this error at: https://sqlalche.me/e/20/f405)
2026-08-24 19:30:14,682 | ERROR   | src.main | Unhandled exception on /api/search/coverage: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, ts_rank(to_tsvector($1::REGCONFIG, transcript_segments.text), plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) AS rank
FROM transcript_segments
WHERE to_tsvector($4::REGCONFIG, transcript_segments.text) @@ plainto_tsquery($2::REGCONFIG, $3::VARCHAR) ORDER BY rank DESC
 LIMIT $5::INTEGER OFFSET $6::INTEGER]
[parameters: ('english', 'english', "Anthropic's IPO in 2027", 'english', 100, 0)]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in _prepare_and_execute
    prepared_stmt, attributes = await adapt_connection._prepare(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in _prepare
    prepared_stmt = await self._connection.prepare(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare
    return await self._prepare(
           ^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in _prepare
    stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in _get_statement
    statement = await self._protocol.prepare(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.InFailedSQLTransactionError: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error: <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/analytics/middleware.py", line 43, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 88, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/routing.py", line 660, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2685, in app
    await route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1766, in handle
    await self.original_router.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2740, in handle
    await included_router._handle_selected(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1786, in _handle_selected
    await original_route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1265, in handle
    await app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 151, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 137, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 691, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 345, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/api/search.py", line 234, in search_coverage
    result = await coverage_service.get_or_create(q, ids, window_days=window_days)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 178, in get_or_create
    snippets = await self._resolve_video_snippets(query, segment_ids, window_days)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 269, in _resolve_video_snippets
    return await self._fallback_snippets(query, segment_ids, window_days)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 282, in _fallback_snippets
    results = await self._search_service.hybrid_search(query, limit=100)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_service.py", line 83, in hybrid_search
    keyword_segments = await self._keyword_search_segments(
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_service.py", line 366, in _keyword_search_segments
    result = await self.db.execute(stmt)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 448, in execute
    result = await greenlet_spawn(
             ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2373, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2271, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, ts_rank(to_tsvector($1::REGCONFIG, transcript_segments.text), plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) AS rank
FROM transcript_segments
WHERE to_tsvector($4::REGCONFIG, transcript_segments.text) @@ plainto_tsquery($2::REGCONFIG, $3::VARCHAR) ORDER BY rank DESC
 LIMIT $5::INTEGER OFFSET $6::INTEGER]
[parameters: ('english', 'english', "Anthropic's IPO in 2027", 'english', 100, 0)]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
INFO:     127.0.0.1:63753 - "GET /api/search/coverage?q=Anthropic%27s%20IPO%20in%202027&window_days=14&segment_ids=f544de94-a4ef-46f4-a02c-1d4d03431a66%2Cb9f03cc4-52b7-464e-96b6-cc10e6d970ce%2Cd9164229-7371-4a4b-ab38-bd5ffb560d38%2Cf78b1c5b-24a5-408d-91f2-c8a134f1cfa5%2C59043a87-55ad-424a-92ef-993e7bae9ce6%2C7d46bce9-13c1-40bc-9031-c556780bdef6%2C9b390848-a9f4-45c2-a59c-798f52b18536%2C91f4c874-0b15-4c8f-abc7-265355fc752a%2C4e508a5a-ff17-467d-bf7d-3bad4956316e%2Cd0644d46-1a49-44ac-b3ac-7f039b22658c%2C902e7697-1ae0-49ff-b811-e51c18a36e3b%2C46160227-22ff-494f-bf9f-f150149f84d2 HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in _prepare_and_execute
    prepared_stmt, attributes = await adapt_connection._prepare(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in _prepare
    prepared_stmt = await self._connection.prepare(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare
    return await self._prepare(
           ^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in _prepare
    stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in _get_statement
    statement = await self._protocol.prepare(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.InFailedSQLTransactionError: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error: <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 422, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 63, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/applications.py", line 1163, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/applications.py", line 90, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/analytics/middleware.py", line 43, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 88, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/routing.py", line 660, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2685, in app
    await route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1766, in handle
    await self.original_router.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2740, in handle
    await included_router._handle_selected(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1786, in _handle_selected
    await original_route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1265, in handle
    await app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 151, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 137, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 691, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 345, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/api/search.py", line 234, in search_coverage
    result = await coverage_service.get_or_create(q, ids, window_days=window_days)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 178, in get_or_create
    snippets = await self._resolve_video_snippets(query, segment_ids, window_days)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 269, in _resolve_video_snippets
    return await self._fallback_snippets(query, segment_ids, window_days)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_coverage_service.py", line 282, in _fallback_snippets
    results = await self._search_service.hybrid_search(query, limit=100)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_service.py", line 83, in hybrid_search
    keyword_segments = await self._keyword_search_segments(
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_service.py", line 366, in _keyword_search_segments
    result = await self.db.execute(stmt)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 448, in execute
    result = await greenlet_spawn(
             ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2373, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2271, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, ts_rank(to_tsvector($1::REGCONFIG, transcript_segments.text), plainto_tsquery($2::REGCONFIG, $3::VARCHAR)) AS rank
FROM transcript_segments
WHERE to_tsvector($4::REGCONFIG, transcript_segments.text) @@ plainto_tsquery($2::REGCONFIG, $3::VARCHAR) ORDER BY rank DESC
 LIMIT $5::INTEGER OFFSET $6::INTEGER]
[parameters: ('english', 'english', "Anthropic's IPO in 2027", 'english', 100, 0)]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
2026-08-24 19:30:14,687 | ERROR   | src.main | Unhandled exception on /api/search/answer: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, videos.title, videos.youtube_video_id, channels.title AS title_1
FROM transcript_segments JOIN videos ON transcript_segments.video_id = videos.id JOIN channels ON videos.channel_id = channels.id
WHERE transcript_segments.id IN ($1::UUID, $2::UUID, $3::UUID, $4::UUID, $5::UUID, $6::UUID, $7::UUID, $8::UUID, $9::UUID, $10::UUID, $11::UUID, $12::UUID)]
[parameters: (UUID('f544de94-a4ef-46f4-a02c-1d4d03431a66'), UUID('b9f03cc4-52b7-464e-96b6-cc10e6d970ce'), UUID('d9164229-7371-4a4b-ab38-bd5ffb560d38'), UUID('f78b1c5b-24a5-408d-91f2-c8a134f1cfa5'), UUID('59043a87-55ad-424a-92ef-993e7bae9ce6'), UUID('7d46bce9-13c1-40bc-9031-c556780bdef6'), UUID('9b390848-a9f4-45c2-a59c-798f52b18536'), UUID('91f4c874-0b15-4c8f-abc7-265355fc752a'), UUID('4e508a5a-ff17-467d-bf7d-3bad4956316e'), UUID('d0644d46-1a49-44ac-b3ac-7f039b22658c'), UUID('902e7697-1ae0-49ff-b811-e51c18a36e3b'), UUID('46160227-22ff-494f-bf9f-f150149f84d2'))]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in _prepare_and_execute
    prepared_stmt, attributes = await adapt_connection._prepare(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in _prepare
    prepared_stmt = await self._connection.prepare(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare
    return await self._prepare(
           ^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in _prepare
    stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in _get_statement
    statement = await self._protocol.prepare(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.InFailedSQLTransactionError: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error: <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/analytics/middleware.py", line 43, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 88, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/routing.py", line 660, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2685, in app
    await route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1766, in handle
    await self.original_router.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2740, in handle
    await included_router._handle_selected(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1786, in _handle_selected
    await original_route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1265, in handle
    await app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 151, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 137, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 691, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 345, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/api/search.py", line 213, in search_answer
    result = await answer_service.get_or_create(q, ids, max_input=limit)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_answer_service.py", line 202, in get_or_create
    segments = await self._resolve_segments(query, segment_ids, max_input)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_answer_service.py", line 254, in _resolve_segments
    res = await self.db.execute(stmt)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 448, in execute
    result = await greenlet_spawn(
             ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2373, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2271, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, videos.title, videos.youtube_video_id, channels.title AS title_1
FROM transcript_segments JOIN videos ON transcript_segments.video_id = videos.id JOIN channels ON videos.channel_id = channels.id
WHERE transcript_segments.id IN ($1::UUID, $2::UUID, $3::UUID, $4::UUID, $5::UUID, $6::UUID, $7::UUID, $8::UUID, $9::UUID, $10::UUID, $11::UUID, $12::UUID)]
[parameters: (UUID('f544de94-a4ef-46f4-a02c-1d4d03431a66'), UUID('b9f03cc4-52b7-464e-96b6-cc10e6d970ce'), UUID('d9164229-7371-4a4b-ab38-bd5ffb560d38'), UUID('f78b1c5b-24a5-408d-91f2-c8a134f1cfa5'), UUID('59043a87-55ad-424a-92ef-993e7bae9ce6'), UUID('7d46bce9-13c1-40bc-9031-c556780bdef6'), UUID('9b390848-a9f4-45c2-a59c-798f52b18536'), UUID('91f4c874-0b15-4c8f-abc7-265355fc752a'), UUID('4e508a5a-ff17-467d-bf7d-3bad4956316e'), UUID('d0644d46-1a49-44ac-b3ac-7f039b22658c'), UUID('902e7697-1ae0-49ff-b811-e51c18a36e3b'), UUID('46160227-22ff-494f-bf9f-f150149f84d2'))]
(Background on this error at: https://sqlalche.me/e/20/dbapi)
INFO:     127.0.0.1:63752 - "GET /api/search/answer?q=Anthropic%27s%20IPO%20in%202027&segment_ids=f544de94-a4ef-46f4-a02c-1d4d03431a66%2Cb9f03cc4-52b7-464e-96b6-cc10e6d970ce%2Cd9164229-7371-4a4b-ab38-bd5ffb560d38%2Cf78b1c5b-24a5-408d-91f2-c8a134f1cfa5%2C59043a87-55ad-424a-92ef-993e7bae9ce6%2C7d46bce9-13c1-40bc-9031-c556780bdef6%2C9b390848-a9f4-45c2-a59c-798f52b18536%2C91f4c874-0b15-4c8f-abc7-265355fc752a%2C4e508a5a-ff17-467d-bf7d-3bad4956316e%2Cd0644d46-1a49-44ac-b3ac-7f039b22658c%2C902e7697-1ae0-49ff-b811-e51c18a36e3b%2C46160227-22ff-494f-bf9f-f150149f84d2 HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 526, in _prepare_and_execute
    prepared_stmt, attributes = await adapt_connection._prepare(
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 773, in _prepare
    prepared_stmt = await self._connection.prepare(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 638, in prepare
    return await self._prepare(
           ^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 657, in _prepare
    stmt = await self._get_statement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/asyncpg/connection.py", line 443, in _get_statement
    statement = await self._protocol.prepare(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg/protocol/protocol.pyx", line 165, in prepare
asyncpg.exceptions.InFailedSQLTransactionError: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.Error: <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/uvicorn/protocols/http/httptools_impl.py", line 422, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 63, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/applications.py", line 1163, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/applications.py", line 90, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 193, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/analytics/middleware.py", line 43, in dispatch
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 168, in call_next
    raise app_exc from app_exc.__cause__ or app_exc.__context__
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/cors.py", line 88, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/routing.py", line 660, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2685, in app
    await route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1766, in handle
    await self.original_router.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 2740, in handle
    await included_router._handle_selected(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1786, in _handle_selected
    await original_route.handle(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 1265, in handle
    await app(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 151, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 137, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 691, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/fastapi/routing.py", line 345, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/api/search.py", line 213, in search_answer
    result = await answer_service.get_or_create(q, ids, max_input=limit)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_answer_service.py", line 202, in get_or_create
    segments = await self._resolve_segments(query, segment_ids, max_input)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/src/services/search_answer_service.py", line 254, in _resolve_segments
    res = await self.db.execute(stmt)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/session.py", line 448, in execute
    result = await greenlet_spawn(
             ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 201, in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2373, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2271, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 585, in execute
    self._adapt_connection.await_(
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 563, in _prepare_and_execute
    self._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 513, in _handle_exception
    self._adapt_connection._handle_exception(error)
  File "/Users/akshatsipany/Work/yt-chatter/.venv/lib/python3.12/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py", line 797, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.InFailedSQLTransactionError'>: current transaction is aborted, commands ignored until end of transaction block
[SQL: SELECT transcript_segments.id, transcript_segments.video_id, transcript_segments.start_sec, transcript_segments.end_sec, transcript_segments.text, transcript_segments.embedding, videos.title, videos.youtube_video_id, channels.title AS title_1
FROM transcript_segments JOIN videos ON transcript_segments.video_id = videos.id JOIN channels ON videos.channel_id = channels.id
WHERE transcript_segments.id IN ($1::UUID, $2::UUID, $3::UUID, $4::UUID, $5::UUID, $6::UUID, $7::UUID, $8::UUID, $9::UUID, $10::UUID, $11::UUID, $12::UUID)]
[parameters: (UUID('f544de94-a4ef-46f4-a02c-1d4d03431a66'), UUID('b9f03cc4-52b7-464e-96b6-cc10e6d970ce'), UUID('d9164229-7371-4a4b-ab38-bd5ffb560d38'), UUID('f78b1c5b-24a5-408d-91f2-c8a134f1cfa5'), UUID('59043a87-55ad-424a-92ef-993e7bae9ce6'), UUID('7d46bce9-13c1-40bc-9031-c556780bdef6'), UUID('9b390848-a9f4-45c2-a59c-798f52b18536'), UUID('91f4c874-0b15-4c8f-abc7-265355fc752a'), UUID('4e508a5a-ff17-467d-bf7d-3bad4956316e'), UUID('d0644d46-1a49-44ac-b3ac-7f039b22658c'), UUID('902e7697-1ae0-49ff-b811-e51c18a36e3b'), UUID('46160227-22ff-494f-bf9f-f150149f84d2'))]
(Background on this error at: https://sqlalche.me/e/20/dbapi)