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

        try:
            port = st.get_option("server.port") or 8501
            self.redirect_uri = f"http://localhost:{port}"
        except:
            self.redirect_uri = "http://localhost:8501"

        if not self.supabase_url or not self.supabase_anon_key:
            st.error("SUPABASE_URL / SUPABASE_ANON_KEY 누락")
            self.supabase = None
            return

        # ✅ PKCE + storage + cache 적용된 클라이언트 획득
        self.supabase = _get_supabase(self.supabase_url, self.supabase_anon_key)

    def get_google_auth_url(self) -> str:
        """Google OAuth URL 생성"""
        if not self.supabase: 
            st.error("❌ Supabase 클라이언트가 없습니다")
            return ""
        
        try:
            st.info("🔄 Google OAuth URL 생성 중...")
            
            # 가장 간단한 형태로 OAuth URL 생성
            res = self.supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": self.redirect_uri
                }
            })
            
            # URL 추출
            if hasattr(res, 'url'):
                url = res.url
            elif isinstance(res, dict) and 'url' in res:
                url = res['url']
            else:
                url = str(res)
            
            st.info(f"🔗 Google OAuth URL 생성 완료")
            return url
            
        except Exception as e:
            st.error(f"❌ Google OAuth URL 생성 오류: {str(e)}")
            return ""

    def handle_oauth_callback(self) -> Optional[Dict[str, Any]]:
        """OAuth 콜백 처리"""
        if not self.supabase: 
            return None

        qp = st.query_params
        st.info(f"🔍 콜백 파라미터: {dict(qp)}")
        
        if "code" not in qp:
            st.info("ℹ️ code 파라미터 없음")
            return None

        code = qp["code"]
        st.info(f"✅ 인증 코드 받음: {code[:20]}...")
        
        try:
            # 올바른 형태로 세션 교환 시도 (딕셔너리 형태)
            st.info("🔄 세션 교환 시도 중...")
            resp = self.supabase.auth.exchange_code_for_session({"auth_code": code})
            st.info("✅ 세션 교환 성공!")
            
        except Exception as e:
            st.error(f"❌ 세션 교환 실패: {e}")
            st.info("🔄 다른 방법으로 시도 중...")
            
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
                st.info(f"🔍 REST API 응답: {response.status_code}")
                st.info(f"🔍 REST API 응답 내용: {response.text}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    st.info("✅ REST API 토큰 교환 성공!")
                    
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
                    st.success("✅ OAuth 인증 완료!")
                    return user_data
                else:
                    st.error(f"❌ REST API 실패: {response.text}")
                    
                    # 마지막 시도: authorization_code grant_type
                    st.info("🔄 authorization_code grant_type으로 재시도...")
                    token_url2 = f"{self.supabase_url}/auth/v1/token?grant_type=authorization_code"
                    response2 = requests.post(token_url2, headers=headers, json=data)
                    st.info(f"🔍 재시도 응답: {response2.status_code}")
                    st.info(f"🔍 재시도 내용: {response2.text}")
                    
                    if response2.status_code == 200:
                        token_data = response2.json()
                        st.info("✅ 재시도 성공!")
                        
                        user_data = {
                            "user_id": token_data.get("user", {}).get("id", ""),
                            "email": token_data.get("user", {}).get("email", ""),
                            "name": token_data.get("user", {}).get("user_metadata", {}).get("full_name", ""),
                            "avatar_url": token_data.get("user", {}).get("user_metadata", {}).get("avatar_url", ""),
                            "access_token": token_data.get("access_token", ""),
                        }
                        
                        self.set_user_session(user_data)
                        st.query_params.clear()
                        st.success("✅ OAuth 인증 완료!")
                        return user_data
                    else:
                        st.error(f"❌ 재시도도 실패: {response2.text}")
                        return None
                    
            except Exception as e2:
                st.error(f"❌ REST API 방식도 실패: {e2}")
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
        return bool(st.session_state.get("user") and st.session_state.get("access_token"))

    def set_user_session(self, user_data: Dict[str, Any]):
        st.session_state.user = user_data
        if "access_token" in user_data:
            st.session_state.access_token = user_data["access_token"]
        st.info(f"🔧 세션 저장: {user_data.get('email','N/A')}")

    def logout(self):
        try:
            if self.supabase:
                self.supabase.auth.sign_out()
        finally:
            for k in ("user","access_token"):
                st.session_state.pop(k, None)
            st.query_params.clear()
            st.success("로그아웃 완료")
