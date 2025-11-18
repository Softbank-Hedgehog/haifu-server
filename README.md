# hAIfu backend application

> SoftBank Hackerton 2025의 Hedgehog 팀 백엔드 레포입니다.

## 목차

- [환경 설정](#환경-설정)
- [로컬 개발 환경 구성](#로컬-개발-환경-구성)
- [API](#api)
    - 인증
      - [Github 로그인 URL 조회](#github-로그인-url-조회)
      - [Github OAuth 콜백](#github-oauth-콜백)
      - [현재 사용자 정보 조회](#현재-사용자-정보-조회)
    - 레포지토리
      - [레포지토리 목록 조회](#레포지토리-목록-조회)
      - [레포지토리 상세 조회](#레포지토리-상세-조회)
    - 기타
      - [서버 상태 확인](#7-서버-상태-확인)

## 환경 설정

### 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 필요한 환경변수를 설정하세요.

```bash
# .env.example 파일 복사
cp .env.example .env

# .env 파일 수정 (실제 값 입력)
```

**필수 환경변수:**

| 변수명 | 설명 | 발급 방법 |
|--------|------|----------|
| `GITHUB_CLIENT_ID` | GitHub OAuth Client ID | [GitHub OAuth App 생성](https://github.com/settings/developers) |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth Client Secret | GitHub OAuth App 페이지에서 발급 |
| `JWT_SECRET_KEY` | JWT 토큰 서명용 비밀키 | `openssl rand -hex 32` 명령어로 생성 |
| `DYNAMODB_ENDPOINT` | DynamoDB 엔드포인트 (로컬: `http://localhost:8000`) | - |

**자세한 환경변수 설명은 [팀 노션 .Env 페이지](팀_노션_링크) 참고**

## 로컬 개발 환경 구성

### 1. Python 가상환경 생성

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. DynamoDB Local 실행

```bash
# Docker Compose로 DynamoDB Local 실행
docker-compose up -d

# 테이블 생성
python scripts/create_local_tables.py
```

**테이블 확인:**
```bash
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

### 4. FastAPI 서버 실행

```bash
# 개발 서버 실행 (자동 리로드)
uvicorn app.main:app --reload --port 8001

# Swagger UI 접속
# http://localhost:8001/docs
```

### 5. 테스트

```bash
# 서버 상태 확인
curl http://localhost:8001/

# GitHub 로그인 URL 조회 (JWT 토큰 필요 없음)
curl http://localhost:8001/api/auth/github/login
```

## API

### GitHub 로그인 URL 조회

**GET /api/auth/github/login**

- **요청 헤더**: 없음
- **응답**
    - 200 OK
        
        ```json
        {  "url": "https://github.com/login/oauth/authorize?client_id=..."}
        ```

프론트 측에서는 다음과 같이 활용하시면 됩니다.
```typescript
const response = await fetch('/api/auth/github/login');
const data = await response.json();
// { "url": "https://github.com/login/oauth/authorize?..." }

// 사용자를 GitHub 로그인 페이지로 리디렉션
window.location.href = data.url;
```

### GitHub OAuth 콜백

**GET /api/auth/github/callback**

- **쿼리 파라미터**
    - `code`: GitHub에서 발급한 authorization code
- **응답**
    - 302 Found (Redirect)
        - 성공 시: `{FRONTEND_URL}/callback?token={jwt_token}` 으로 리다이렉트
        - 실패 시: `{FRONTEND_URL}/callback?error={error_type}` 으로 리다이렉트
    
    **에러 타입:**
    - `failed_to_get_token`: GitHub에서 access token 발급 실패
    - `failed_to_get_user_info`: GitHub API에서 사용자 정보 조회 실패
    - `oauth_error`: GitHub OAuth 에러
    - `unexpected_error`: 예상치 못한 서버 에러

프론트엔드에서는 `/callback` 페이지에서 쿼리 파라미터로 전달받은 `token`(JWT 토큰)을 저장해 둔 후, 사용자 정보가 필요한 API 호출 시
```
Authorization: Bearer <access_token>
```
형식으로 헤더에 담아 서버에 전달하면 됩니다.

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

프론트 측에서는 다음과 같이 활용 하시면 됩니다.

```typescript
// 사용자가 레포 목록에서 선택
const repo = { full_name: "facebook/react" };
const [owner, repoName] = repo.full_name.split('/');

// API 호출
const response = await fetch(`/api/repos/${owner}/${repoName}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

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


**AI 챗봇에 유용한 정보:**

- `language`: 주요 언어
- `topics`: 토픽/태그 (사용자가 직접 설정한 키워드)
- `name`: 레포지토리 이름 (프로젝트 성격 파악)
- `description`: 사용자가 작성한 레포지토리 설명
- `default_branch`: 기본 브랜치 (분석할 브랜치 결정)

### 서버 상태 확인

**GET /health**

- **요청 헤더**: 없음
- **응답**
    - 200 OK

## 응답 포맷

모든 API는 일관된 응답 포맷을 사용합니다.

**특징:**
- 명확한 역할: `message`(사용자용), `error_code`(개발자용)
- 일관성: 성공/실패 모두 동일한 패턴

### 성공 응답

```json
{
  "success": true,
  "message": "Success",
  "data": {
    // 실제 데이터
  }
}
```

### 리스트 응답

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [/* 배열 데이터 */],
    "page": 1,
    "per_page": 30,
    "total": 100
  }
}
```

### 에러 응답

```json
{
  "success": false,
  "message": "Error message",
  "error_code": "ERROR_CODE"
}
```

## 예외처리

체계적인 예외처리로 일관된 에러 응답을 제공합니다.

### 에러 코드

| HTTP 상태 | 에러 코드 | 설명 |
|-----------|-----------|------|
| 401 | `AUTH_ERROR` | 인증 실패 |
| 401 | `GITHUB_API_ERROR` | GitHub API 인증 실패 |
| 404 | `REPO_NOT_FOUND` | 레포지토리 없음 |
| 404 | `FILE_NOT_FOUND` | 파일 없음 |
| 400 | `GITHUB_API_ERROR` | GitHub API 요청 실패 |
| 500 | `INTERNAL_ERROR` | 서버 내부 오류 |

### 인증 에러 예시

```json
{
  "success": false,
  "message": "GitHub token not found",
  "error_code": "AUTH_ERROR",
  "data": null
}
```

### GitHub API 에러 예시

```json
{
  "success": false,
  "message": "Repository facebook/react not found",
  "error_code": "REPO_NOT_FOUND",
  "data": null
}
```

## 아키텍처

### 프로젝트 구조

```
app/
├── core/              # 핵심 설정 및 보안
│   ├── __init__.py
│   ├── config.py      # 환경 설정
│   ├── security.py    # JWT 토큰 처리
│   └── exceptions.py  # 커스텀 예외 클래스
├── routers/           # API 라우터
│   ├── __init__.py
│   ├── auth.py        # 인증 관련 API
│   ├── repos.py       # 레포지토리 관련 API
│   └── health.py      # 헬스체크 API
├── schemas/           # Pydantic 스키마
│   ├── __init__.py
│   ├── auth.py        # 인증 관련 데이터 모델
│   └── common.py      # 공통 응답 스키마
├── service/           # 비즈니스 로직 서비스
│   ├── __init__.py
│   ├── auth_service.py    # 인증 비즈니스 로직
│   └── github_service.py  # GitHub API 비즈니스 로직
├── __init__.py
├── database.py        # 데이터베이스 설정
└── main.py           # FastAPI 앱 진입점
```

### 서비스 레이어

비즈니스 로직은 `app/service/` 디렉토리의 서비스 레이어로 분리되어 있습니다:

- **AuthService**: GitHub OAuth, JWT 토큰 관리
- **GitHubService**: GitHub API 호출, 데이터 변환

### 보안

- JWT 토큰 기반 인증
- GitHub OAuth 2.0
- CORS 설정으로 허용된 도메인만 접근 가능
- 환경변수/Parameter Store를 통한 민감 정보 관리