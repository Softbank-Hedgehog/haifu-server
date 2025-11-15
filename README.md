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

#### 응답 필드 정보

기본정보

| 필드 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| `id` | number | GitHub 레포지토리 고유 ID | `123456789` |
| `name` | string | 레포지토리 이름 | `"my-react-app"` |
| `full_name` | string | owner/repo 형태의 전체 이름 | `"user/my-react-app"` |
| `description` | string | 레포 설명 (사용자가 작성) | `"A simple React todo app"` |

URL 정보

| 필드 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| `html_url` | string | 브라우저에서 볼 수 있는 웹 URL | `"<https://github.com/user/my-app>"` |
| `clone_url` | string | HTTPS clone URL | `"<https://github.com/user/my-app.git>"` |
| `ssh_url` | string | SSH clone URL | `"git@github.com:user/my-app.git"` |

코드 정보

| 필드 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| `language` | string | GitHub이 감지한 주요 언어 | `"JavaScript"` |
| `languages_url` | string | 모든 언어 비율 조회 API URL | `"<https://api.github.com/repos/.../languages>"` |
| `topics` | array | 레포에 설정된 토픽/태그 | `["react", "typescript", "pwa"]` |
| `default_branch` | string | 기본 브랜치 이름 | `"main"` |

소유자 정보

| 필드 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| `owner.login` | string | GitHub 사용자명 | `"user"` |
| `owner.avatar_url` | string | 프로필 이미지 URL | `"<https://avatars.githubusercontent.com/>..."` |
| `private` | boolean | 비공개 레포 여부 | `false` |

통계 정보

| 필드 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| `size` | number | 레포지토리 크기 (KB) | `2048` |
| `stargazers_count` | number | 스타(⭐) 개수 | `150` |
| `watchers_count` | number | 와처 수 | `150` |
| `forks_count` | number | 포크 횟수 | `25` |
| `open_issues_count` | number | 열린 이슈 개수 | `5` |

시간 정보

| 필드 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| `created_at` | string (ISO 8601) | 레포 생성 시간 | `"2023-01-15T10:00:00Z"` |
| `updated_at` | string (ISO 8601) | 레포 메타데이터 마지막 업데이트 | `"2024-01-15T10:00:00Z"` |
| `pushed_at` | string (ISO 8601) | 마지막 코드 푸시 시간 | `"2024-01-15T15:30:00Z"` |


AI 챗봇에게 유용할 것 같은 정보는 아래와 같습니다.

- `language`: 주요 언어
- `topics`: 토픽/태그. 사용자가 직접 설정한 키워드
- `name`: 레포지토리 이름 → 이름에서 힌트를 얻을 수 있음
- `description`: 설명 사용자가 작성한 레포지토리 설명
- `default_branch`: 기본 브랜치. 어느 브랜치 분석할지 결정

### 서버 상태 확인

**GET /health**

- **요청 헤더**: 없음
- **응답**
    - 200 OK