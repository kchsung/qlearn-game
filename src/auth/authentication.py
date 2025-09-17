# src/auth/authentication.py
"""
사용자 인증 및 세션 관리 (Supabase Google OAuth 통합)
"""

import streamlit as st
from typing import Optional, Dict, Any
from .supabase_auth import SupabaseAuth


class AuthenticationManager:
    """사용자 인증 관리자 (Supabase Google OAuth)"""
    
    def __init__(self):
        self.supabase_auth = SupabaseAuth()
    
    def handle_google_login(self):
        """Google 로그인 처리"""
        try:
            # URL에 code가 있는지 확인
            if 'code' in st.query_params:
                # OAuth 콜백 처리
                st.info("🔄 OAuth 콜백을 처리하는 중...")
                user_data = self.supabase_auth.handle_oauth_callback()
                
                if user_data:
                    st.info("Google 인증 성공! 사용자 정보를 동기화하는 중...")
                    # Supabase 데이터베이스에 사용자 정보 저장/업데이트
                    user_id = self._sync_user_to_supabase_db(user_data)
                    
                    if user_id:
                        # 세션 설정 (순서 중요!)
                        st.session_state.user_id = user_id
                        self.supabase_auth.set_user_session(user_data)
                        
                        # 세션 상태 강제 유지
                        st.session_state['login_completed'] = True
                        st.session_state['user_email'] = user_data.get('email', '')
                        
                        # 디버깅 정보
                        st.info(f"✅ 세션 설정 완료 - user_id: {user_id}")
                        st.info(f"✅ Supabase 사용자: {user_data.get('email', 'N/A')}")
                        st.info(f"✅ 세션 상태 확인: {st.session_state.get('user_id')}")
                        
                        st.success("🎉 Google 로그인 성공! 게임을 시작하세요!")
                        st.balloons()
                        
                        # URL 파라미터 정리
                        st.query_params.clear()
                        
                        # 즉시 리다이렉트하지 말고 잠시 대기
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 사용자 정보 동기화 실패. 다시 시도해주세요.")
                else:
                    st.error("❌ OAuth 콜백 처리 실패")
            else:
                # Google OAuth URL 생성 및 리다이렉트
                st.info("🔄 Google OAuth URL 생성 중...")
                auth_url = self.supabase_auth.get_google_auth_url()
                if auth_url:
                    st.info("Google 로그인 페이지로 이동합니다...")
                    
                    # 더 안정적인 리다이렉트 방법
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px;">
                        <h3>🔐 Google 로그인</h3>
                        <p>Google 계정으로 로그인하려면 아래 버튼을 클릭하세요.</p>
                        <a href="{auth_url}" target="_self" style="
                            display: inline-block;
                            background: #4285f4;
                            color: white;
                            padding: 12px 24px;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: bold;
                            margin: 10px;
                        ">Google로 로그인</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 자동 리다이렉트도 시도
                    st.markdown(f"""
                    <script>
                    setTimeout(function() {{
                        window.location.href = '{auth_url}';
                    }}, 2000);
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.info("2초 후 자동으로 Google 로그인 페이지로 이동합니다...")
                else:
                    st.error("❌ Google 로그인 URL 생성 실패. 설정을 확인해주세요.")
                        
        except Exception as e:
            st.error(f"❌ Google 로그인 중 오류 발생: {str(e)}")
            st.error("디버깅 정보: Supabase 설정을 확인해주세요.")
    
    def _sync_user_to_supabase_db(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Supabase 사용자 정보를 Supabase DB에 동기화"""
        try:
            from src.core.database import GameDatabase
            
            user_id = user_data['user_id']
            email = user_data['email']
            name = user_data.get('name', '')
            avatar_url = user_data.get('avatar_url', '')
            
            # Supabase DB 클라이언트 생성
            db = GameDatabase()
            
            # 사용자 프로필 확인
            existing_profile = db.get_user_profile(user_id)
            
            if not existing_profile:
                # 새 사용자 생성
                success = db.create_user_profile(user_id, name, email, avatar_url)
                if not success:
                    st.error("사용자 프로필 생성 실패")
                    return None
            else:
                # 기존 사용자 정보 업데이트
                updates = {
                    'username': name,
                    'email': email,
                    'profile_image': avatar_url
                }
                success = db.update_user_profile(user_id, updates)
                if not success:
                    st.error("사용자 프로필 업데이트 실패")
                    return None
            
            return user_id
            
        except Exception as e:
            st.error(f"사용자 정보 동기화 중 오류: {str(e)}")
            return None
    
    def logout(self):
        """사용자 로그아웃"""
        try:
            # Supabase 로그아웃
            self.supabase_auth.logout()
            
            # 모든 인증 관련 세션 상태 정리
            auth_keys = [
                'user_id', 'user_profile', 'user', 'access_token', 
                'login_completed', 'user_email', 'supabase_user'
            ]
            
            for key in auth_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            # 디버깅 정보도 정리
            if 'debug_auth' in st.session_state:
                del st.session_state.debug_auth
            
            st.success("✅ 로그아웃 완료!")
            st.info("다시 로그인하려면 사이드바의 Google 로그인 버튼을 클릭하세요.")
            
        except Exception as e:
            st.error(f"로그아웃 중 오류: {str(e)}")
            # 오류가 발생해도 세션은 정리
            for key in list(st.session_state.keys()):
                if key in ['user_id', 'user_profile', 'user', 'access_token', 
                          'login_completed', 'user_email', 'supabase_user', 'debug_auth']:
                    del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        # 여러 방법으로 인증 상태 확인
        has_user_id = 'user_id' in st.session_state and st.session_state.user_id
        has_supabase_user = self.supabase_auth.is_authenticated()
        has_login_completed = st.session_state.get('login_completed', False)
        has_user_email = st.session_state.get('user_email', '')
        
        # 디버깅용 로그 (개발 중에만)
        if hasattr(st, 'session_state') and st.session_state.get('debug_auth', False):
            st.write(f"🔍 인증 상태 디버깅:")
            st.write(f"- user_id: {st.session_state.get('user_id', 'None')}")
            st.write(f"- supabase user: {has_supabase_user}")
            st.write(f"- login_completed: {has_login_completed}")
            st.write(f"- user_email: {has_user_email}")
            st.write(f"- session keys: {list(st.session_state.keys())}")
        
        # 인증 성공 조건: user_id가 있거나 login_completed가 True
        return (has_user_id and has_supabase_user) or (has_login_completed and has_user_email)
    
    def get_current_user_id(self) -> Optional[str]:
        """현재 사용자 ID 반환"""
        return st.session_state.get('user_id')
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """현재 사용자 정보 반환 (Supabase)"""
        return self.supabase_auth.get_current_user()
    
    def get_current_user_profile(self) -> Optional[Dict[str, Any]]:
        """현재 사용자 프로필 반환 (로컬 DB)"""
        return st.session_state.get('user_profile')
    
    def set_user_session(self, user_id: str, user_profile: Dict[str, Any] = None):
        """사용자 세션 설정"""
        st.session_state.user_id = user_id
        if user_profile:
            st.session_state.user_profile = user_profile
    
    def validate_session(self) -> bool:
        """세션 유효성 검증"""
        if not self.is_authenticated():
            return False
        
        # Supabase 토큰 유효성 확인
        if not self.supabase_auth.refresh_token_if_needed():
            return False
        
        # 로컬 DB에서 사용자 존재 확인
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (st.session_state.user_id,))
            user = cursor.fetchone()
            conn.close()
            
            return user is not None
        except Exception:
            return False
