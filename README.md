# hAIfu backend application

> SoftBank Hackerton 2025의 Hedgehog 팀 백엔드 레포입니다.

- [API](#api)
    - 인증
      - [회원가입](#github-로그인-url-조회)
      - [로그인](#github-oauth-콜백)
      - [내 정보 조회](#현재-사용자-정보-조회)
    - 레포지토리
      - [레포지토리 목록 조회](#레포지토리-목록-조회)
      - [레포지토리 상세 조회](#레포지토리-상세-조회)
    - 기타
      - [서버 상태 확인](#7-서버-상태-확인)

## API

### GitHub 로그인 URL 조회

**GET /api/auth/github/login**

- **요청 헤더**: 없음
- **응답**
    - 200 OK
        
        ```json
        {  "url": "https://github.com/login/oauth/authorize?client_id=..."}
        ```
        

### GitHub OAuth 콜백

**GET /api/auth/github/callback**

- **쿼리 파라미터**
    - `code`: GitHub에서 발급한 authorization code
- **응답**
    - 200 OK
        
        ```json
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer",
          "user": {
            "id": 123456,
            "username": "user",
            "email": "user@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/123456",
            "name": "User Name"
          }
        }
        ```
        
    - 400 Bad Request → 잘못된 code 또는 GitHub OAuth 실패

### 현재 사용자 정보 조회

**GET /api/auth/me**

- **요청 헤더**
    
    ```
    Authorization: Bearer <JWT 토큰>
    ```
    
- **응답**
    - 200 OK
        
        ```json
        {
          "id": 123456,
          "username": "user",
          "email": "user@example.com",
          "avatar_url": "https://avatars.githubusercontent.com/u/123456",
          "name": "User Name"
        }
        ```
        
    - 401 Unauthorized → 토큰이 없거나 유효하지 않은 경우

### 레포지토리 목록 조회

**GET /api/repos/list**

- **요청 헤더**
    
    ```
    Authorization: Bearer <JWT 토큰>
    ```
    
- **쿼리 파라미터**
    - `page`: 페이지 번호 (기본값: 1)
    - `per_page`: 페이지당 개수 (기본값: 30)
- **응답**
    - 200 OK
        
        ```json
        {
          "repositories": [
            {
              "id": 123456789,
              "name": "my-react-app",
              "full_name": "user/my-react-app",
              "description": "A simple React app",
              "html_url": "https://github.com/user/my-react-app",
              "language": "JavaScript",
              "private": false,
              "updated_at": "2024-01-15T10:00:00Z"
            }
          ],
          "page": 1,
          "total": 10
        }
        ```
        
    - 401 Unauthorized → 유효하지 않은 토큰

### 레포지토리 상세 조회

**GET /api/repos/{owner}/{repo}**

- **요청 헤더**
    
    ```
    Authorization: Bearer <JWT 토큰>
    ```
    
- **경로 파라미터**
    - `owner`: 레포지토리 소유자
    - `repo`: 레포지토리 이름
- **응답**
    - 200 OK
        
        ```json
        {
          "id": 123456789,
          "name": "my-react-app",
          "full_name": "user/my-react-app",
          "description": "A simple React app",
          "html_url": "https://github.com/user/my-react-app",
          "clone_url": "https://github.com/user/my-react-app.git",
          "ssh_url": "git@github.com:user/my-react-app.git",
          "default_branch": "main",
          "language": "JavaScript",
          "languages_url": "https://api.github.com/repos/user/my-react-app/languages",
          "private": false,
          "owner": {
            "login": "user",
            "avatar_url": "https://avatars.githubusercontent.com/u/123456"
          },
          "topics": ["react", "typescript"],
          "size": 2048,
          "stargazers_count": 15,
          "watchers_count": 15,
          "forks_count": 3,
          "open_issues_count": 2,
          "created_at": "2023-01-15T10:00:00Z",
          "updated_at": "2024-01-15T10:00:00Z",
          "pushed_at": "2024-01-15T15:30:00Z"
        }
        ```
        
    - 404 Not Found → 레포지토리를 찾을 수 없음
    - 401 Unauthorized → 유효하지 않은 토큰

### 서버 상태 확인

**GET /health**

- **요청 헤더**: 없음
- **응답**
    - 200 OK