# hAIfu backend application

> SoftBank Hackerton 2025의 Hedgehog 팀 백엔드 레포입니다.

- [API](#api)
    - [1. 회원가입](#1-회원가입)
    - [2. 로그인](#2-로그인)
    - [3. 내 정보 조회](#3-내-정보-조회)
    - [4. 서버 상태확인](#4-서버-상태-확인)

## API
### 1. 회원가입
**POST /users/signup**
* **요청 본문 (JSON)**
  ```json
  {
    "login_id": "hoghoghog",
    "password": "1234",
    "nickname": "멧돼지"
  }
  ```
* **응답**
  * 201 Created
    ```json
    {
      "member_id": "mem_ab12cd34",
      "login_id": "hoghoghog",
      "nickname": "멧돼지",
      "role": "USER",
      "created_at": "2025-11-10T03:28:28"
    }
    ```
  * 400 Bad Request → 이미 존재하는 login_id
  * 422 Unprocessable Entity → 필드 누락 또는 잘못된 형식
### 2. 로그인
**POST /users/login**
* **요청 본문 (JSON)**
  ```json
  {
    "login_id": "hoghoghog",
    "password": "1234"
  }
  ```
* **응답**
  * 200 OK
    ```json
    {
      "access_token": "<JWT 토큰>",
      "token_type": "bearer"
    }
    ```
  * 401 Unauthorized → 존재하지 않는 사용자 또는 비밀번호 불일치
### 3. 내 정보 조회
**GET /users/me**
* **요청 헤더**
  ```
  Authorization: Bearer <JWT 토큰>
  ```
* **응답**
  * 200 OK
    ```json
    {
      "member_id": "mem_ab12cd34",
      "login_id": "jaehoon",
      "nickname": "재훈",
      "role": "USER",
      "created_at": "2025-11-10T03:28:28"
    }
    ```
  * 401 Unauthorized → 토큰이 없거나, 유효하지 않거나, 만료된 경우
### 4. 서버 상태 확인
**GET /health**
* **요청 헤더**: 없음
* **응답**
  * 200 OK
    ```json
    { "status": "ok" }
    ```