# main.py
"""
AI Master Quest - AI 활용능력평가 게임
메인 실행 파일
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# .env 파일 로드 (로컬 환경용)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

import streamlit as st
from src.app import AIAssessmentGame
from src.core.config import validate_environment

# 페이지 설정
st.set_page_config(
    page_title="AI Master Quest - AI 활용능력평가 게임",
    page_icon="🎮",
    layout="wide"
)

# CSS 스타일
st.markdown("""
<style>
/* Pretendard 폰트 적용 */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

/* 전체 폰트 설정 */
* {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
}

/* Streamlit 기본 요소들 폰트 적용 */
.stApp {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stMarkdown {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stTextInput > div > div > input {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stTextArea > div > div > textarea {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stSelectbox > div > div > select {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stButton > button {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stRadio > div > label {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stCheckbox > div > label {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stMetric > div > div > div {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.stProgress > div > div > div > div {
    background-image: linear-gradient(to right, #4CAF50, #45a049);
}

.achievement-badge {
    display: inline-block;
    padding: 5px 10px;
    margin: 2px;
    border-radius: 15px;
    background-color: #f0f0f0;
    font-size: 14px;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

.level-badge {
    font-size: 24px;
    font-weight: bold;
    color: #4CAF50;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 사이드바 폰트 */
.css-1d391kg {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 헤더 폰트 */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 테이블 폰트 */
.stDataFrame {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 알림 메시지 폰트 */
.stAlert {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 탭 폰트 */
.stTabs > div > div > div > button {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
}

/* 모든 툴팁 완전 제거 */
*[title] {
    title: none !important;
}

*[title]:hover::after {
    display: none !important;
}

*[title]:hover::before {
    display: none !important;
}

/* Streamlit 개발 모드 툴팁 숨기기 */
[data-testid="stTooltip"] {
    display: none !important;
    visibility: hidden !important;
}

/* 위젯 key 툴팁 숨기기 */
.stTooltip {
    display: none !important;
    visibility: hidden !important;
}

/* 개발 모드 디버깅 정보 숨기기 */
[title*="key"] {
    display: none !important;
    visibility: hidden !important;
}

/* 모든 title 속성 제거 */
* {
    title: none !important;
}

/* 사이드바 영역의 모든 툴팁 숨기기 */
.css-1d391kg *[title] {
    title: none !important;
}

/* 브라우저 기본 툴팁 완전 차단 */
*[title]:hover {
    pointer-events: none;
}

*[title]:hover * {
    pointer-events: auto;
}

/* Streamlit 사이드바 컨테이너 */
.css-1d391kg {
    position: relative;
}

/* 사이드바 전체에 오버레이 */
.css-1d391kg::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    pointer-events: none;
    background: transparent;
}
</style>

<script>
// 모든 title 속성을 제거하는 JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // 모든 요소의 title 속성 제거
    function removeAllTitles() {
        const allElements = document.querySelectorAll('*');
        allElements.forEach(element => {
            if (element.hasAttribute('title')) {
                element.removeAttribute('title');
            }
        });
    }
    
    // 초기 실행
    removeAllTitles();
    
    // DOM 변경 감지하여 지속적으로 제거
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.hasAttribute('title')) {
                            node.removeAttribute('title');
                        }
                        // 자식 요소들도 확인
                        const childElements = node.querySelectorAll('*');
                        childElements.forEach(child => {
                            if (child.hasAttribute('title')) {
                                child.removeAttribute('title');
                            }
                        });
                    }
                });
            }
        });
    });
    
    // 전체 문서 감시
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // 주기적으로 title 속성 제거 (추가 보장)
    setInterval(removeAllTitles, 1000);
});
</script>
""", unsafe_allow_html=True)

def main():
    """메인 함수"""
    # 환경변수 검증
    if not validate_environment():
        st.error("❌ 환경변수가 설정되지 않았습니다. 위의 안내를 따라 .env 파일을 생성하세요.")
        st.stop()
    
    # 세션 상태 초기화 (페이지 새로고침 시 복구)
    _initialize_session_state()
    
    # 애플리케이션 실행
    app = AIAssessmentGame()
    app.run()

def _initialize_session_state():
    """세션 상태 초기화 및 복구"""
    # 기본 세션 상태 설정
    if 'session_initialized' not in st.session_state:
        st.session_state.session_initialized = True
        
        # 인증 관련 세션 상태 초기화
        auth_keys = ['user_id', 'user_profile', 'user', 'access_token', 
                    'login_completed', 'user_email', 'supabase_user']
        
        for key in auth_keys:
            if key not in st.session_state:
                st.session_state[key] = None

if __name__ == "__main__":
    main()
