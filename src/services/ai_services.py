# ai_services.py
"""
AI 관련 서비스 클래스들
"""

import json
import time
import random
import base64
import io
import hashlib
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

from src.core.config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS, OPENAI_TEMPERATURE,
    GRADING_CRITERIA, LEVEL_COLORS, LEVEL_ICONS
)

# OpenAI 클라이언트 초기화
try:
    from openai import OpenAI
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        client = None
        st.warning("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
except Exception as e:
    client = None
    st.error(f"OpenAI 클라이언트 초기화 오류: {str(e)}")


class ProfileGenerator:
    """AI 기반 프로필 이미지 생성기"""
    
    @staticmethod
    def generate_profile_image(username: str, level: int, prompt: str = None) -> str:
        """사용자 프로필 이미지 생성"""
        try:
            img = Image.new('RGB', (200, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # 레벨에 따른 배경색
            bg_color = LEVEL_COLORS.get(level, '#FFFFFF')
            
            # 배경 그리기
            draw.rectangle([0, 0, 200, 200], fill=bg_color)
            
            # 사용자 이니셜
            initials = ''.join([word[0].upper() for word in username.split()[:2]])
            
            # 텍스트 그리기
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                font = ImageFont.load_default()
            
            draw.text((100, 100), initials, fill='white', anchor='mm', font=font)
            
            # 레벨 표시
            level_icon = LEVEL_ICONS.get(level, '')
            draw.text((170, 170), level_icon, fill='white', anchor='mm')
            
            # Base64로 인코딩
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            st.error(f"프로필 이미지 생성 오류: {str(e)}")
            return ""


class AutoGrader:
    """AI 기반 자동 채점 시스템"""
    
    def __init__(self):
        self.grading_criteria = GRADING_CRITERIA
    
    def grade_answer(self, question: Dict, answer: str, level: str) -> Dict:
        """답변 자동 채점"""
        start_time = time.time()
        
        # OpenAI 클라이언트가 없는 경우 시뮬레이션 모드
        if client is None:
            return self._simulate_grading(question, answer, level, start_time)
        
        # 채점 프롬프트 구성
        system_prompt = """당신은 AI 활용능력평가 전문 채점관입니다.
        주어진 답변을 평가하고 점수와 피드백을 제공해주세요.
        평가는 공정하고 객관적이어야 하며, 구체적인 개선점을 제시해야 합니다."""
        
        criteria = self.grading_criteria.get(level, self.grading_criteria["basic"])
        
        user_prompt = f"""
문제: {question.get('question_text', question.get('question', '문제 없음'))}

학생 답변: {answer}

평가 기준:
{json.dumps(criteria, indent=2)}

다음 형식으로 채점해주세요:
{{
    "total_score": 0-100 사이의 점수,
    "criteria_scores": {{각 기준별 점수}},
    "passed": true/false (60점 이상이면 true),
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "feedback": "종합 피드백"
}}
"""
        
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS
            )
            
            # 응답 파싱
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            time_taken = int(time.time() - start_time)
            
            # JSON 파싱
            try:
                result = json.loads(content)
            except:
                # 파싱 실패 시 기본 구조
                result = {
                    "total_score": 0,
                    "passed": False,
                    "feedback": content
                }
            
            result["time_taken"] = time_taken
            result["tokens_used"] = tokens_used
            
            return result
            
        except Exception as e:
            return {
                "total_score": 0,
                "passed": False,
                "feedback": f"채점 중 오류 발생: {str(e)}",
                "time_taken": int(time.time() - start_time),
                "tokens_used": 0
            }
    
    def _simulate_grading(self, question: Dict, answer: str, level: str, start_time: float) -> Dict:
        """OpenAI API 없이 시뮬레이션 채점"""
        time_taken = int(time.time() - start_time)
        
        # 답변 길이와 내용에 따른 간단한 점수 계산
        answer_length = len(answer.strip())
        base_score = min(100, max(0, answer_length * 2))  # 길이에 따른 기본 점수
        
        # 난이도별 조정
        from src.core.config import DIFFICULTY_MULTIPLIER
        adjusted_score = base_score * DIFFICULTY_MULTIPLIER.get(level, 1.0)
        
        # 랜덤 요소 추가 (실제 AI 채점 시뮬레이션)
        final_score = min(100, max(0, adjusted_score + random.randint(-20, 20)))
        
        passed = final_score >= 60
        
        feedback = f"""
시뮬레이션 모드에서 채점되었습니다.

점수: {final_score:.1f}점
결과: {'통과' if passed else '실패'}

답변 길이: {answer_length}자
소요 시간: {time_taken}초

실제 AI 채점을 위해서는 OpenAI API 키를 설정해주세요.
"""
        
        return {
            "total_score": final_score,
            "criteria_scores": {"accuracy": final_score * 0.6, "completeness": final_score * 0.3, "clarity": final_score * 0.1},
            "passed": passed,
            "strengths": ["답변을 제출했습니다", "문제에 대한 시도를 했습니다"] if answer_length > 10 else [],
            "improvements": ["더 구체적인 답변을 작성해보세요", "실제 사례를 포함해보세요"] if not passed else [],
            "feedback": feedback,
            "time_taken": time_taken,
            "tokens_used": 0
        }


class QuestionGenerator:
    """문제 생성기"""
    
    @staticmethod
    def generate_question(difficulty: str, level: int) -> Dict:
        """난이도와 레벨에 따른 문제 생성"""
        questions = {
            "basic": [
                "ChatGPT를 사용하여 간단한 요약문을 작성하는 방법을 설명하세요.",
                "AI 도구를 활용하여 이메일 초안을 작성하는 과정을 설명하세요.",
                "AI를 사용하여 번역 작업을 수행하는 방법을 설명하세요."
            ],
            "intermediate": [
                "AI를 활용하여 비즈니스 프레젠테이션 자료를 만드는 전략을 제시하세요.",
                "AI 도구를 사용하여 데이터 분석 결과를 시각화하는 방법을 설명하세요.",
                "AI를 활용하여 고객 서비스 자동화 시스템을 설계하는 방안을 제시하세요."
            ],
            "advanced": [
                "AI를 활용하여 새로운 비즈니스 모델을 창출하는 혁신적인 아이디어를 제시하세요.",
                "AI 기술을 활용하여 기존 업무 프로세스를 혁신하는 방안을 설계하세요.",
                "AI를 활용하여 사회적 문제를 해결하는 창의적인 솔루션을 제안하세요."
            ]
        }
        
        question_list = questions.get(difficulty, questions["basic"])
        selected_question = random.choice(question_list)
        
        return {
            "id": f"Q_{int(time.time())}_{random.randint(1000, 9999)}",
            "difficulty": difficulty,
            "question": selected_question,
            "level": level,
            "type": "practice"
        }
