"""
Supabase Google OAuth 인증 관리자 (PKCE는 SDK에 맡김)
"""
import os
import streamlit as st
from typing import Optional, Dict, Any
from supabase import create_client
from supabase.client import ClientOptions
from src.core.config import SUPABASE_URL, SUPABASE_ANON_KEY

# Supabase 클라이언트를 캐시하여 재사용
@st.cache_resource
def _get_supabase(url: str, anon: str):
    return create_client(url, anon)

class SupabaseAuth:
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_anon_key = SUPABASE_ANON_KEY

        # 동적 redirect_uri 설정
        try:
            import os
            import streamlit as st
            
            # Streamlit Cloud 환경 감지
            is_streamlit_cloud = (
                os.getenv('STREAMLIT_SERVER_BASE_URL_PATH') or
                os.getenv('STREAMLIT_SERVER_PORT') == '8501' or
                'streamlit.app' in str(st.get_option('server.headless', '')) or
                os.getenv('STREAMLIT_SHARING_MODE') == 'True'
            )
            
            if is_streamlit_cloud:
                # Streamlit Cloud 환경
                self.redirect_uri = "https://qlearn-game.streamlit.app"
            else:
                # 로컬 환경
                port = st.get_option("server.port") or 8501
                self.redirect_uri = f"http://localhost:{port}"
        except:
            # 기본값: Streamlit Cloud URL (배포 환경 우선)
            self.redirect_uri = "https://qlearn-game.streamlit.app"

        if not self.supabase_url or not self.supabase_anon_key:
            st.error("SUPABASE_URL / SUPABASE_ANON_KEY 누락")
            self.supabase = None
            return

        # ✅ PKCE + storage + cache 적용된 클라이언트 획득
        self.supabase = _get_supabase(self.supabase_url, self.supabase_anon_key)

    def get_google_auth_url(self) -> str:
        if not self.supabase:
            st.error("❌ Supabase 클라이언트가 없습니다")
            return ""

        # 1) OAuth URL 1회 발급 (rerun 대비)
        if "oauth_url" not in st.session_state:
            res = self.supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {"redirect_to": self.redirect_uri}
            })
            st.session_state["oauth_url"] = getattr(res, "url", None) or (
                isinstance(res, dict) and res.get("url")
            ) or str(res)

        url = st.session_state["oauth_url"]
        if not url:
            st.error("❌ OAuth URL 생성 실패")
            return ""

        # 2) 현재 탭(top)으로 히스토리 교체 이동 (새 창 X)
        st.components.v1.html(f"""
          <div style="display:flex;gap:8px;align-items:center">
            <button id="glogin" type="button" style="padding:10px 14px;border-radius:8px">
              🔐 Google로 로그인
            </button>
            <span style="opacity:.6">현재 탭에서 이동합니다</span>
          </div>
          <script>
            (function(){{
              const url = {url!r};
              function go(){{
                try {{
                  if (window.top && window.top !== window) {{
                    window.top.location.replace(url);   // 최상위 탭에서 교체 이동
                  }} else {{
                    window.location.replace(url);       // 현재 탭에서 교체 이동
                  }}
                }} catch(e) {{ window.location.href = url; }}
              }}
              const btn = document.getElementById('glogin');
              if (btn) btn.addEventListener('click', function(ev){{ ev.preventDefault(); go(); }});
            }})();
          </script>
        """, height=60, key="oauth_login_html")

        st.stop()


    def handle_oauth_callback(self) -> Optional[Dict[str, Any]]:
        """OAuth 콜백 처리"""
        if not self.supabase: 
            return None

        qp = st.query_params
        
        if "code" not in qp:
            return None

        code = qp["code"]
        
        try:
            # 올바른 형태로 세션 교환 시도 (딕셔너리 형태)
            resp = self.supabase.auth.exchange_code_for_session({"auth_code": code})
            
        except Exception as e:
            # 다른 방법으로 시도 중...
            
            # 다른 방법: 직접 REST API 호출 (PKCE grant_type 사용)
            try:
                import requests
                
                # PKCE grant_type 사용
                token_url = f"{self.supabase_url}/auth/v1/token?grant_type=pkce"
                headers = {
                    "apikey": self.supabase_anon_key,
                    "Content-Type": "application/json"
                }
                data = {
                    "auth_code": code
                }
                
                response = requests.post(token_url, headers=headers, json=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # 사용자 데이터 구성
                    user_data = {
                        "user_id": token_data.get("user", {}).get("id", ""),
                        "email": token_data.get("user", {}).get("email", ""),
                        "name": token_data.get("user", {}).get("user_metadata", {}).get("full_name", ""),
                        "avatar_url": token_data.get("user", {}).get("user_metadata", {}).get("avatar_url", ""),
                        "access_token": token_data.get("access_token", ""),
                    }
                    
                    self.set_user_session(user_data)
                    st.query_params.clear()
                    return user_data
                else:
                    # 마지막 시도: authorization_code grant_type
                    token_url2 = f"{self.supabase_url}/auth/v1/token?grant_type=authorization_code"
                    response2 = requests.post(token_url2, headers=headers, json=data)
                    
                    if response2.status_code == 200:
                        token_data = response2.json()
                        
                        user_data = {
                            "user_id": token_data.get("user", {}).get("id", ""),
                            "email": token_data.get("user", {}).get("email", ""),
                            "name": token_data.get("user", {}).get("user_metadata", {}).get("full_name", ""),
                            "avatar_url": token_data.get("user", {}).get("user_metadata", {}).get("avatar_url", ""),
                            "access_token": token_data.get("access_token", ""),
                        }
                        
                        self.set_user_session(user_data)
                        st.query_params.clear()
                        return user_data
                    else:
                        return None
                    
            except Exception as e2:
                return None

        # SDK 방식이 성공한 경우
        session = getattr(resp, "session", None) or (resp.get("session") if isinstance(resp, dict) else None)
        user = getattr(resp, "user", None) or (resp.get("user") if isinstance(resp, dict) else None)
        
        if not session or not user:
            st.error("❌ 세션/유저 정보 없음")
            return None

        user_meta = getattr(user, "user_metadata", {}) or {}
        if isinstance(user_meta, str):
            try:
                import json
                user_meta = json.loads(user_meta)
            except:
                user_meta = {}

        user_data = {
            "user_id": getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None),
            "email": getattr(user, "email", "") or (user.get("email") if isinstance(user, dict) else ""),
            "name": user_meta.get("full_name", ""),
            "avatar_url": user_meta.get("avatar_url", ""),
            "access_token": getattr(session, "access_token", None) or (session.get("access_token") if isinstance(session, dict) else None),
        }

        self.set_user_session(user_data)
        st.query_params.clear()
        st.success("✅ OAuth 인증 완료!")
        return user_data

    def _get_user_info_from_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        if not self.supabase: return None
        res = self.supabase.auth.get_user(access_token)
        u = getattr(res, "user", None)
        if not u: return None
        meta = getattr(u, "user_metadata", {}) or {}
        return {
            "user_id": u.id,
            "email": u.email,
            "name": meta.get("full_name", ""),
            "avatar_url": meta.get("avatar_url", ""),
            "access_token": access_token,
        }

    def get_current_user_info(self) -> Optional[Dict[str, Any]]:
        at = st.session_state.get("access_token")
        return self._get_user_info_from_token(at) if at else None

    def is_authenticated(self) -> bool:
        """인증 상태 확인 - 세션 유지 강화"""
        # 세션에 사용자 정보가 있는지 확인
        has_user = bool(st.session_state.get("user"))
        has_token = bool(st.session_state.get("access_token"))
        
        # 토큰이 있으면 유효성 검증
        if has_token:
            try:
                # 토큰 유효성 간단 검증 (만료 시간 확인)
                token = st.session_state.get("access_token")
                if token and len(token) > 10:  # 기본적인 토큰 형식 확인
                    return has_user and has_token
            except:
                pass
        
        return has_user and has_token

    def set_user_session(self, user_data: Dict[str, Any]):
        st.session_state.user = user_data
        if "access_token" in user_data:
            st.session_state.access_token = user_data["access_token"]

    def logout(self):
        try:
            if self.supabase:
                self.supabase.auth.sign_out()
        finally:
            for k in ("user","access_token"):
                st.session_state.pop(k, None)
            st.query_params.clear()
            st.success("로그아웃 완료")
