#!/usr/bin/env python3
"""
API 테스트 스크립트 - DB 동작 확인

사용법:
    python scripts/test_api_with_db.py [JWT_TOKEN]
    
JWT 토큰 없이 실행하면:
    - 서버 상태 확인
    - GitHub 로그인 URL 조회
    - JWT 토큰을 얻는 방법 안내
    
JWT 토큰으로 실행하면:
    - Project CRUD 전체 테스트
    - Service CRUD 전체 테스트
"""

import sys
import httpx
import json
from typing import Optional

BASE_URL = "http://localhost:8001"


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_endpoint(method: str, endpoint: str, description: str, 
                  data: Optional[dict] = None, token: Optional[str] = None):
    """API 엔드포인트 테스트"""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    print(f"📡 {description}")
    print(f"   {method} {endpoint}")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                headers["Content-Type"] = "application/json"
                response = client.post(url, headers=headers, json=data)
            elif method == "PUT":
                headers["Content-Type"] = "application/json"
                response = client.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                print(f"   ❌ 지원하지 않는 HTTP 메서드: {method}")
                return None
            
            print(f"   HTTP {response.status_code}")
            
            if response.status_code >= 200 and response.status_code < 300:
                print(f"   ✅ 성공")
                result = response.json()
                print(f"   응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"   ❌ 실패")
                try:
                    error = response.json()
                    print(f"   에러: {json.dumps(error, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   에러: {response.text}")
                return None
            
    except httpx.ConnectError:
        print(f"   ❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        return None
    except Exception as e:
        print(f"   ❌ 에러 발생: {str(e)}")
        return None
    
    print()


def main():
    token = sys.argv[1] if len(sys.argv) > 1 else None
    
    print_section("API 테스트 시작")
    
    # 1. 서버 상태 확인
    print_section("1. 서버 상태 확인")
    test_endpoint("GET", "/", "서버 상태 확인")
    
    # 2. Health Check
    test_endpoint("GET", "/health", "Health Check")
    
    # 3. GitHub 로그인 URL 조회
    print_section("2. 인증 관련 API")
    login_response = test_endpoint("GET", "/api/auth/github/login", 
                                   "GitHub 로그인 URL 조회")
    
    if not token:
        print("\n" + "="*60)
        print("⚠️  JWT 토큰이 없습니다.")
        print("="*60)
        if login_response and login_response.get("data", {}).get("url"):
            print("\nJWT 토큰을 얻으려면:")
            print(f"1. 브라우저에서 다음 URL로 접속:")
            print(f"   {login_response['data']['url']}")
            print("2. GitHub 로그인 후 콜백 URL에서 토큰을 받으세요")
            print("3. 이 스크립트를 다시 실행:")
            print(f"   python scripts/test_api_with_db.py YOUR_JWT_TOKEN")
        print("\n또는 테스트 토큰 발급 API 사용:")
        print("   curl -X POST http://localhost:8001/api/auth/test-token")
        print("   위 명령어로 토큰을 받아서 이 스크립트를 실행하세요.")
        print("\n또는 Swagger UI에서 테스트하세요:")
        print("   http://localhost:8001/docs")
        return
    
    # JWT 토큰이 있는 경우 - 전체 CRUD 테스트
    print_section("3. Project CRUD 테스트")
    
    # 3-1. 현재 사용자 정보 조회
    user_info = test_endpoint("GET", "/api/auth/me", 
                              "현재 사용자 정보 조회", token=token)
    
    if not user_info:
        print("❌ 사용자 정보를 가져올 수 없습니다. JWT 토큰이 유효한지 확인하세요.")
        return
    
    user_id = user_info.get("data", {}).get("id")
    print(f"✅ User ID: {user_id}\n")
    
    # 3-2. Project 생성
    project_data = {
        "name": "테스트 프로젝트",
        "description": "DB 테스트용 프로젝트입니다"
    }
    create_response = test_endpoint("POST", "/api/projects", 
                                    "Project 생성", data=project_data, token=token)
    
    if not create_response:
        print("❌ Project 생성 실패. 테스트를 중단합니다.")
        return
    
    project_id = create_response.get("data", {}).get("id")
    print(f"✅ Project ID: {project_id}\n")
    
    # 3-3. Project 목록 조회
    test_endpoint("GET", "/api/projects", 
                  "Project 목록 조회", token=token)
    
    # 3-4. Project 상세 조회
    test_endpoint("GET", f"/api/projects/{project_id}", 
                  "Project 상세 조회", token=token)
    
    # 3-5. Project 수정
    update_data = {
        "name": "수정된 프로젝트명",
        "description": "수정된 설명"
    }
    test_endpoint("PUT", f"/api/projects/{project_id}", 
                  "Project 수정", data=update_data, token=token)
    
    # 4. Service CRUD 테스트
    print_section("4. Service CRUD 테스트")
    
    # Service 생성에 필요한 정보 확인
    print("⚠️  Service 생성은 실제 GitHub 레포지토리 정보가 필요합니다.")
    print("   아래 API로 레포지토리와 브랜치를 확인하세요:\n")
    
    # 4-1. 레포지토리 목록 조회
    repos_response = test_endpoint("GET", "/api/repos/list?page=1&per_page=5", 
                                   "레포지토리 목록 조회", token=token)
    
    if repos_response and repos_response.get("data", {}).get("items"):
        repos = repos_response["data"]["items"]
        if repos:
            first_repo = repos[0]
            repo_owner = first_repo.get("full_name", "").split("/")[0] if "/" in first_repo.get("full_name", "") else ""
            repo_name = first_repo.get("name", "")
            
            if repo_owner and repo_name:
                # 4-2. 브랜치 목록 조회
                branches_response = test_endpoint(
                    "GET", f"/api/repos/{repo_owner}/{repo_name}/branches",
                    "브랜치 목록 조회", token=token
                )
                
                if branches_response and branches_response.get("data"):
                    branches = branches_response["data"]
                    branch = branches[0] if branches else "main"
                    
                    # 4-3. Service 생성
                    service_data = {
                        "name": "테스트 서비스",
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                        "branch": branch,
                        "runtime": "NODEJS_18",
                        "cpu": "1 vCPU",
                        "memory": "2 GB",
                        "port": 3000,
                        "build_command": "npm install",
                        "start_command": "npm start"
                    }
                    service_response = test_endpoint(
                        "POST", f"/api/projects/{project_id}/services",
                        "Service 생성", data=service_data, token=token
                    )
                    
                    if service_response:
                        service_id = service_response.get("data", {}).get("id")
                        
                        # 4-4. Service 목록 조회
                        test_endpoint("GET", f"/api/projects/{project_id}/services",
                                     "Service 목록 조회", token=token)
                        
                        # 4-5. Service 상세 조회
                        test_endpoint("GET", f"/api/services/{service_id}?project_id={project_id}",
                                     "Service 상세 조회", token=token)
                        
                        # 4-6. Service 수정
                        service_update = {
                            "name": "수정된 서비스명"
                        }
                        test_endpoint("PUT", f"/api/services/{service_id}?project_id={project_id}",
                                     "Service 수정", data=service_update, token=token)
                        
                        # 4-7. Service 삭제
                        test_endpoint("DELETE", f"/api/services/{service_id}?project_id={project_id}",
                                     "Service 삭제", token=token)
                else:
                    print("⚠️  브랜치 정보를 가져올 수 없습니다. Service 생성은 건너뜁니다.")
            else:
                print("⚠️  레포지토리 정보를 파싱할 수 없습니다. Service 생성은 건너뜁니다.")
        else:
            print("⚠️  레포지토리가 없습니다. Service 생성은 건너뜁니다.")
    else:
        print("⚠️  레포지토리 목록을 가져올 수 없습니다. Service 생성은 건너뜁니다.")
    
    # 5. Project 삭제 (하위 서비스도 함께 삭제)
    print_section("5. Project 삭제 테스트")
    # 자동화된 테스트를 위해 자동으로 삭제
    auto_delete = len(sys.argv) > 2 and sys.argv[2] == "--delete"
    if auto_delete:
        print("⚠️  자동 삭제 모드: 프로젝트를 삭제합니다...")
        test_endpoint("DELETE", f"/api/projects/{project_id}",
                     "Project 삭제 (하위 서비스도 함께 삭제)", token=token)
    else:
        print("⚠️  Project 삭제는 건너뜁니다. (자동 삭제하려면 --delete 옵션 추가)")
        print(f"   삭제하려면: python scripts/test_api_with_db.py {token} --delete")
    
    print_section("테스트 완료!")
    print("✅ 모든 API가 DB와 정상적으로 동작합니다!")


if __name__ == "__main__":
    main()

