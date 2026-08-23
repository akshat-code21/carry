INFO:     Application startup complete.
2026-08-23 21:01:08,734 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:10,949 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IJdhuHPZPxdXu0Xo3h551RAHQj "HTTP/1.1 200 OK"
2026-08-23 21:01:10,976 | INFO    | src.auth.dependencies | Session token carries no 'role' claim; syncing admin role via Clerk Backend API public metadata instead (Configure → Sessions → Customize session token → {"role": "{{user.public_metadata.role}}"} avoids the per-minute API lookup). Present claims: ['azp', 'exp', 'fva', 'iat', 'iss', 'nbf', 'sid', 'sts', 'sub', 'v']
INFO:     127.0.0.1:62581 - "GET /api/activity/unread-count HTTP/1.1" 200 OK
2026-08-23 21:01:48,019 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:48,020 | WARNING | src.auth.clerk | Session token verification failed: jwk_kid_mismatch
2026-08-23 21:01:48,161 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:48,161 | WARNING | src.auth.clerk | Session token verification failed: jwk_kid_mismatch
2026-08-23 21:01:48,265 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:48,266 | WARNING | src.auth.clerk | Session token verification failed: jwk_kid_mismatch
2026-08-23 21:01:48,441 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:48,442 | WARNING | src.auth.clerk | Session token verification failed: jwk_kid_mismatch
INFO:     127.0.0.1:62622 - "GET /api/channels HTTP/1.1" 401 Unauthorized
2026-08-23 21:01:48,538 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:48,540 | WARNING | src.auth.clerk | Session token verification failed: jwk_kid_mismatch
2026-08-23 21:01:48,715 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:48,716 | WARNING | src.auth.clerk | Session token verification failed: jwk_kid_mismatch
INFO:     127.0.0.1:62624 - "GET /api/activity/unread-count HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:62625 - "GET /api/videos HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:62626 - "GET /api/themes HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:62623 - "POST /api/usage/events HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:62627 - "GET /api/tickers HTTP/1.1" 401 Unauthorized
2026-08-23 21:01:48,913 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:48,914 | WARNING | src.auth.clerk | Session token verification failed: jwk_kid_mismatch
2026-08-23 21:01:49,062 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/jwks "HTTP/1.1 200 OK"
2026-08-23 21:01:49,063 | WARNING | src.auth.clerk | Session token verification failed: jwk_kid_mismatch
INFO:     127.0.0.1:62636 - "GET /api/tickers/top-etfs HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:62637 - "GET /api/auth/me HTTP/1.1" 401 Unauthorized
2026-08-23 21:01:50,428 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IK2nVaUR8yUJZo1nv6GGCPQiFs "HTTP/1.1 200 OK"
2026-08-23 21:01:50,459 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IK2nVaUR8yUJZo1nv6GGCPQiFs "HTTP/1.1 200 OK"
2026-08-23 21:01:50,518 | INFO    | src.auth.service | Linking Clerk identity user_3IK2nVaUR8yUJZo1nv6GGCPQiFs -> existing user borncancer21@gmail.com
2026-08-23 21:01:50,522 | INFO    | src.auth.service | Linking Clerk identity user_3IK2nVaUR8yUJZo1nv6GGCPQiFs -> existing user borncancer21@gmail.com
2026-08-23 21:01:50,686 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IK2nVaUR8yUJZo1nv6GGCPQiFs "HTTP/1.1 200 OK"
2026-08-23 21:01:50,707 | INFO    | src.auth.service | Linking Clerk identity user_3IK2nVaUR8yUJZo1nv6GGCPQiFs -> existing user borncancer21@gmail.com
2026-08-23 21:01:51,054 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IK2nVaUR8yUJZo1nv6GGCPQiFs "HTTP/1.1 200 OK"
2026-08-23 21:01:51,066 | INFO    | src.auth.service | Linking Clerk identity user_3IK2nVaUR8yUJZo1nv6GGCPQiFs -> existing user borncancer21@gmail.com
2026-08-23 21:01:51,106 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IK2nVaUR8yUJZo1nv6GGCPQiFs "HTTP/1.1 200 OK"
2026-08-23 21:01:51,126 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IK2nVaUR8yUJZo1nv6GGCPQiFs "HTTP/1.1 200 OK"
2026-08-23 21:01:51,135 | INFO    | src.auth.service | Linking Clerk identity user_3IK2nVaUR8yUJZo1nv6GGCPQiFs -> existing user borncancer21@gmail.com
2026-08-23 21:01:51,340 | INFO    | httpx | HTTP Request: GET https://api.clerk.com/v1/users/user_3IK2nVaUR8yUJZo1nv6GGCPQiFs "HTTP/1.1 200 OK"
2026-08-23 21:01:51,349 | INFO    | src.auth.service | Linking Clerk identity user_3IK2nVaUR8yUJZo1nv6GGCPQiFs -> existing user borncancer21@gmail.com