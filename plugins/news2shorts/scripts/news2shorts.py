#!/usr/bin/env python3
"""Minimal local tooling for the news2shorts Codex plugin."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from difflib import SequenceMatcher
import email.utils
import functools
import getpass
import hashlib
import html
import io
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
from urllib import error, parse, request
from zoneinfo import ZoneInfo


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "news2shorts"
TEMPLATE_ROOT = SKILL_ROOT / "templates"
KST = ZoneInfo("Asia/Seoul")
NAVER_BASE_URL = "https://naverapihub.apigw.ntruss.com"
DISCOVERY_CANDIDATE_COUNT = 10
TYPECAST_TTS_URL = "https://api.typecast.ai/v1/text-to-speech"
TYPECAST_MODEL = "ssfm-v30"
TYPECAST_VOICE_ID = "tc_68d4b115f0486108a7eefb37"
TYPECAST_VOICE_NAME = "Kangil"
TYPECAST_VOICE_SELECTION_STRATEGY = "official-popular-top5+content-fit+stable-80-20"
TYPECAST_VOICE_POPULARITY_BASIS = "Typecast 공식 인기 캐릭터 Top 5 (2026-08-12 갱신)"
TYPECAST_VOICE_POPULARITY_SOURCE = "https://typecast.ai/kr/learn/typecast-new-editor-characters/"
TYPECAST_VOICE_CANDIDATES = {
    "daeun": {
        "voice_id": "tc_692799c46508f6b9468c54c7",
        "voice_name": "Daeun",
        "profile": "short-form-conversational",
        "use_cases": ["Instagram Reels/TikTok/Shorts", "Bright short-form"],
    },
    "seohyeon": {
        "voice_id": "tc_69f2e455ea79fd197aa0476f",
        "voice_name": "Seohyeon",
        "profile": "news-clarity",
        "use_cases": ["News/Card news/Current issues", "Accurate delivery"],
    },
    "piljae": {
        "voice_id": "tc_68257f68bc6e3c161ab5078d",
        "voice_name": "Piljae",
        "profile": "documentary-information",
        "use_cases": ["Information/Knowledge YouTube", "Trust and wit"],
    },
    "moonjung": {
        "voice_id": "tc_68f9c6a72f0f04a417bb136f",
        "voice_name": "Moonjung",
        "profile": "calm-explainer",
        "use_cases": ["Lecture/Guide/Information", "Calm explainer"],
    },
    "kangil": {
        "voice_id": "tc_68d4b115f0486108a7eefb37",
        "voice_name": "Kangil",
        "profile": "long-form-immersive",
        "use_cases": ["Podcast/Long documentary/Information", "Immersive delivery"],
    },
}
TYPECAST_VOICE_ALIASES = {
    "다은": "daeun",
    "서현": "seohyeon",
    "필재": "piljae",
    "문정": "moonjung",
    "강일": "kangil",
}
TYPECAST_DEFAULT_VOICE_BUCKETS = ("kangil",) * 8 + ("daeun",) * 2
TYPECAST_DEFAULT_VOICE_DISTRIBUTION = "Kangil 80% / Daeun 20%"
TYPECAST_DEFAULT_VOICE_DISTRIBUTION_BASIS = "project-stable-sha256"
TYPECAST_DELIVERY_PROFILES = {
    "auto": {
        "emotion_type": "smart",
        "audio_pitch": 0,
        "tempo_multiplier": 1.0,
    },
    "contrast": {
        "emotion_type": "preset",
        "emotion_preset": "toneup",
        "emotion_intensity": 1.05,
        "audio_pitch": 1,
        "tempo_multiplier": 0.98,
    },
    "verdict": {
        "emotion_type": "preset",
        "emotion_preset": "tonedown",
        "emotion_intensity": 1.1,
        "audio_pitch": -1,
        "tempo_multiplier": 0.94,
    },
}
TYPECAST_PAYOFF_DELIVERIES = {"contrast", "verdict"}
TYPECAST_GUIDE_KEYWORDS = {
    "가이드",
    "대처",
    "방법",
    "사용법",
    "설정법",
    "신청",
    "예방",
    "절차",
    "주의사항",
    "체크리스트",
}
TYPECAST_ESTIMATED_CHARS_PER_SECOND = 6.2
TYPECAST_SCENE_TAIL_SECONDS = 0.35
TYPECAST_LEADING_SILENCE_KEEP_SECONDS = 0.12
TYPECAST_TRAILING_SILENCE_KEEP_SECONDS = 0.18
TYPECAST_SILENCE_THRESHOLD_DB = -42
CONTINUOUS_FLOW_MODE = "continuous-flow"
VISUAL_FIRST_MODE = "visual-first"
DELIVERY_MODES = {CONTINUOUS_FLOW_MODE, VISUAL_FIRST_MODE}
NARRATION_STYLE_STANDARD = "standard"
NARRATION_STYLE_CC_HELPER_CONVERSATIONAL = "cc-helper-conversational"
NARRATION_STYLES = {
    NARRATION_STYLE_STANDARD,
    NARRATION_STYLE_CC_HELPER_CONVERSATIONAL,
}
SOURCE_VIDEO_AUDIO_MODE = "source-video"
NARRATION_AUDIO_MODE = "narration"
ALLOWED_SCENE_AUDIO_MODES = {NARRATION_AUDIO_MODE, SOURCE_VIDEO_AUDIO_MODE}
SOURCE_AUDIO_REVIEW_FILENAME = "source-audio-review.json"
SOURCE_AUDIO_REVIEW_VERSION = 1
SOURCE_TRANSCRIPT_MATCH_THRESHOLD = 0.72
SOURCE_TRANSCRIPT_COVERAGE_THRESHOLD = 0.80
SOURCE_AUDIO_EDGE_MARGIN_SECONDS = 0.15
CONTINUOUS_FLOW_MIN_SCENE_SECONDS = 1.0
CONTINUOUS_FLOW_PAYOFF_MIN_SECONDS = 3.5
CONTINUOUS_FLOW_DEFAULT_DURATION_SECONDS = 20
CONTINUOUS_FLOW_MIN_DURATION_SECONDS = 12
CONTINUOUS_FLOW_MAX_DURATION_SECONDS = 35
VISUAL_FIRST_DEFAULT_DURATION_SECONDS = 12
VISUAL_FIRST_MIN_DURATION_SECONDS = 8
VISUAL_FIRST_MAX_DURATION_SECONDS = 14
VISUAL_FIRST_MIN_SCENES = 4
VISUAL_FIRST_MAX_SCENES = 6
VISUAL_FIRST_EARLY_WINDOW_SECONDS = 3.0
VISUAL_FIRST_MIN_EARLY_STATES = 3
CONTINUOUS_FLOW_ANSWER_DEADLINE_SECONDS = 8.0
VISUAL_FIRST_ANSWER_DEADLINE_SECONDS = 1.5
TRUTH_GUARD_DEADLINE_SECONDS = 4.0
TARGET_DURATION_WARNING_RATIO = 1.15
TARGET_DURATION_ERROR_RATIO = 1.25
ORDINARY_SCENE_WARNING_SECONDS = 4.5
ORDINARY_SCENE_ERROR_SECONDS = 6.0
PAYOFF_SCENE_WARNING_SECONDS = 6.0
PAYOFF_SCENE_ERROR_SECONDS = 7.0
EARLY_RETENTION_DEADLINE_SECONDS = 10.0
TYPECAST_KEYCHAIN_SERVICE = "news2shorts.typecast.api-key"
TYPECAST_KEYCHAIN_LABEL = "news2shorts Typecast API key"
SCREEN_COPY_MODE_NOUN_PHRASES = "noun-phrases"
SCREEN_COPY_LIMITS = {
    "display_headline": 22,
    "eyebrow": 14,
    "headline": 22,
    "headline_highlight": 10,
    "caption": 24,
    "caption_focus": 12,
    "evidence_label": 22,
    "evidence_value": 18,
    "payoff_title": 22,
    "payoff_detail": 34,
    "payoff_punch": 20,
    "payoff_callback": 28,
    "discussion_prompt": 14,
}
SCREEN_COPY_EXAMPLES = {
    "display_headline": "커피믹스 이상 제품",
    "eyebrow": "현재 확인 결과",
    "headline": "커피믹스 이상 제품",
    "headline_highlight": "이상 제품",
    "caption": "동일 상자 3개 발견",
    "caption_focus": "3개",
    "evidence_label": "동일 상자 발견",
    "evidence_value": "3개",
    "payoff_title": "관리 소홀 인정",
    "payoff_detail": "수정·점검·보상 약속",
    "payoff_punch": "정보 오류, 시민 부담?",
    "payoff_callback": "굳은 제품 → 정상 아님",
    "discussion_prompt": "정상 제품?",
}
GENERIC_UNKNOWN_PAYOFF_TERMS = ("미확인", "확인 중", "아직 없음", "지켜봐야")
UNSTABLE_RELATIVE_TIME_PATTERN = re.compile(
    r"(?:오늘|내일|다음\s*달|이번\s*달|이달)부터"
)
IMMEDIATE_TOW_PATTERN = re.compile(
    r"(?:(?:바로|즉시)\s*견인|신고(?:하면|하자마자).{0,8}견인)"
)
DEFAULT_VISUAL_SOURCE_PRIORITY = (
    "current-news-article",
    "public-community-post",
    "official-primary-media",
    "licensed-media-library",
    "generated-fallback",
)
DEFAULT_VISUAL_LOCALE = "ko-KR"
DEFAULT_FOREIGN_VISUAL_FALLBACK = "blocked"
DEFAULT_KOREAN_GENERATED_STYLE = "korean-editorial-realism"
INTERNATIONAL_VISUAL_LOCALE = "mixed-source"
INTERNATIONAL_FOREIGN_VISUAL_FALLBACK = "source-event-only"
INTERNATIONAL_GENERATED_STYLE = "source-event-explainer"
SCREEN_SENTENCE_ENDING_PATTERN = re.compile(
    r"(?:입니다|합니다|됩니다|했습니다|있습니다|없습니다|아닙니다|"
    r"이에요|예요|해요|돼요|맞나요|인가요|일까요|할까요|나요|까요|"
    r"한다|된다|있다|없다|아니다|맞다|같다|[았었였됐]다)$"
)
DEFAULT_QUERIES = [
    "정치",
    "경제",
    "사회",
    "IT 과학",
    "정부 정책 시민 부담",
    "국회 논란 특혜",
    "세금 물가 주거 연금",
    "안전 사고 관리 부실",
    "소비자 피해 개인정보",
]
DEFAULT_PROJECT_HISTORY_ROOT = "projects"
USED_TOPIC_TOKEN_SIMILARITY_THRESHOLD = 0.25
USED_TOPIC_TEXT_SIMILARITY_THRESHOLD = 0.58
USED_TOPIC_MIN_SHARED_TERMS = 2
POLITICAL_TERMS = {
    "대통령",
    "대통령실",
    "정부",
    "국회",
    "국정",
    "정당",
    "여당",
    "야당",
    "의원",
    "장관",
    "선거",
    "공천",
    "지자체",
    "도지사",
}
CITIZEN_SENSITIVITY_TERMS = {
    "생활비": {"세금", "요금", "물가", "가격", "보험료", "연금", "지원금", "수수료", "과태료"},
    "주거·금융": {"집값", "전세", "월세", "대출", "금리", "보증금", "임대", "분양"},
    "안전·건강": {"사고", "화재", "붕괴", "감염", "리콜", "범죄", "치안", "의료", "식품", "산재"},
    "교육·노동": {"학교", "교육", "교사", "학생", "임금", "실업", "채용", "노동", "퇴직"},
    "권리·정보": {"개인정보", "해킹", "유출", "환불", "보상", "차별", "갑질", "소비자"},
    "공공서비스": {"중단", "지연", "취소", "폐쇄", "장애", "교통", "전기", "통신", "행정"},
}
CITIZEN_AFFECTED_GROUP_TERMS = {
    "가구",
    "가족",
    "소비자",
    "시민",
    "주민",
    "이용자",
    "환자",
    "보호자",
    "학생",
    "학부모",
    "운전자",
    "세입자",
    "임차인",
    "자영업자",
    "소상공인",
    "노동자",
    "근로자",
    "직장인",
    "가입자",
    "수급자",
    "피해자",
    "유족",
    "아내",
    "남편",
    "아동",
    "청소년",
    "고령자",
    "장애인",
}
CITIZEN_COST_TERMS = {
    "세금",
    "요금",
    "물가",
    "가격",
    "비용",
    "부담",
    "식비",
    "장바구니",
    "외식",
    "월세",
    "전세",
    "보증금",
    "대출",
    "금리",
    "보험료",
    "병원비",
    "등록금",
    "수수료",
    "과태료",
    "연금",
    "임금",
    "환불",
    "손해",
}
CITIZEN_HARM_TERMS = {
    "사망",
    "살해",
    "부상",
    "피해",
    "위험",
    "사고",
    "화재",
    "붕괴",
    "감염",
    "범죄",
    "유해",
    "실종",
}
CITIZEN_PROTECTION_TERMS = {
    "접근금지",
    "보호명령",
    "보호",
    "경보",
    "신고",
    "수색",
    "관리",
    "감독",
    "점검",
    "리콜",
    "보고",
    "대피",
    "안전",
}
CITIZEN_RIGHTS_TERMS = {
    "거부",
    "제한",
    "차별",
    "해고",
    "박탈",
    "침해",
    "유출",
    "해킹",
    "중단",
    "지연",
    "폐쇄",
    "장애",
    "취소",
    "미지급",
    "강요",
    "환불",
    "보상",
}
CITIZEN_PUBLIC_SERVICE_TERMS = {
    "경찰",
    "소방",
    "병원",
    "학교",
    "지자체",
    "행정",
    "교통",
    "전기",
    "통신",
    "공공",
    "정부",
}
INTERNAL_STAKEHOLDER_TERMS = {
    "성과급",
    "보너스",
    "임원",
    "주주",
    "배당",
    "인센티브",
    "사내",
    "직원",
    "연봉",
    "스톡옵션",
}
EXTERNAL_PUBLIC_CONSEQUENCE_TERMS = {
    "가구",
    "가족",
    "소비자",
    "시민",
    "주민",
    "이용자",
    "환자",
    "학부모",
    "학생",
    "운전자",
    "세입자",
    "임차인",
    "자영업자",
    "소상공인",
    "물가",
    "장바구니",
    "세금",
    "요금",
    "안전",
    "개인정보",
    "교통",
    "의료",
    "전기",
    "통신",
}
CITIZEN_MEASURABLE_CONSEQUENCE_PATTERN = re.compile(
    r"\d[\d,.]*(?:만|억|천)?\s*(?:원|%|퍼센트|명|가구|시간|일|개월)|"
    r"(?:인상|상승|급등|하락|삭감|미지급|초과|증가|감소)"
)
ACCOUNTABILITY_TERMS = {
    "특혜",
    "비리",
    "거짓",
    "허위",
    "은폐",
    "누락",
    "부실",
    "방치",
    "책임",
    "감찰",
    "수사",
    "기소",
    "이해충돌",
}
COMMUNITY_SIGNAL_MATCH_THRESHOLD = 0.2
STOP_WORDS = {
    "기자",
    "뉴스",
    "오늘",
    "관련",
    "대한",
    "위해",
    "통해",
    "밝혀",
    "발표",
    "논란",
    "정부",
    "한국",
    "서울",
    "단독",
    "속보",
    "종합",
}
FONT_CANDIDATES = [
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/Library/Fonts/NotoSansKR-Regular.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
ALLOWED_ASSET_KINDS = {"generated", "licensed", "official", "owned", "unreviewed"}
ALLOWED_SEARCH_OUTCOMES = {"collected", "generated", "no_usable_asset"}
ALLOWED_IMAGE_MOTIONS = {"none", "slow-zoom", "zoom-in", "zoom-out"}
ALLOWED_IMAGE_FITS = {"auto", "contain", "cover"}
ALLOWED_VISUAL_RELEVANCE_LEVELS = {"direct", "contextual"}
ALLOWED_MEDIA_TYPES = {
    "photo",
    "video",
    "document",
    "chart",
    "illustration",
    "pictogram",
    "screenshot",
    "map",
    "logo",
}
DEFAULT_MIN_REAL_MEDIA_RATIO = 0.6
VISUAL_MODES = {"standard", "hot-real-news", "whiteboard"}
MAX_INTERNET_IMAGE_BYTES = 25 * 1024 * 1024
MAX_INTERNET_IMAGE_PIXELS = 50_000_000
ALLOWED_VISUAL_ROLES = {"evidence", "context", "explanation", "reaction-meme"}
ALLOWED_MEME_ORIGINS = {"licensed", "owned", "original"}
ALLOWED_COMPANY_VISUAL_TYPES = {
    "logo",
    "official-image",
    "licensed-photo",
    "branded-product",
    "facility-signage",
}
ALLOWED_PERSON_ROLES = {
    "public_official",
    "public_figure",
    "private_person",
    "victim",
    "accused",
    "other",
}
ALLOWED_PERSON_VISUAL_STATUSES = {
    "used",
    "privacy_excluded",
    "rights_blocked",
}
ALLOWED_ACCOUNTABILITY_MODES = {"verified", "not_applicable"}
ALLOWED_VISUAL_ATTENTION_DEVICES = {
    "reaction-meme",
    "contrast-composite",
    "consequence-photo",
    "evidence-closeup",
    "motion-proof",
}
VISUAL_ATTENTION_BEATS = {"hook", "rehook", "turn", "impact"}
GENERIC_TENSION_QUESTIONS = {
    "이게맞나",
    "이게맞나요",
    "왜이럴까",
    "어떻게될까",
    "무슨일일까",
    "진짜일까",
}
CITIZEN_STAKE_TERMS = {
    "시민",
    "국민",
    "소비자",
    "주민",
    "납세자",
    "이용자",
    "직장인",
    "자영업자",
    "세입자",
    "환자",
    "보호자",
    "학생",
    "학부모",
    "운전자",
    "노동자",
    "가구",
    "식탁",
    "지갑",
    "안전",
    "생활",
    "주거",
    "요금",
    "세금",
}
SUMMARY_LEAD_PREFIXES = (
    "오늘뉴스",
    "이번뉴스",
    "뉴스요약",
    "뉴스를요약",
    "소식입니다",
    "정리하면",
    "정리해보면",
)
QUICK_REVEAL_DIRECT_VISUAL_BEATS = {"hook", "evidence", "turn", "impact", "payoff"}
REACTION_MEME_BEATS = {"context", "rehook"}
DEFAULT_CTA_TAIL_DURATION = 2.0
MIN_CTA_TAIL_DURATION = 0.8
MAX_CTA_TAIL_DURATION = 6.0
CTA_NARRATION_TAIL_SECONDS = 0.25
DEFAULT_CTA_NARRATION = "다음 소식도 바로 전해드릴게요."
DEFAULT_COMMENT_CTA_HEADLINE = "여러분의 판단"
DEFAULT_COMMENT_CTA_PROMPT = "댓글로 한마디"
DEFAULT_COMMENT_CTA_NARRATION = "여러분의 생각을 댓글로 남겨주세요."
DEFAULT_COMMENT_CTA_FALLBACK_NARRATION = (
    "여러분은 어떻게 보세요? 여러분의 생각을 댓글로 남겨주세요."
)
CTA_TAIL_VARIANTS = ("subscribe", "comment")
CTA_TAIL_SELECTION_STRATEGY = "sensitive-safe+discussion-fit+stable-50-50"
CTA_TAIL_AFTER_MID_SELECTION_STRATEGY = "explicit-final-cta-after-mid-v1"
CTA_TAIL_DEFAULT_DISTRIBUTION = "Subscribe 50% / Comment 50%"
CTA_TAIL_DEFAULT_DISTRIBUTION_BASIS = "project-stable-sha256"
MID_CTA_MODES = {"auto", "enabled", "disabled"}
MID_CTA_PLACEMENT = "after-auto-rehook"
MID_CTA_STYLE = "pity-native-arrow"
MID_CTA_UI_TARGET_PROFILE = "youtube-shorts-mobile"
MID_CTA_MIN_BODY_SECONDS = 20.0
MID_CTA_MIN_DURATION = 1.5
MID_CTA_MAX_DURATION = 2.0
MID_CTA_AUDIO_TAIL_SECONDS = 0.12
MID_CTA_TARGET_MIN_RATIO = 0.40
MID_CTA_TARGET_MAX_RATIO = 0.60
MID_CTA_TARGET_RATIO = 0.50
MID_CTA_ALLOWED_BEATS = {"rehook", "turn"}
MID_CTA_DEFAULT_TARGET_X = 0.34
MID_CTA_DEFAULT_TARGET_Y = 0.86
MID_CTA_UNVERIFIED_METRIC_PATTERN = re.compile(
    r"(?:많은\s*분|조회수|구독률|시청자\s*수)"
)
BRAND_CLOSE_DURATION = 0.8
BRAND_INTRO_ASSET_ID = "news-hanmyeon-channel"
BRAND_INTRO_ASSET_PATH = PLUGIN_ROOT / "assets" / "brand-intro-news-hanmyeon.mp4"
BRAND_INTRO_ASSET_PATHS = {
    BRAND_INTRO_ASSET_ID: BRAND_INTRO_ASSET_PATH,
    "oldman-korea-map": PLUGIN_ROOT / "assets" / "brand-intro-oldman-korea-map.mp4",
}
ALLOWED_BRAND_INTRO_ASSET_IDS = frozenset(BRAND_INTRO_ASSET_PATHS)
BRAND_INTRO_SOURCE_DURATION_SECONDS = 3.15
BRAND_MODE_CORNER_LOGO = "corner-logo"
BRAND_MODE_LEGACY_FULL = "legacy-full"
ALLOWED_BRAND_MODES = {BRAND_MODE_CORNER_LOGO, BRAND_MODE_LEGACY_FULL}
BRAND_LOGO_PATH = PLUGIN_ROOT / "assets" / "news-hanmyeon-channel-logo.png"
BRAND_LOGO_SIZE = 64
BRAND_LOGO_MARGIN = 24
DEFAULT_BRAND_INTRO_TRANSITION = "fadeblack"
DEFAULT_BRAND_INTRO_TRANSITION_DURATION = 0.25
MIN_BRAND_INTRO_TRANSITION_DURATION = 0.10
MAX_BRAND_INTRO_TRANSITION_DURATION = 0.75
ALLOWED_BRAND_INTRO_TRANSITIONS = {DEFAULT_BRAND_INTRO_TRANSITION}
VISUAL_FIRST_AUDIO_PROFILE = "news-pulse"
VISUAL_FIRST_AUDIO_PATH = "audio/background-music.wav"
MIN_MOTION_DURATION = 0.35
MAX_MOTION_DURATION = 2.5
FACT_STACK_EVIDENCE_KINDS = {
    "photo",
    "video",
    "document",
    "map",
    "comparison",
    "number",
    "timeline",
    "diagram",
}
FACT_STACK_PROOF_BEATS = {"evidence", "turn", "impact", "rehook"}
EARLY_RESOLUTION_PATTERN = re.compile(r"^\s*(?:정답|결론|원인)(?:은|는|이|가)?\b")
FACT_INDEX_PATTERN = re.compile(r"^(?P<current>[1-9]\d*)/(?P<total>[1-9]\d*)$")
DEFAULT_GENERATED_IMAGE_SIZE = (720, 1280)
OUTPUT_VIDEO_SIZE = (720, 1280)
YOUTUBE_TITLE_LIMIT = 100
YOUTUBE_DESCRIPTION_LIMIT = 5000
DEFAULT_THUMBNAIL_PATH = "thumbnail.jpg"
THUMBNAIL_STYLES = {"auto", "presenter-led", "evidence-led"}
THUMBNAIL_PRESENTER_USAGE_ROLE = "thumbnail-presenter"
GENERIC_THUMBNAIL_BADGES = {
    "이게맞아",
    "이게맞아?",
    "충격",
    "대박",
    "실화",
    "실화?",
    "속보",
}
EDITOR_PACKAGE_VERSION = 1
EDITOR_PACKAGE_ROOT = "edit-package"
TITLE_HASHTAG_COUNT = 2
PUBLISH_MARKDOWN_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\((?:https?://|www\.)[^)]+\)",
    re.IGNORECASE,
)
PUBLISH_LINK_PATTERN = re.compile(
    r"(?:https?://|www\.)[^\s<>()\[\]]+|"
    r"(?:[A-Za-z0-9-]+\.)+(?:com|net|org|io|ai|kr)(?:/[^\s<>()\[\]]*)?",
    re.IGNORECASE,
)
PUBLISH_HASHTAG_PATTERN = re.compile(r"#[0-9A-Za-z가-힣_]+")
PUBLIC_DESCRIPTION_PRODUCTION_PATTERNS = (
    re.compile(
        r"(?:화면(?:의|에)|영상(?:에|에서)|사용(?:한|된))[^.!?]{0,80}"
        r"(?:사진|이미지|시각\s*자료)[^.!?]{0,80}"
        r"(?:Pexels|Unsplash|Pixabay|Wikimedia|Openverse|라이선스|자료\s*사진|"
        r"해당\s*[^.!?]{0,24}(?:아님|아닙니다))",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:사진|이미지|영상)(?:은|는|이|가)?[^.!?]{0,60}"
        r"(?:Pexels|Unsplash|Pixabay|Wikimedia|Openverse|라이선스|자료\s*사진|"
        r"해당\s*[^.!?]{0,24}(?:아님|아닙니다))",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:음성|내레이션)(?:은|는|이|가)?[^.!?]{0,40}"
        r"(?:Typecast|타입캐스트|TTS|합성\s*음성)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:Typecast|타입캐스트|TTS)[^.!?]{0,40}(?:음성|내레이션|합성)",
        re.IGNORECASE,
    ),
)
MAX_PAYOFF_HOOK_SIMILARITY = 0.55
MIN_PAYOFF_LENGTH = 14
WEAK_PAYOFF_TEXTS = {
    "결론은",
    "결론은?",
    "앞으로가중요합니다",
    "어떻게될까요",
    "지켜봐야합니다",
    "지금은권한을만드는중",
    "변화가시작됩니다",
}
RETENTION_TEMPLATES = {"quick-reveal", "fact-stack", "story-explainer"}
NEW_PROJECT_TEMPLATES = {"quick-reveal"}
SUPPORTED_TEMPLATES = RETENTION_TEMPLATES | {"broadcast-card", "classic-card"}
EDITORIAL_IDENTIFIER_PATTERN = re.compile(
    r"(?P<label>의안|법안|안건|사건|문서|접수|공고|발의|관리)"
    r"(?:\s*번호)?\s*(?:제\s*)?(?P<identifier>\d{5,})(?:\s*호)?"
    r"(?P<particle>으로|에서|은|는|이|가|을|를|과|와|로|의|에)?"
)
STANDALONE_IDENTIFIER_PATTERN = re.compile(
    r"제\s*\d{5,}\s*호(?P<particle>으로|에서|은|는|이|가|을|를|과|와|로|의|에)?"
)
EDITORIAL_IDENTIFIER_NOUNS = {
    "의안": "의안",
    "법안": "법안",
    "안건": "안건",
    "사건": "사건",
    "문서": "문서",
    "접수": "접수 건",
    "공고": "공고",
    "발의": "의안",
    "관리": "관리 항목",
}
EDITORIAL_SCENE_TEXT_FIELDS = {
    "eyebrow",
    "headline",
    "headline_highlight",
    "caption",
    "caption_focus",
    "evidence_label",
    "evidence_value",
    "ticker",
    "payoff_title",
    "payoff_detail",
    "payoff_punch",
    "payoff_callback",
    "discussion_prompt",
    "narration",
    "credit",
    "source_label",
}
HOOK_TYPES = {
    "counterintuitive",
    "result-first",
    "comparison-reversal",
    "change-impact",
    "numeric-gap",
    "issue-tension",
}
SCENE_BEATS = {"hook", "context", "evidence", "turn", "impact", "rehook", "payoff", "loop"}


class News2ShortsError(RuntimeError):
    pass


def now_kst() -> dt.datetime:
    return dt.datetime.now(KST)


def iso_now() -> str:
    return now_kst().isoformat(timespec="seconds")


def fail(message: str, exit_code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def load_json(path: Path) -> object:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise News2ShortsError(f"필수 파일이 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise News2ShortsError(f"JSON 형식이 잘못되었습니다: {path}: {exc}") from exc


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def has_final_consonant(value: str) -> bool:
    if not value:
        return False
    codepoint = ord(value[-1])
    return 0xAC00 <= codepoint <= 0xD7A3 and (codepoint - 0xAC00) % 28 != 0


def normalized_particle(noun: str, particle: str) -> str:
    if not particle:
        return ""
    final = has_final_consonant(noun)
    if particle in {"은", "는"}:
        return "은" if final else "는"
    if particle in {"이", "가"}:
        return "이" if final else "가"
    if particle in {"을", "를"}:
        return "을" if final else "를"
    if particle in {"과", "와"}:
        return "과" if final else "와"
    if particle in {"으로", "로"}:
        return "으로" if final else "로"
    return particle


def suppress_editorial_identifiers(value: str) -> str:
    """Replace spoken/display identifiers while preserving meaningful facts and evidence files."""

    text = str(value or "")

    def replace_labeled(match: re.Match[str]) -> str:
        noun = EDITORIAL_IDENTIFIER_NOUNS[match.group("label")]
        return f"해당 {noun}{normalized_particle(noun, match.group('particle') or '')}"

    def replace_standalone(match: re.Match[str]) -> str:
        noun = "안건"
        return f"해당 {noun}{normalized_particle(noun, match.group('particle') or '')}"

    text = EDITORIAL_IDENTIFIER_PATTERN.sub(replace_labeled, text)
    text = STANDALONE_IDENTIFIER_PATTERN.sub(replace_standalone, text)
    return text


def suppress_public_identifiers(project_dir: Path, project: dict, storyboard: dict) -> list[str]:
    """Remove administrative IDs from public-facing text, leaving source evidence untouched."""

    changed_fields: list[str] = []

    def replace_field(container: dict, field: str, location: str) -> None:
        value = container.get(field)
        if not isinstance(value, str):
            return
        sanitized = suppress_editorial_identifiers(value)
        if sanitized != value:
            container[field] = sanitized
            changed_fields.append(f"{location}.{field}")

    for field in ("title", "topic"):
        replace_field(project, field, "project")
    profile = project.get("shorts_profile")
    if isinstance(profile, dict):
        for field in (
            "hook",
            "hook_stake",
            "issue_focus",
            "viewer_stake",
            "tension_question",
            "visual_attention_reason",
            "open_loop",
            "midpoint_rehook",
            "payoff",
            "loop_close",
        ):
            replace_field(profile, field, "project.shorts_profile")
    style = project.get("visual_style")
    if isinstance(style, dict):
        for field in ("display_headline", "headline_highlight"):
            replace_field(style, field, "project.visual_style")

    replace_field(storyboard, "title", "storyboard")
    scenes = storyboard.get("scenes")
    if isinstance(scenes, list):
        for index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                continue
            scene_id = str(scene.get("id") or f"scene-{index:02d}")
            for field in EDITORIAL_SCENE_TEXT_FIELDS:
                replace_field(scene, field, f"storyboard.{scene_id}")

    script_path = project_dir / "script.md"
    if script_path.is_file():
        script = script_path.read_text(encoding="utf-8")
        sanitized_script = suppress_editorial_identifiers(script)
        if sanitized_script != script:
            script_path.write_text(sanitized_script, encoding="utf-8")
            changed_fields.append("script.md")

    publish_path = project_dir / "publish.json"
    if publish_path.is_file():
        publish = load_json(publish_path)
        if isinstance(publish, dict):
            publish_changed = False
            for field in ("title", "description", "pinned_comment"):
                value = publish.get(field)
                if isinstance(value, str):
                    sanitized = suppress_editorial_identifiers(value)
                    if sanitized != value:
                        publish[field] = sanitized
                        changed_fields.append(f"publish.{field}")
                        publish_changed = True
            tags = publish.get("tags")
            if isinstance(tags, list):
                sanitized_tags = [
                    suppress_editorial_identifiers(tag) if isinstance(tag, str) else tag for tag in tags
                ]
                if sanitized_tags != tags:
                    publish["tags"] = sanitized_tags
                    changed_fields.append("publish.tags")
                    publish_changed = True
            if publish_changed:
                write_json(publish_path, publish)

    if changed_fields:
        write_json(project_dir / "storyboard.json", storyboard)
    return changed_fields


def slugify(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z가-힣]+", "-", value.strip().lower())
    return value.strip("-")[:72] or "news-short"


def clean_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", html.unescape(value or "")).strip()


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise News2ShortsError(f"명령을 찾을 수 없습니다: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown error").strip()
        raise News2ShortsError(f"명령 실행 실패: {command[0]}: {detail}") from exc


@functools.cache
def verified_ssl_context() -> ssl.SSLContext:
    default_paths = ssl.get_default_verify_paths()
    if default_paths.cafile and Path(default_paths.cafile).is_file():
        return ssl.create_default_context()
    for candidate in (Path("/etc/ssl/cert.pem"), Path("/opt/homebrew/etc/openssl@3/cert.pem")):
        if candidate.is_file():
            return ssl.create_default_context(cafile=str(candidate))
    return ssl.create_default_context()


def keychain_typecast_api_key() -> str:
    if sys.platform != "darwin":
        return ""
    security = shutil.which("security")
    if not security:
        return ""
    try:
        result = subprocess.run(
            [
                security,
                "find-generic-password",
                "-a",
                getpass.getuser(),
                "-s",
                TYPECAST_KEYCHAIN_SERVICE,
                "-w",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def typecast_setup_command(command: str) -> str:
    script = PLUGIN_ROOT / "scripts" / "news2shorts.py"
    return f'python3 "{script}" {command}'


def typecast_keychain_check_limited() -> bool:
    return sys.platform == "darwin" and bool(os.environ.get("CODEX_SANDBOX"))


@functools.cache
def typecast_api_key_record() -> tuple[str, str | None]:
    environment_key = os.environ.get("TYPECAST_API_KEY", "").strip()
    if environment_key:
        return environment_key, "environment"
    keychain_key = keychain_typecast_api_key()
    if keychain_key:
        return keychain_key, "keychain"
    return "", None


def resolve_project_file(project_dir: Path, relative: str, *, must_exist: bool = True) -> Path:
    if not relative:
        raise News2ShortsError("빈 파일 경로는 사용할 수 없습니다.")
    candidate = (project_dir / relative).resolve()
    try:
        candidate.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise News2ShortsError(f"프로젝트 밖의 파일은 사용할 수 없습니다: {relative}") from exc
    if must_exist and not candidate.is_file():
        raise News2ShortsError(f"파일을 찾을 수 없습니다: {relative}")
    return candidate


def naver_headers() -> dict[str, str]:
    client_id = os.environ.get("NAVER_API_HUB_CLIENT_ID", "").strip()
    client_secret = os.environ.get("NAVER_API_HUB_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise News2ShortsError(
            "NAVER API HUB 자격 증명이 없습니다. "
            "NAVER_API_HUB_CLIENT_ID와 NAVER_API_HUB_CLIENT_SECRET을 설정하세요."
        )
    return {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
        "Content-Type": "application/json",
        "User-Agent": "news2shorts/0.1",
    }


def naver_call(path: str, *, params: dict[str, object] | None = None, body: object | None = None) -> dict:
    url = f"{NAVER_BASE_URL}{path}"
    if params:
        url = f"{url}?{parse.urlencode(params)}"
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    method = "POST" if payload is not None else "GET"
    req = request.Request(url, data=payload, headers=naver_headers(), method=method)
    try:
        with request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise News2ShortsError(f"NAVER API HUB 요청 실패: HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise News2ShortsError(f"NAVER API HUB 연결 실패: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise News2ShortsError("NAVER API HUB 응답이 JSON이 아닙니다.") from exc


def parse_pubdate(value: str) -> dt.datetime | None:
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def title_tokens(title: str) -> set[str]:
    tokens = re.findall(r"[0-9A-Za-z가-힣]{2,}", title.lower())
    return {token for token in tokens if token not in STOP_WORDS and not token.isdigit()}


def domain_for(article: dict) -> str:
    url = article.get("originallink") or article.get("link") or ""
    return parse.urlsplit(url).netloc.lower().removeprefix("www.")


def title_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = len(left & right)
    if overlap < 2:
        return 0.0
    return overlap / len(left | right)


def normalized_source_url(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = parse.urlsplit(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    host = parsed.netloc.lower().removeprefix("www.")
    path = re.sub(r"/{2,}", "/", parsed.path or "/").rstrip("/") or "/"
    return parse.urlunsplit((parsed.scheme.lower(), host, path, parsed.query, ""))


def used_topic_match_terms(value: object) -> set[str]:
    tokens = [
        token
        for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", str(value or "").lower())
        if token not in STOP_WORDS and not token.isdigit()
    ]
    terms = {token for token in tokens if len(token) >= 4}
    for index in range(len(tokens) - 1):
        combined = tokens[index] + tokens[index + 1]
        if 4 <= len(combined) <= 24:
            terms.add(combined)
    return terms


def is_news2shorts_history_project(project: object) -> bool:
    if not isinstance(project, dict):
        return False
    profile = project.get("shorts_profile")
    if not isinstance(profile, dict):
        return False
    has_editorial_profile = any(
        str(profile.get(field) or "").strip()
        for field in ("hook", "issue_focus", "viewer_stake", "payoff")
    )
    has_topic_identity = any(
        str(project.get(field) or "").strip()
        for field in ("title", "topic", "source_url")
    )
    return has_editorial_profile and has_topic_identity


def load_used_topic_history(project_history_root: Path) -> tuple[list[dict], list[str]]:
    if not project_history_root.is_dir():
        return [], [f"기존 프로젝트 이력 경로를 찾지 못했습니다: {project_history_root}"]

    records: list[dict] = []
    warnings: list[str] = []
    for project_file in sorted(project_history_root.rglob("project.json")):
        try:
            project = load_json(project_file)
        except News2ShortsError as exc:
            warnings.append(str(exc))
            continue
        if not is_news2shorts_history_project(project):
            continue

        assert isinstance(project, dict)
        profile = project.get("shorts_profile") or {}
        text_values = [
            project.get("title"),
            project.get("topic"),
            profile.get("hook"),
            profile.get("hook_stake"),
            profile.get("issue_focus"),
            profile.get("viewer_stake"),
            profile.get("payoff"),
        ]
        source_urls = {normalized_source_url(project.get("source_url"))}
        sources_file = project_file.parent / "sources.json"
        if sources_file.is_file():
            try:
                sources_payload = load_json(sources_file)
            except News2ShortsError as exc:
                warnings.append(str(exc))
            else:
                if isinstance(sources_payload, dict):
                    for source in sources_payload.get("sources") or []:
                        if not isinstance(source, dict):
                            continue
                        text_values.append(source.get("title"))
                        source_urls.add(normalized_source_url(source.get("url")))

        texts = [str(value).strip() for value in text_values if str(value or "").strip()]
        match_terms: set[str] = set()
        for value in texts:
            match_terms.update(used_topic_match_terms(value))
        records.append(
            {
                "project_path": project_file.parent.relative_to(project_history_root).as_posix(),
                "status": str(project.get("status") or "").strip(),
                "title": str(project.get("title") or "").strip(),
                "topic": str(project.get("topic") or "").strip(),
                "texts": texts,
                "source_urls": {url for url in source_urls if url},
                "match_terms": match_terms,
            }
        )
    return records, warnings


def match_used_topic(candidate: dict, history: list[dict]) -> dict | None:
    candidate_texts = [str(candidate.get("title") or "").strip()]
    candidate_urls: set[str] = set()
    for source in candidate.get("sources") or []:
        if not isinstance(source, dict):
            continue
        title = str(source.get("title") or "").strip()
        if title:
            candidate_texts.append(title)
        for field in ("url", "naver_url"):
            normalized = normalized_source_url(source.get(field))
            if normalized:
                candidate_urls.add(normalized)

    candidate_terms: set[str] = set()
    for value in candidate_texts:
        candidate_terms.update(used_topic_match_terms(value))

    best_match: dict | None = None
    for record in history:
        shared_urls = sorted(candidate_urls & record["source_urls"])
        best_token_score = 0.0
        best_text_score = 0.0
        for candidate_text in candidate_texts:
            candidate_tokens = title_tokens(candidate_text)
            for history_text in record["texts"]:
                best_token_score = max(
                    best_token_score,
                    title_similarity(candidate_tokens, title_tokens(history_text)),
                )
                best_text_score = max(best_text_score, text_similarity(candidate_text, history_text))
        shared_terms = sorted(
            candidate_terms & record["match_terms"],
            key=lambda term: (-len(term), term),
        )

        reason = ""
        if shared_urls:
            reason = "기존 프로젝트와 동일한 출처 URL"
        elif best_token_score >= USED_TOPIC_TOKEN_SIMILARITY_THRESHOLD:
            reason = "기존 프로젝트와 핵심 제목어가 같은 뉴스 군집"
        elif best_text_score >= USED_TOPIC_TEXT_SIMILARITY_THRESHOLD:
            reason = "기존 프로젝트의 제목·주제와 유사한 뉴스 군집"
        elif len(shared_terms) >= USED_TOPIC_MIN_SHARED_TERMS:
            reason = "기존 프로젝트와 복수의 고유 주제어가 일치하는 뉴스 군집"
        if not reason:
            continue

        match = {
            "reason": reason,
            "project_path": record["project_path"],
            "project_status": record["status"],
            "project_title": record["title"],
            "project_topic": record["topic"],
            "shared_terms": shared_terms[:8],
            "token_similarity": round(best_token_score, 3),
            "text_similarity": round(best_text_score, 3),
            "same_source_url": bool(shared_urls),
        }
        match_rank = (
            1 if shared_urls else 0,
            best_token_score,
            best_text_score,
            len(shared_terms),
        )
        if best_match is None or match_rank > best_match["_rank"]:
            best_match = {**match, "_rank": match_rank}

    if best_match is not None:
        best_match.pop("_rank", None)
    return best_match


def matching_terms(text: str, terms: set[str]) -> list[str]:
    normalized = text.lower()
    return sorted(term for term in terms if term in normalized)


def topic_signals(items: list[dict]) -> dict[str, object]:
    text = " ".join(f"{item.get('title', '')} {item.get('description', '')}" for item in items)
    political_terms = matching_terms(text, POLITICAL_TERMS)
    sensitivity_categories = [
        category
        for category, terms in CITIZEN_SENSITIVITY_TERMS.items()
        if matching_terms(text, terms)
    ]
    accountability_terms = matching_terms(text, ACCOUNTABILITY_TERMS)
    return {
        "politics": bool(political_terms),
        "political_terms": political_terms[:5],
        "citizen_sensitive": bool(sensitivity_categories),
        "citizen_sensitivity_categories": sensitivity_categories,
        "accountability": bool(accountability_terms),
        "accountability_terms": accountability_terms[:5],
    }


def citizen_impact_gate(items: list[dict]) -> dict[str, object]:
    """Reject news clusters that do not expose a direct citizen consequence."""

    text = " ".join(f"{item.get('title', '')} {item.get('description', '')}" for item in items)
    affected_groups = matching_terms(text, CITIZEN_AFFECTED_GROUP_TERMS)
    cost_terms = matching_terms(text, CITIZEN_COST_TERMS)
    harm_terms = matching_terms(text, CITIZEN_HARM_TERMS)
    protection_terms = matching_terms(text, CITIZEN_PROTECTION_TERMS)
    rights_terms = matching_terms(text, CITIZEN_RIGHTS_TERMS)
    public_service_terms = matching_terms(text, CITIZEN_PUBLIC_SERVICE_TERMS)
    internal_terms = matching_terms(text, INTERNAL_STAKEHOLDER_TERMS)
    external_terms = matching_terms(text, EXTERNAL_PUBLIC_CONSEQUENCE_TERMS)
    measurable = bool(CITIZEN_MEASURABLE_CONSEQUENCE_PATTERN.search(text))

    paths: list[str] = []
    if affected_groups and cost_terms and measurable:
        paths.append("direct-household-cost")
    if harm_terms and affected_groups and (protection_terms or public_service_terms):
        paths.append("safety-or-protection-failure")
    if affected_groups and rights_terms:
        paths.append("rights-or-access-loss")
    if affected_groups and public_service_terms and rights_terms:
        paths.append("public-service-failure")

    internal_only = bool(internal_terms) and not bool(external_terms) and not bool(
        {"rights-or-access-loss", "safety-or-protection-failure", "public-service-failure"} & set(paths)
    )
    eligible = bool(paths) and not internal_only
    reasons: list[str] = []
    if not affected_groups:
        reasons.append("영향받는 시민·소비자·가구·이용자 집단이 제목과 요약에 드러나지 않음")
    if not paths:
        reasons.append("직접 비용·안전·권리·공공서비스 결과가 확인되지 않음")
    if internal_only:
        reasons.append("외부 시민 결과가 확인되지 않은 조직 내부 이해관계")
    if eligible:
        reasons.append("직접 시민 결과 경로 확인")

    return {
        "eligible": eligible,
        "paths": paths,
        "affected_groups": affected_groups[:8],
        "cost_terms": cost_terms[:8],
        "harm_terms": harm_terms[:8],
        "protection_terms": protection_terms[:8],
        "rights_terms": rights_terms[:8],
        "public_service_terms": public_service_terms[:8],
        "measurable_consequence": measurable,
        "internal_stakeholder_only": internal_only,
        "reasons": reasons,
        "manual_requirement": (
            "최종 후보에는 출처로 뒷받침되는 '누가 무엇을 얼마나 잃거나 위험해지는가' 한 문장을 작성해야 합니다."
        ),
    }


def load_community_signals(path_value: str | None) -> list[dict[str, str]]:
    if not path_value:
        return []
    path = Path(path_value).expanduser().resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise News2ShortsError(f"커뮤니티 신호 파일을 읽지 못했습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise News2ShortsError("커뮤니티 신호 파일이 올바른 JSON이 아닙니다.") from exc
    raw_signals = payload.get("signals") if isinstance(payload, dict) else payload
    if not isinstance(raw_signals, list):
        raise News2ShortsError("커뮤니티 신호 파일은 배열 또는 signals 배열을 포함한 객체여야 합니다.")
    if len(raw_signals) > 50:
        raise News2ShortsError("커뮤니티 신호는 현재 검토에 필요한 50개 이하만 사용할 수 있습니다.")
    signals: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for index, value in enumerate(raw_signals, start=1):
        if not isinstance(value, dict):
            raise News2ShortsError(f"커뮤니티 신호 {index}은 객체여야 합니다.")
        title = clean_html(str(value.get("title") or ""))[:180]
        community = re.sub(r"\s+", " ", str(value.get("community") or "")).strip()[:80]
        url = str(value.get("url") or "").strip()
        parsed = parse.urlsplit(url)
        if not title or not community or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise News2ShortsError(
                f"커뮤니티 신호 {index}에는 title, community, 공개 http(s) URL이 필요합니다."
            )
        if url in seen_urls:
            continue
        seen_urls.add(url)
        signals.append({"title": title, "community": community, "url": url})
    return signals


def matching_community_signals(token_set: set[str], signals: list[dict[str, str]]) -> list[dict[str, str]]:
    matched: list[dict[str, str]] = []
    for signal in signals:
        if title_similarity(token_set, title_tokens(signal["title"])) >= COMMUNITY_SIGNAL_MATCH_THRESHOLD:
            matched.append(signal)
    return matched[:8]


def text_similarity(left: str, right: str) -> float:
    normalized_left = re.sub(r"[^0-9A-Za-z가-힣]", "", left.lower())
    normalized_right = re.sub(r"[^0-9A-Za-z가-힣]", "", right.lower())
    if min(len(normalized_left), len(normalized_right)) < 8:
        return 0.0
    return SequenceMatcher(None, normalized_left, normalized_right).ratio()


def has_shared_significant_term(left: object, right: object) -> bool:
    """Check whether two Korean editorial fields share a meaningful visible term."""

    left_terms = {
        term
        for term in re.findall(r"[0-9A-Za-z가-힣]{2,}", str(left or "").lower())
        if term not in STOP_WORDS
    }
    normalized_right = re.sub(r"[^0-9A-Za-z가-힣]", "", str(right or "").lower())
    return any(re.sub(r"[^0-9A-Za-z가-힣]", "", term) in normalized_right for term in left_terms)


def ends_with_question(value: object) -> bool:
    return bool(re.search(r"[?？]\s*$", str(value or "").strip()))


def is_summary_lead(value: object) -> bool:
    normalized = re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "").lower())
    return any(normalized.startswith(prefix) for prefix in SUMMARY_LEAD_PREFIXES)


def has_citizen_stake(value: object) -> bool:
    normalized = re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "").lower())
    return any(term in normalized for term in CITIZEN_STAKE_TERMS)


def normalized_company_name(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "").lower())


def screen_copy_issues(field: str, value: object) -> list[str]:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        return []
    issues: list[str] = []
    limit = SCREEN_COPY_LIMITS.get(field)
    if limit and len(text) > limit:
        issues.append(f"{field}은 {limit}자 이하의 짧은 명사형 문구여야 합니다: {len(text)}자")
    ending_check = re.sub(r"[.!?…]+$", "", text).strip()
    if SCREEN_SENTENCE_ENDING_PATTERN.search(ending_check):
        example = SCREEN_COPY_EXAMPLES.get(field, "비정상 상태 · 원인 미확인")
        issues.append(
            f"{field}은 서술문 대신 명사형 화면 문구를 사용하세요: "
            f"예: `{example}`"
        )
    return issues


def contains_publish_link(value: object) -> bool:
    text = str(value or "")
    return bool(PUBLISH_MARKDOWN_LINK_PATTERN.search(text) or PUBLISH_LINK_PATTERN.search(text))


def link_free_upload_text(value: object) -> str:
    text = PUBLISH_MARKDOWN_LINK_PATTERN.sub(r"\1", str(value or ""))
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = PUBLISH_LINK_PATTERN.sub("", raw_line)
        line = re.sub(r"[ \t]+", " ", line).strip()
        line = re.sub(r"[:：]\s*$", "", line).rstrip()
        cleaned_lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()


def is_public_production_disclosure(value: object) -> bool:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return bool(text) and any(pattern.search(text) for pattern in PUBLIC_DESCRIPTION_PRODUCTION_PATTERNS)


def contains_public_production_disclosure(value: object) -> bool:
    for raw_line in str(value or "").splitlines():
        for sentence in re.split(r"(?<=[.!?])\s+", raw_line):
            if is_public_production_disclosure(sentence):
                return True
    return False


def public_upload_description(value: object) -> str:
    text = link_free_upload_text(value)
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        sentences = re.split(r"(?<=[.!?])\s+", raw_line)
        kept = [sentence.strip() for sentence in sentences if not is_public_production_disclosure(sentence)]
        cleaned_lines.append(" ".join(sentence for sentence in kept if sentence))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()


def duplicated_title_sentences(title: object, description: object) -> list[str]:
    title_text = PUBLISH_HASHTAG_PATTERN.sub("", str(title or "")).strip()
    normalized_title = re.sub(r"[^0-9A-Za-z가-힣]", "", title_text.lower())
    if not normalized_title:
        return []

    duplicates: list[str] = []
    for raw_line in public_upload_description(description).splitlines():
        if raw_line.strip() == "출처":
            break
        for sentence in re.split(r"(?<=[.!?])\s+", raw_line):
            candidate = PUBLISH_HASHTAG_PATTERN.sub("", sentence).strip()
            normalized_candidate = re.sub(r"[^0-9A-Za-z가-힣]", "", candidate.lower())
            if not normalized_candidate:
                continue
            if normalized_candidate == normalized_title or text_similarity(title_text, candidate) >= 0.92:
                duplicates.append(candidate)
    return duplicates


def deduplicated_upload_description(title: object, description: object) -> str:
    duplicate_sentences = set(duplicated_title_sentences(title, description))
    cleaned_lines: list[str] = []
    in_sources = False
    for raw_line in public_upload_description(description).splitlines():
        if raw_line.strip() == "출처":
            in_sources = True
        line = PUBLISH_HASHTAG_PATTERN.sub("", raw_line)
        if not in_sources:
            sentences = re.split(r"(?<=[.!?])\s+", line)
            line = " ".join(
                sentence.strip()
                for sentence in sentences
                if sentence.strip() and sentence.strip() not in duplicate_sentences
            )
        line = re.sub(r"[ \t]+", " ", line).strip()
        cleaned_lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()


def cluster_articles(
    articles: list[dict],
    queries: list[str],
    hours: int,
    community_signals: list[dict[str, str]] | None = None,
) -> list[dict]:
    community_signals = community_signals or []
    clusters: list[dict] = []
    for article in articles:
        tokens = title_tokens(article["title"])
        best = None
        best_score = 0.0
        for cluster in clusters:
            similarity = title_similarity(tokens, cluster["token_set"])
            if similarity > best_score:
                best_score = similarity
                best = cluster
        if best is not None and best_score >= 0.25:
            best["items"].append(article)
            best["token_set"].update(tokens)
            best["queries"].add(article["query"])
        else:
            clusters.append(
                {
                    "items": [article],
                    "token_set": set(tokens),
                    "queries": {article["query"]},
                }
            )

    current = now_kst()
    candidates: list[dict] = []
    for index, cluster in enumerate(clusters, start=1):
        items = sorted(cluster["items"], key=lambda item: item["published_at"], reverse=True)
        domains = {domain_for(item) for item in items if domain_for(item)}
        newest = dt.datetime.fromisoformat(items[0]["published_at"])
        age_hours = max(0.0, (current - newest).total_seconds() / 3600)
        recent_cutoff = current - dt.timedelta(hours=6)
        recent_items = [item for item in items if dt.datetime.fromisoformat(item["published_at"]) >= recent_cutoff]
        recent_domains = {domain_for(item) for item in recent_items if domain_for(item)}
        signals = topic_signals(items)
        impact_gate = citizen_impact_gate(items)
        matched_community = matching_community_signals(cluster["token_set"], community_signals)
        community_count = len({item["community"].lower() for item in matched_community})
        freshness_score = max(0.0, 15.0 * (1.0 - min(age_hours, hours) / max(hours, 1)))
        velocity_score = min(20.0, len(recent_domains) * 4.0 + len(recent_items) * 2.0)
        source_score = min(15.0, len(domains) * 5.0)
        sensitivity_score = min(20.0, len(signals["citizen_sensitivity_categories"]) * 5.0)
        political_score = 5.0 if signals["politics"] else 0.0
        accountability_score = 10.0 if signals["accountability"] else 0.0
        community_score = 5.0 if community_count >= 3 else 3.0 if community_count == 2 else 0.0
        coverage_score = min(5.0, len(cluster["queries"]) * 2.5)
        verification_score = 5.0 if len(domains) >= 2 else 0.0
        score_components = {
            "freshness": round(freshness_score, 2),
            "news_velocity": round(velocity_score, 2),
            "source_diversity": round(source_score, 2),
            "citizen_sensitivity": round(sensitivity_score, 2),
            "political_relevance": round(political_score, 2),
            "accountability": round(accountability_score, 2),
            "community_signal": round(community_score, 2),
            "query_coverage": round(coverage_score, 2),
            "verification_readiness": round(verification_score, 2),
        }
        base_score = round(sum(score_components.values()), 2)
        keywords = sorted(
            cluster["token_set"],
            key=lambda token: sum(token in title_tokens(item["title"]) for item in items),
            reverse=True,
        )[:5]
        candidates.append(
            {
                "id": f"candidate-{index:02d}",
                "title": items[0]["title"],
                "score": base_score,
                "base_score": base_score,
                "score_breakdown": {"components": score_components, "trend_bonus": 0.0},
                "topic_signals": signals,
                "citizen_impact_gate": impact_gate,
                "hotness_evidence": {
                    "recent_6h_article_count": len(recent_items),
                    "recent_6h_source_count": len(recent_domains),
                    "community_signal_count": len(matched_community),
                    "community_count": community_count,
                    "community_lead_only": True,
                },
                "community_signals": matched_community,
                "keywords": keywords,
                "article_count": len(items),
                "source_count": len(domains),
                "query_count": len(cluster["queries"]),
                "latest_published_at": items[0]["published_at"],
                "sources": [
                    {
                        "title": item["title"],
                        "publisher_domain": domain_for(item),
                        "url": item.get("originallink") or item.get("link"),
                        "naver_url": item.get("link"),
                        "published_at": item["published_at"],
                    }
                    for item in items[:8]
                ],
            }
        )
    return sorted(
        candidates,
        key=lambda candidate: (
            bool(candidate.get("citizen_impact_gate", {}).get("eligible")),
            candidate["score"],
        ),
        reverse=True,
    )


def add_trend_scores(candidates: list[dict]) -> str | None:
    eligible = [candidate for candidate in candidates if candidate.get("keywords")][:5]
    if not eligible:
        return "검색어 트렌드에 전달할 후보 키워드가 없습니다."
    end_date = now_kst().date()
    start_date = end_date - dt.timedelta(days=6)
    keyword_groups = [
        {
            "groupName": candidate["id"],
            "keywords": candidate["keywords"][:5],
        }
        for candidate in eligible
    ]
    response = naver_call(
        "/search-trend/v1/search",
        body={
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "timeUnit": "date",
            "keywordGroups": keyword_groups,
        },
    )
    ratios: dict[str, float] = {}
    for result in response.get("results", []):
        data = result.get("data") or []
        if data:
            ratios[result.get("title", "")] = float(data[-1].get("ratio", 0.0))
    for candidate in candidates:
        ratio = ratios.get(candidate["id"])
        candidate["trend_ratio"] = ratio
        if ratio is not None:
            trend_bonus = round(min(10.0, ratio * 0.1), 2)
            candidate["score_breakdown"]["trend_bonus"] = trend_bonus
            candidate["score"] = round(min(100.0, candidate["base_score"] + trend_bonus), 2)
    candidates.sort(key=lambda candidate: candidate["score"], reverse=True)
    return None


def cmd_doctor(args: argparse.Namespace) -> int:
    try:
        import PIL  # type: ignore

        pillow = PIL.__version__
    except ImportError:
        pillow = None
    font = next((str(path) for path in FONT_CANDIDATES if path.is_file()), None)
    _, typecast_api_key_source = typecast_api_key_record()
    keychain_check_limited = typecast_api_key_source is None and typecast_keychain_check_limited()
    if typecast_api_key_source:
        typecast_guidance = "Typecast API 키를 사용할 수 있습니다."
    elif keychain_check_limited:
        typecast_guidance = (
            "이 Codex 실행에서는 macOS 키체인 확인이 제한될 수 있어 키가 없다고 단정할 수 없습니다. "
            f"사용자 터미널에서 `{typecast_setup_command('doctor')}`를 실행해 다시 확인하고, "
            f"그때도 없으면 `{typecast_setup_command('configure-typecast')}`를 한 번 실행하세요."
        )
    else:
        typecast_guidance = (
            "Typecast API 키가 없습니다. "
            f"`{typecast_setup_command('configure-typecast')}`를 한 번 실행한 뒤 "
            f"`{typecast_setup_command('doctor')}`로 확인하세요."
        )
    brand_intro_info: dict | None = None
    brand_intro_error = ""
    if BRAND_INTRO_ASSET_PATH.is_file():
        try:
            brand_intro_info = probe_video(BRAND_INTRO_ASSET_PATH)
        except News2ShortsError as exc:
            brand_intro_error = str(exc)
    else:
        brand_intro_error = f"공통 인트로 자산이 없습니다: {BRAND_INTRO_ASSET_PATH}"
    brand_intro_ok = bool(
        brand_intro_info
        and brand_intro_info.get("has_video")
        and brand_intro_info.get("has_audio")
        and (brand_intro_info.get("width"), brand_intro_info.get("height")) == OUTPUT_VIDEO_SIZE
    )
    brand_logo_ok = BRAND_LOGO_PATH.is_file()
    report = {
        "ok": bool(
            shutil.which("ffmpeg")
            and shutil.which("ffprobe")
            and pillow
            and font
            and brand_intro_ok
            and brand_logo_ok
        ),
        "plugin_root": str(PLUGIN_ROOT),
        "python": sys.version.split()[0],
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "source_audio_transcription": source_transcription_backends(),
        "source_audio_review_file": SOURCE_AUDIO_REVIEW_FILENAME,
        "pillow": pillow,
        "font": font,
        "local_tts": shutil.which("say"),
        "brand_intro_asset": BRAND_INTRO_ASSET_ID,
        "brand_intro_path": str(BRAND_INTRO_ASSET_PATH),
        "brand_intro_ok": brand_intro_ok,
        "brand_intro_error": brand_intro_error,
        "brand_intro_video": brand_intro_info,
        "brand_intro_transition": DEFAULT_BRAND_INTRO_TRANSITION,
        "brand_intro_transition_duration": DEFAULT_BRAND_INTRO_TRANSITION_DURATION,
        "default_brand_mode": BRAND_MODE_CORNER_LOGO,
        "brand_logo_path": str(BRAND_LOGO_PATH),
        "brand_logo_ok": brand_logo_ok,
        "delivery_modes": sorted(DELIVERY_MODES),
        "visual_first_audio_profile": VISUAL_FIRST_AUDIO_PROFILE,
        "visual_first_audio_vocals": False,
        "cta_tail_variants": list(CTA_TAIL_VARIANTS),
        "cta_tail_selection_strategy": CTA_TAIL_SELECTION_STRATEGY,
        "cta_tail_default_distribution": CTA_TAIL_DEFAULT_DISTRIBUTION,
        "cta_tail_default_distribution_basis": CTA_TAIL_DEFAULT_DISTRIBUTION_BASIS,
        "mid_cta_modes": sorted(MID_CTA_MODES),
        "mid_cta_placement": MID_CTA_PLACEMENT,
        "mid_cta_duration_range": [MID_CTA_MIN_DURATION, MID_CTA_MAX_DURATION],
        "mid_cta_ui_target_profile": MID_CTA_UI_TARGET_PROFILE,
        "mid_cta_arrow_target": {
            "x": MID_CTA_DEFAULT_TARGET_X,
            "y": MID_CTA_DEFAULT_TARGET_Y,
        },
        "default_tts_provider": "typecast",
        "default_visual_source_priority": list(DEFAULT_VISUAL_SOURCE_PRIORITY),
        "default_visual_locale": DEFAULT_VISUAL_LOCALE,
        "default_foreign_visual_fallback": DEFAULT_FOREIGN_VISUAL_FALLBACK,
        "default_generated_visual_style": DEFAULT_KOREAN_GENERATED_STYLE,
        "required_discovery_candidate_count": DISCOVERY_CANDIDATE_COUNT,
        "typecast_outer_silence_trim": {
            "enabled": True,
            "leading_keep_seconds": TYPECAST_LEADING_SILENCE_KEEP_SECONDS,
            "trailing_keep_seconds": TYPECAST_TRAILING_SILENCE_KEEP_SECONDS,
            "threshold_db": TYPECAST_SILENCE_THRESHOLD_DB,
            "internal_pauses_preserved": True,
        },
        "typecast_api_key_configured": typecast_api_key_source is not None,
        "typecast_api_key_source": typecast_api_key_source,
        "typecast_keychain_check_limited": keychain_check_limited,
        "typecast_setup_command": (
            "" if typecast_api_key_source else typecast_setup_command("configure-typecast")
        ),
        "typecast_setup_guidance": typecast_guidance,
        "typecast_voice_mode": "auto",
        "typecast_voice_selection_strategy": TYPECAST_VOICE_SELECTION_STRATEGY,
        "typecast_voice_popularity_basis": TYPECAST_VOICE_POPULARITY_BASIS,
        "typecast_voice_popularity_source": TYPECAST_VOICE_POPULARITY_SOURCE,
        "typecast_voice_candidates": [
            candidate["voice_name"] for candidate in TYPECAST_VOICE_CANDIDATES.values()
        ],
        "typecast_default_voice_distribution": TYPECAST_DEFAULT_VOICE_DISTRIBUTION,
        "typecast_default_voice_distribution_basis": TYPECAST_DEFAULT_VOICE_DISTRIBUTION_BASIS,
        "typecast_fallback_voice_id": TYPECAST_VOICE_ID,
        "typecast_fallback_voice_name": TYPECAST_VOICE_NAME,
        "typecast_voice_id": TYPECAST_VOICE_ID,
        "typecast_voice_name": TYPECAST_VOICE_NAME,
        "naver_api_hub_configured": bool(
            os.environ.get("NAVER_API_HUB_CLIENT_ID")
            and os.environ.get("NAVER_API_HUB_CLIENT_SECRET")
        ),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["ok"] else 1


def cmd_configure_typecast(args: argparse.Namespace) -> int:
    if sys.platform != "darwin":
        raise News2ShortsError(
            "macOS 키체인은 이 운영체제에서 사용할 수 없습니다. "
            "TYPECAST_API_KEY 환경변수를 설정하세요."
        )
    security = shutil.which("security")
    if not security:
        raise News2ShortsError("macOS security 명령을 찾을 수 없습니다.")

    print("Typecast API 키를 macOS 키체인에 저장합니다.")
    print("표시되는 password 프롬프트에 API 키를 입력하세요. 입력 내용은 화면에 표시되지 않습니다.")
    try:
        result = subprocess.run(
            [
                security,
                "add-generic-password",
                "-U",
                "-a",
                getpass.getuser(),
                "-s",
                TYPECAST_KEYCHAIN_SERVICE,
                "-l",
                TYPECAST_KEYCHAIN_LABEL,
                "-w",
            ],
            check=False,
        )
    except OSError as exc:
        raise News2ShortsError(f"macOS 키체인 실행 실패: {exc}") from exc
    if result.returncode != 0:
        raise News2ShortsError("Typecast API 키를 macOS 키체인에 저장하지 못했습니다.")

    typecast_api_key_record.cache_clear()
    if not keychain_typecast_api_key():
        raise News2ShortsError("저장 후 Typecast API 키를 macOS 키체인에서 확인하지 못했습니다.")
    print("Typecast API 키를 macOS 키체인에 저장했습니다.")
    print("Typecast 보이스 자동 선택을 사용합니다.")
    print(f"선택 전략: {TYPECAST_VOICE_SELECTION_STRATEGY}")
    print(f"인기 후보 근거: {TYPECAST_VOICE_POPULARITY_BASIS}")
    print("후보: " + ", ".join(candidate["voice_name"] for candidate in TYPECAST_VOICE_CANDIDATES.values()))
    print(f"일반 자동 선택: {TYPECAST_DEFAULT_VOICE_DISTRIBUTION}")
    print(f"기본 대체 보이스: {TYPECAST_VOICE_NAME} ({TYPECAST_VOICE_ID})")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    queries = args.query or DEFAULT_QUERIES
    if not 1 <= args.limit <= 100:
        fail("--limit은 1에서 100 사이여야 합니다.")
    if not 1 <= args.hours <= 168:
        fail("--hours는 1에서 168 사이여야 합니다.")
    if args.candidates != DISCOVERY_CANDIDATE_COUNT:
        fail(f"--candidates는 {DISCOVERY_CANDIDATE_COUNT}만 허용합니다.")
    effective_hours = min(args.hours, 24) if args.hot_real_news else args.hours
    cutoff = now_kst() - dt.timedelta(hours=effective_hours)
    seen: set[str] = set()
    articles: list[dict] = []
    for query in queries:
        response = naver_call(
            "/search/v1/news",
            params={"query": query, "display": args.limit, "start": 1, "sort": "date", "format": "json"},
        )
        for raw in response.get("items", []):
            title = clean_html(raw.get("title", ""))
            published = parse_pubdate(raw.get("pubDate", ""))
            if not title or published is None or published < cutoff:
                continue
            unique_key = raw.get("originallink") or raw.get("link") or title
            if unique_key in seen:
                continue
            seen.add(unique_key)
            articles.append(
                {
                    "title": title,
                    "description": clean_html(raw.get("description", "")),
                    "originallink": raw.get("originallink", ""),
                    "link": raw.get("link", ""),
                    "published_at": published.isoformat(timespec="seconds"),
                    "query": query,
                }
            )

    community_signals = load_community_signals(args.community_signals)
    candidates = cluster_articles(articles, queries, effective_hours, community_signals)
    project_history_root = Path(args.project_history_root).expanduser().resolve()
    used_topic_history, history_warnings = load_used_topic_history(project_history_root)
    warnings: list[str] = list(history_warnings)
    new_candidates: list[dict] = []
    excluded_used_topics: list[dict] = []
    for candidate in candidates:
        history_match = match_used_topic(candidate, used_topic_history)
        if history_match is None:
            new_candidates.append(candidate)
            continue
        excluded_used_topics.append(
            {
                "id": candidate["id"],
                "title": candidate["title"],
                "score": candidate["score"],
                "history_match": history_match,
            }
        )
    if not args.skip_trends and new_candidates:
        try:
            warning = add_trend_scores(new_candidates)
            if warning:
                warnings.append(warning)
        except News2ShortsError as exc:
            warnings.append(f"검색어 트렌드 점수를 생략했습니다: {exc}")
    qualified_candidates = [
        candidate
        for candidate in new_candidates
        if candidate.get("citizen_impact_gate", {}).get("eligible") is True
    ]
    rejected_candidates = [
        {
            "id": candidate["id"],
            "title": candidate["title"],
            "score": candidate["score"],
            "citizen_impact_gate": candidate.get("citizen_impact_gate", {}),
        }
        for candidate in new_candidates
        if candidate.get("citizen_impact_gate", {}).get("eligible") is not True
    ]
    if args.hot_real_news:
        hot_candidates: list[dict] = []
        for candidate in qualified_candidates:
            hotness = candidate.get("hotness_evidence") or {}
            if (
                int(hotness.get("recent_6h_source_count") or 0) >= 2
                and int(candidate.get("source_count") or 0) >= 2
            ):
                hot_candidates.append(candidate)
            else:
                rejected_candidates.append(
                    {
                        "id": candidate["id"],
                        "title": candidate["title"],
                        "score": candidate["score"],
                        "hot_real_news_gate": {
                            "eligible": False,
                            "reason": "최근 6시간 내 서로 다른 출처 2곳 이상에서 확인되지 않았습니다.",
                        },
                    }
                )
        qualified_candidates = hot_candidates
    discovery_complete = len(qualified_candidates) >= DISCOVERY_CANDIDATE_COUNT
    candidate_shortfall = max(0, DISCOVERY_CANDIDATE_COUNT - len(qualified_candidates))
    if not discovery_complete:
        warnings.append(
            f"검증된 후보가 {len(qualified_candidates)}/{DISCOVERY_CANDIDATE_COUNT}개입니다. "
            "시간 범위·검색 레인·기사 수를 넓혀 10개를 채우기 전까지 완료 목록으로 사용하지 마세요."
        )

    result = {
        "version": 6,
        "as_of": iso_now(),
        "timezone": "Asia/Seoul",
        "window_hours": effective_hours,
        "discovery_mode": "hot-real-news" if args.hot_real_news else "standard",
        "queries": queries,
        "article_count": len(articles),
        "project_history_root": str(project_history_root),
        "project_history_count": len(used_topic_history),
        "used_topic_exclusion_policy": (
            "현재 projects 이력의 news2shorts project.json과 sources.json을 먼저 읽고, "
            "동일 출처 URL 또는 제목·주제·교차검증 기사 기준으로 같은 뉴스 군집을 후보에서 제외합니다. "
            "초안·수정 대기·렌더 완료 상태를 모두 이미 다룬 주제로 봅니다."
        ),
        "candidate_count_before_history_gate": len(candidates),
        "excluded_used_topic_count": len(excluded_used_topics),
        "community_signal_count": len(community_signals),
        "community_signal_policy": (
            "공개 커뮤니티의 제목과 URL은 이슈 발견 신호일 뿐 사실·여론 근거가 아닙니다. "
            "서로 다른 두 커뮤니티 이상이 같은 검증된 뉴스 군집과 일치할 때만 제한적으로 가산합니다."
        ),
        "score_disclaimer": "후보 검토 우선순위이며 조회수 예측이나 국민 여론 측정값이 아닙니다.",
        "citizen_impact_gate_policy": (
            "추천 후보는 영향받는 집단과 직접 비용·안전·권리·공공서비스 결과를 함께 확인해야 합니다. "
            "외부 시민 결과가 없는 조직 내부 이해관계와 간접 정치 공방은 추천 목록에서 제외합니다."
        ),
        "candidate_count_before_citizen_gate": len(new_candidates),
        "qualified_candidate_count": len(qualified_candidates),
        "required_candidate_count": DISCOVERY_CANDIDATE_COUNT,
        "discovery_complete": discovery_complete,
        "candidate_shortfall": candidate_shortfall,
        "score_model": {
            "freshness": 15,
            "news_velocity": 20,
            "source_diversity": 15,
            "citizen_sensitivity": 20,
            "political_relevance": 5,
            "accountability": 10,
            "community_signal": 5,
            "query_coverage": 5,
            "verification_readiness": 5,
            "search_trend_bonus": 10,
            "score_cap": 100,
        },
        "warnings": warnings,
        "candidates": qualified_candidates[:DISCOVERY_CANDIDATE_COUNT],
        "excluded_used_topics": excluded_used_topics[:DISCOVERY_CANDIDATE_COUNT],
        "rejected_candidates": rejected_candidates[:DISCOVERY_CANDIDATE_COUNT],
    }
    if args.output:
        output = Path(args.output).expanduser().resolve()
        write_json(output, result)
        print(output)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if discovery_complete else 2


def ensure_empty_project_dir(project_dir: Path) -> None:
    if project_dir.exists() and any(project_dir.iterdir()):
        raise News2ShortsError(f"프로젝트 디렉터리가 비어 있지 않습니다: {project_dir}")
    project_dir.mkdir(parents=True, exist_ok=True)


def cmd_init(args: argparse.Namespace) -> int:
    if not args.title.strip():
        fail("--title은 비어 있을 수 없습니다.")
    delivery_mode = str(args.delivery_mode or CONTINUOUS_FLOW_MODE).strip()
    if delivery_mode not in DELIVERY_MODES:
        fail("--delivery-mode는 continuous-flow 또는 visual-first여야 합니다.")
    narration_style = str(
        args.narration_style or NARRATION_STYLE_STANDARD
    ).strip()
    if narration_style not in NARRATION_STYLES:
        fail("--narration-style은 standard 또는 cc-helper-conversational이어야 합니다.")
    if (
        delivery_mode == VISUAL_FIRST_MODE
        and narration_style != NARRATION_STYLE_STANDARD
    ):
        fail("visual-first는 내레이션이 없어 cc-helper-conversational 말투를 사용할 수 없습니다.")
    if args.duration is None:
        duration = (
            VISUAL_FIRST_DEFAULT_DURATION_SECONDS
            if delivery_mode == VISUAL_FIRST_MODE
            else CONTINUOUS_FLOW_DEFAULT_DURATION_SECONDS
        )
    else:
        duration = int(args.duration)
    if delivery_mode == VISUAL_FIRST_MODE:
        if not VISUAL_FIRST_MIN_DURATION_SECONDS <= duration <= VISUAL_FIRST_MAX_DURATION_SECONDS:
            fail(
                "visual-first --duration은 "
                f"{VISUAL_FIRST_MIN_DURATION_SECONDS}에서 {VISUAL_FIRST_MAX_DURATION_SECONDS}초 사이여야 합니다."
            )
    elif not CONTINUOUS_FLOW_MIN_DURATION_SECONDS <= duration <= CONTINUOUS_FLOW_MAX_DURATION_SECONDS:
        fail(
            "continuous-flow --duration은 "
            f"{CONTINUOUS_FLOW_MIN_DURATION_SECONDS}에서 {CONTINUOUS_FLOW_MAX_DURATION_SECONDS}초 사이여야 합니다."
        )
    if args.source_url:
        parsed_source = parse.urlsplit(args.source_url)
        if parsed_source.scheme not in {"http", "https"} or not parsed_source.netloc:
            fail("--source-url은 http 또는 https 뉴스 URL이어야 합니다.")
    created_at = iso_now()
    slug = slugify(args.title)
    project_dir = (
        Path(args.project_dir).expanduser().resolve()
        if args.project_dir
        else (Path.cwd() / "outputs" / now_kst().date().isoformat() / slug).resolve()
    )
    ensure_empty_project_dir(project_dir)
    (project_dir / "assets" / "generated").mkdir(parents=True)
    (project_dir / "assets" / "collected").mkdir(parents=True)
    (project_dir / "audio").mkdir(parents=True)

    project = load_json(TEMPLATE_ROOT / "project.template.json")
    assert isinstance(project, dict)
    project.update(
        {
            "title": args.title,
            "slug": slug,
            "topic": args.title,
            "source_url": args.source_url or "",
            "created_at": created_at,
            "updated_at": created_at,
            "target_duration_seconds": duration,
            "sensitive_topic": args.sensitive,
            "delivery_mode": delivery_mode,
            "narration_style": narration_style,
            "format_selection": {
                "mode": args.format_mode,
                "selected": args.style,
                "reason": args.format_reason,
                "confidence": args.format_confidence,
            },
            "shorts_profile": {
                "hook_type": args.hook_type,
                "hook": "",
                "hook_stake": "",
                "issue_focus": "",
                "viewer_stake": "",
                "tension_question": "",
                "visual_attention_device": "",
                "visual_attention_scene_id": "",
                "visual_attention_reason": "",
                "open_loop": "",
                "midpoint_rehook": "",
                "early_rehook_scene_id": "",
                "first_answer_scene_id": "",
                "truth_guard_scene_id": "",
                "withheld_detail": "",
                "truth_guard": "",
                "payoff": "",
                "loop_close": "",
            },
            "visual_style": {
                "template": args.style,
                "brand_name": "",
                "accent_color": "#FFF200",
                "display_headline": args.title,
                "headline_highlight": "",
                "screen_copy_mode": SCREEN_COPY_MODE_NOUN_PHRASES,
                "show_fact_stack_index": False,
                "show_payoff_label": True,
                "payoff_panel_style": "editorial-card",
                "show_source_label": True,
            },
        }
    )
    visual_sourcing = project.get("visual_sourcing")
    visual_style = project.get("visual_style")
    assert isinstance(visual_sourcing, dict) and isinstance(visual_style, dict)
    visual_sourcing["mode"] = args.visual_mode
    visual_sourcing["hot_real_news"] = {
        "enabled": args.visual_mode in {"hot-real-news", "whiteboard"},
        "max_age_hours": 24,
        "min_recent_6h_source_count": 2,
        "allow_unreviewed_local_draft": True,
    }
    visual_sourcing["whiteboard"] = {
        "enabled": args.visual_mode == "whiteboard",
        "renderer": "whiteboard-shorts",
        "project_dir": "whiteboard-project",
        "source_rights_inherited": True,
    }
    if args.international_source_country:
        source_country = str(args.international_source_country).strip().upper()
        source_locale = str(args.international_source_locale or "").strip()
        citizen_stake = str(args.international_citizen_stake or "").strip()
        if not re.fullmatch(r"[A-Z]{2}", source_country):
            fail("--international-source-country는 ISO 2자리 국가 코드여야 합니다.")
        if len(source_locale) < 2:
            fail("--international-source-locale을 입력하세요.")
        if len(re.sub(r"\s+", "", citizen_stake)) < 8:
            fail("--international-citizen-stake에 한국 시민 영향을 구체적으로 입력하세요.")
        visual_sourcing.update(
            {
                "korean_visuals_required": False,
                "visual_locale": INTERNATIONAL_VISUAL_LOCALE,
                "foreign_visual_fallback": INTERNATIONAL_FOREIGN_VISUAL_FALLBACK,
                "korean_context_review_required": False,
                "generated_style": INTERNATIONAL_GENERATED_STYLE,
                "international_source_visuals": {
                    "enabled": True,
                    "source_country": source_country,
                    "source_locale": source_locale,
                    "actual_event_only": True,
                    "rights_review_required": True,
                    "citizen_stake": citizen_stake,
                },
            }
        )
    visual_style["render_mode"] = args.visual_mode
    brand_intro = project.get("brand_intro")
    mid_cta = project.get("mid_cta")
    cta_tail = project.get("cta_tail")
    audio_bed = project.get("audio_bed")
    assert (
        isinstance(brand_intro, dict)
        and isinstance(mid_cta, dict)
        and isinstance(cta_tail, dict)
        and isinstance(audio_bed, dict)
    )
    brand_intro.update(
        {
            "enabled": True,
            "mode": BRAND_MODE_CORNER_LOGO,
            "asset": BRAND_INTRO_ASSET_ID,
            "position": "top-left",
        }
    )
    cta_tail["duration"] = DEFAULT_CTA_TAIL_DURATION
    cta_tail["narration"] = DEFAULT_CTA_NARRATION
    mid_cta["mode"] = str(args.mid_cta_mode or "auto")
    if delivery_mode == VISUAL_FIRST_MODE:
        cta_tail["voice_enabled"] = False
        audio_bed.update(
            {
                "enabled": True,
                "mode": "renderer-generated",
                "profile": VISUAL_FIRST_AUDIO_PROFILE,
                "vocals": False,
                "path": VISUAL_FIRST_AUDIO_PATH,
            }
        )
    else:
        audio_bed.update(
            {
                "enabled": False,
                "mode": "none",
                "profile": "",
                "vocals": False,
                "path": "",
            }
        )
    write_json(project_dir / "project.json", project)
    sources = {"version": 1, "as_of": created_at, "sources": []}
    if args.source_url:
        sources["sources"].append(
            {
                "id": "source-01",
                "title": args.title,
                "publisher": "",
                "url": args.source_url,
                "published_at": "",
                "updated_at": "",
                "retrieved_at": created_at,
                "type": "original_article",
            }
        )
    write_json(project_dir / "sources.json", sources)
    write_json(project_dir / "fact-sheet.json", {"version": 1, "claims": []})
    write_json(
        project_dir / "storyboard.json",
        {
            "version": 6,
            "title": args.title,
            "as_of": created_at,
            "format": args.style,
            "hook_type": args.hook_type,
            "scenes": [],
        },
    )
    write_json(project_dir / "rights-manifest.json", {"version": 2, "searches": [], "assets": []})
    write_json(
        project_dir / "publish.json",
        {
            "version": 5,
            "title": "",
            "description": "",
            "tags": [],
            "source_lines": [],
            "contains_synthetic_media": False,
            "pinned_comment": "",
            "upload_settings": {
                "thumbnail_method": "file_upload",
                "thumbnail_file": DEFAULT_THUMBNAIL_PATH,
                "thumbnail_status": "pending",
                "thumbnail_hook": "",
                "thumbnail_subhook": "",
                "thumbnail_badge": "",
                "thumbnail_style": "auto",
                "thumbnail_presenter_file": "",
                "thumbnail_note": f"별도 호기심 유도 썸네일 파일: {DEFAULT_THUMBNAIL_PATH}",
                "playlist": "선택 안 함",
                "audience": "not_made_for_kids",
                "category": "News & Politics",
                "video_language": "ko",
                "altered_content": "review_required",
                "paid_promotion": False,
                "age_restriction": "review_required",
                "allow_comments": True,
                "visibility": "private",
                "schedule_at": "",
            },
        },
    )
    (project_dir / "script.md").write_text(
        "# 쇼츠 대본\n\n"
        "## 후크 후보\n\n1. \n2. \n3. \n\n"
        f"## 선택한 후크\n\n- 유형: {args.hook_type}\n- 문장: \n\n"
        "## 시민 관점 이슈 렌즈\n\n- 핵심 모순: \n- 시민·소비자 이해관계: \n- 첫 훅 질문: \n"
        "- 시선 장치: \n- 적용 장면: \n- 선택 이유: \n\n"
        "## 지역·인물·책임 구체화\n\n- 핵심 지역명: \n- 중앙 인물: \n"
        "- 확인된 행위·누락: \n- 시민 피해·신뢰 훼손: \n- 근거 주장: \n\n"
        "## 집중 유지 설계\n\n- 오픈 루프: \n- 중간 재후킹: \n- 보상: \n"
        "- 마지막 붙잡기: \n- Typecast 전달: \n- 자연스러운 루프: \n\n"
        "## 스토리 연결\n\n- 훅이 여는 궁금증: \n- 중간 전환이 바꾸는 예상: \n- 결론이 회수하는 답: \n\n"
        "## 내레이션\n\n"
        "## 검증 메모\n\n",
        encoding="utf-8",
    )
    print(project_dir)
    return 0


def cmd_optimize_images(args: argparse.Namespace) -> int:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise News2ShortsError("Pillow가 필요합니다. doctor 결과를 확인하세요.") from exc

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"프로젝트 디렉터리를 찾을 수 없습니다: {project_dir}")
    project = load_json(project_dir / "project.json")
    manifest = load_json(project_dir / "rights-manifest.json")
    if not isinstance(project, dict) or not isinstance(manifest, dict):
        fail("project.json 또는 rights-manifest.json 형식이 잘못되었습니다.")

    visual_sourcing = project.get("visual_sourcing")
    configured_limit = generated_image_size_limit(visual_sourcing if isinstance(visual_sourcing, dict) else {})
    default_width, default_height = configured_limit or DEFAULT_GENERATED_IMAGE_SIZE
    max_width = args.max_width or default_width
    max_height = args.max_height or default_height
    if not 320 <= max_width <= 2160 or not 480 <= max_height <= 3840:
        fail("이미지 제한 크기가 허용 범위를 벗어났습니다.")

    results: list[dict] = []
    changed = False
    for asset in manifest.get("assets", []):
        if not isinstance(asset, dict) or str(asset.get("kind") or "") != "generated":
            continue
        relative = str(asset.get("path") or "").strip()
        if not relative or Path(relative).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        image_path = resolve_project_file(project_dir, relative)
        try:
            with Image.open(image_path) as opened:
                image = ImageOps.exif_transpose(opened)
                original_width, original_height = image.size
                resized = original_width > max_width or original_height > max_height
                if resized:
                    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    suffix = image_path.suffix.lower()
                    output_format = "JPEG" if suffix in {".jpg", ".jpeg"} else suffix.removeprefix(".").upper()
                    if output_format == "JPG":
                        output_format = "JPEG"
                    if output_format == "JPEG" and image.mode not in {"RGB", "L"}:
                        image = image.convert("RGB")
                    temp_path = image_path.with_name(f".{image_path.stem}.optimized{image_path.suffix}")
                    save_options = {"quality": 86, "optimize": True} if output_format in {"JPEG", "WEBP"} else {"optimize": True}
                    image.save(temp_path, format=output_format, **save_options)
                    temp_path.replace(image_path)
                    changed = True
                width, height = image.size
        except Exception as exc:
            raise News2ShortsError(f"생성 이미지를 최적화할 수 없습니다: {relative}: {exc}") from exc

        asset["width"] = width
        asset["height"] = height
        asset["optimized_at"] = iso_now()
        results.append(
            {
                "path": relative,
                "before": f"{original_width}x{original_height}",
                "after": f"{width}x{height}",
                "resized": resized,
            }
        )

    if results:
        write_json(project_dir / "rights-manifest.json", manifest)
    print(
        json.dumps(
            {
                "ok": True,
                "limit": f"{max_width}x{max_height}",
                "processed": len(results),
                "resized": sum(1 for item in results if item["resized"]),
                "files": results,
                "manifest_updated": bool(results),
                "pixels_changed": changed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def find_font() -> Path:
    for candidate in FONT_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise News2ShortsError("한글을 표시할 수 있는 폰트를 찾지 못했습니다.")


def load_font_face(font_path: Path, size: int, *, bold: bool = False):
    from PIL import ImageFont

    if bold and font_path.name == "AppleSDGothicNeo.ttc":
        return ImageFont.truetype(str(font_path), size=size, index=14)
    if bold:
        bold_candidates = [
            font_path.with_name("NotoSansKR-Bold.otf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]
        bold_path = next((candidate for candidate in bold_candidates if candidate.is_file()), None)
        if bold_path:
            return ImageFont.truetype(str(bold_path), size=size)
    return ImageFont.truetype(str(font_path), size=size)


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    words: list[str] = []
    for word in text.split(" "):
        if draw.textbbox((0, 0), word, font=font)[2] <= max_width:
            words.append(word)
            continue
        chunk = ""
        for char in word:
            trial = chunk + char
            if chunk and draw.textbbox((0, 0), trial, font=font)[2] > max_width:
                words.append(chunk)
                chunk = char
            else:
                chunk = trial
        if chunk:
            words.append(chunk)

    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if current and draw.textbbox((0, 0), trial, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def fitted_lines(
    draw,
    text: str,
    font_path: Path,
    max_width: int,
    max_lines: int,
    start_size: int,
    *,
    bold: bool = False,
):
    for size in range(start_size, 31, -2):
        font = load_font_face(font_path, size, bold=bold)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    font = load_font_face(font_path, 32, bold=bold)
    lines = wrap_text(draw, text, font, max_width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(". ") + "…"
    return font, lines


def fitted_balanced_lines(
    draw,
    text: str,
    font_path: Path,
    max_width: int,
    max_lines: int,
    start_size: int,
    *,
    bold: bool = False,
):
    """Fit a headline while avoiding a short orphan on the second line."""
    normalized = re.sub(r"\s+", " ", text.strip())
    words = normalized.split(" ") if normalized else []
    if max_lines != 2 or len(words) < 2:
        return fitted_lines(draw, normalized, font_path, max_width, max_lines, start_size, bold=bold)

    for size in range(start_size, 31, -2):
        font = load_font_face(font_path, size, bold=bold)
        if draw.textbbox((0, 0), normalized, font=font)[2] <= max_width:
            return font, [normalized]
        candidates: list[tuple[float, list[str]]] = []
        for split_at in range(1, len(words)):
            left = " ".join(words[:split_at])
            right = " ".join(words[split_at:])
            left_width = draw.textbbox((0, 0), left, font=font)[2]
            right_width = draw.textbbox((0, 0), right, font=font)[2]
            if left_width > max_width or right_width > max_width:
                continue
            shortest_characters = min(len(re.sub(r"\s+", "", left)), len(re.sub(r"\s+", "", right)))
            orphan_penalty = max(0, 3 - shortest_characters) * max_width
            candidates.append((orphan_penalty + abs(left_width - right_width), [left, right]))
        if candidates:
            return font, min(candidates, key=lambda item: item[0])[1]
    return fitted_lines(draw, normalized, font_path, max_width, max_lines, 32, bold=bold)


def draw_centered_lines(
    draw,
    lines: list[str],
    font,
    y: int,
    fill,
    spacing: int = 12,
    *,
    canvas_width: int = 1080,
) -> int:
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        width = box[2] - box[0]
        height = box[3] - box[1]
        draw.text(((canvas_width - width) / 2, y), line, font=font, fill=fill)
        y += height + spacing
    return y


def draw_centered_stroked_emphasized_lines(
    draw,
    lines: list[str],
    font,
    y: int,
    fill,
    accent,
    phrase: str,
    *,
    spacing: int = 18,
    stroke_width: int = 10,
) -> int:
    phrase = phrase.strip()
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        line_width = box[2] - box[0]
        line_height = box[3] - box[1]
        cursor = (1080 - line_width) / 2
        if phrase and phrase in line:
            before, highlighted, after = line.partition(phrase)
            for text, color in ((before, fill), (highlighted, accent), (after, fill)):
                if not text:
                    continue
                draw.text(
                    (cursor, y),
                    text,
                    font=font,
                    fill=color,
                    stroke_width=stroke_width,
                    stroke_fill="#050505",
                )
                text_box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
                cursor += text_box[2] - text_box[0]
        else:
            draw.text(
                (cursor, y),
                line,
                font=font,
                fill=fill,
                stroke_width=stroke_width,
                stroke_fill="#050505",
            )
        y += line_height + spacing
    return y


def render_classic_frame(
    scene: dict,
    project: dict,
    project_dir: Path,
    destination: Path,
    *,
    draft: bool,
) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageFont
    except ImportError as exc:
        raise News2ShortsError("Pillow가 필요합니다. doctor 결과를 확인하세요.") from exc

    width, height = 1080, 1920
    canvas = Image.new("RGB", (width, height), "#0C1423")
    draw = ImageDraw.Draw(canvas)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = (
            int(12 + 12 * ratio),
            int(20 + 10 * ratio),
            int(35 + 24 * ratio),
        )
        draw.line((0, y, width, y), fill=color)

    image_value = str(scene.get("image") or "").strip()
    if image_value:
        image_path = resolve_project_file(project_dir, image_value)
        try:
            source = ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
        except Exception as exc:
            raise News2ShortsError(f"이미지를 열 수 없습니다: {image_value}: {exc}") from exc
        background = ImageOps.fit(source, (width, height), method=Image.Resampling.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(radius=28))
        background = Image.blend(background, Image.new("RGB", (width, height), "#07101D"), 0.48)
        canvas.paste(background)
        foreground = ImageOps.contain(source, (960, 1050), method=Image.Resampling.LANCZOS)
        x = (width - foreground.width) // 2
        y = 380 + (900 - foreground.height) // 2
        card = Image.new("RGBA", (foreground.width + 20, foreground.height + 20), (255, 255, 255, 35))
        canvas.paste(card, (x - 10, y - 10), card)
        canvas.paste(foreground, (x, y))
    else:
        draw.rounded_rectangle((110, 430, 970, 1160), radius=48, fill="#16263D", outline="#2B4868", width=4)
        for index in range(6):
            offset = 520 + index * 92
            length = 480 + (index % 3) * 90
            draw.rounded_rectangle((190, offset, 190 + length, offset + 30), radius=15, fill="#294867")

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((0, 0, width, 430), fill=(5, 10, 18, 170))
    overlay_draw.rectangle((0, 1160, width, height), fill=(5, 10, 18, 205))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    font_path = find_font()
    small_font = ImageFont.truetype(str(font_path), size=34)
    draw.rounded_rectangle((70, 72, 350, 134), radius=22, fill="#DDEBFF")
    draw.text((96, 83), "NEWS2SHORTS", font=small_font, fill="#101B2B")

    headline = str(scene.get("headline") or project.get("title") or "이 결정, 시민에게 맞을까?")
    headline_font, headline_lines = fitted_lines(draw, headline, font_path, 940, 3, 82)
    draw_centered_lines(draw, headline_lines, headline_font, 168, "white", spacing=10)

    caption = str(scene.get("caption") or "").strip()
    if caption:
        caption_font, caption_lines = fitted_lines(draw, caption, font_path, 880, 3, 66)
        line_height = max(72, caption_font.size + 14)
        panel_height = max(190, 80 + len(caption_lines) * line_height)
        panel_top = 1290
        draw.rounded_rectangle(
            (70, panel_top, 1010, panel_top + panel_height),
            radius=38,
            fill="#F4F7FB",
        )
        draw_centered_lines(draw, caption_lines, caption_font, panel_top + 44, "#101827", spacing=12)

    credit = str(scene.get("credit") or "").strip()
    if credit:
        credit_lines = wrap_text(draw, credit, small_font, 900)[:2]
        draw_centered_lines(draw, credit_lines, small_font, 1750, "#D2DBE8", spacing=4)

    canvas.save(destination, format="PNG", optimize=True)


def visual_style_config(project: dict) -> dict:
    configured = project.get("visual_style")
    if isinstance(configured, str):
        return {"template": configured}
    if isinstance(configured, dict):
        return configured
    return {"template": "classic-card"}


def shorts_profile_config(project: dict) -> dict:
    configured = project.get("shorts_profile")
    return configured if isinstance(configured, dict) else {}


def narration_voice_config(project: dict) -> dict:
    configured = project.get("narration_voice")
    return configured if isinstance(configured, dict) else {"mode": "auto", "voice": ""}


def scene_audio_mode(scene: dict) -> str:
    return str(scene.get("audio_mode") or NARRATION_AUDIO_MODE).strip().lower()


def scene_uses_source_video_audio(scene: dict) -> bool:
    return scene_audio_mode(scene) == SOURCE_VIDEO_AUDIO_MODE


def narration_style_config(project: dict) -> str:
    return str(
        project.get("narration_style") or NARRATION_STYLE_STANDARD
    ).strip()


def uses_formal_narration_ending(value: str) -> bool:
    return bool(
        re.search(
            r"(?:합니다|입니다|됩니다|랍니다|습니다|합니까|입니까|됩니까)(?:[.!?…]+|$)",
            value,
        )
    )


def narration_ending_family(value: object) -> str:
    tokens = re.findall(r"[0-9A-Za-z가-힣]+", str(value or "").lower())
    if not tokens:
        return ""
    last = tokens[-1]
    if last.endswith(("는데", "인데")):
        return "de"
    if last == "함" or last.endswith(("다고함", "라고함")):
        return "ham"
    return ""


def validate_narration_style(project: dict, scenes: list[dict]) -> list[str]:
    errors: list[str] = []
    style = narration_style_config(project)
    if style not in NARRATION_STYLES:
        return [
            "project.json narration_style은 standard 또는 "
            "cc-helper-conversational이어야 합니다."
        ]
    if style != NARRATION_STYLE_CC_HELPER_CONVERSATIONAL:
        return errors
    if str(project.get("delivery_mode") or "").strip() == VISUAL_FIRST_MODE:
        return ["visual-first는 내레이션이 없어 cc-helper-conversational 말투를 사용할 수 없습니다."]

    narrated_endings: list[tuple[str, str, bool]] = []
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            continue
        narration = str(scene.get("narration") or "").strip()
        if not narration:
            continue
        scene_id = str(scene.get("id") or f"scene-{index:02d}")
        if scene_uses_source_video_audio(scene):
            narrated_endings.append((scene_id, "", False))
            continue
        if uses_formal_narration_ending(narration):
            errors.append(
                f"{scene_id} cc-helper-conversational은 친구 설명형 구어체여야 하며 "
                "합니다/했습니다 종결을 사용할 수 없습니다."
            )
        narrated_endings.append((scene_id, narration_ending_family(narration), True))

    for left, right in zip(narrated_endings, narrated_endings[1:]):
        if left[2] and right[2] and left[1] == right[1] == "de":
            errors.append(
                f"{left[0]}/{right[0]}에 "
                "~데/~는데 종결을 연속 사용할 수 없습니다."
            )
    if (
        len(narrated_endings) >= 2
        and all(item[2] for item in narrated_endings[-2:])
        and [item[1] for item in narrated_endings[-2:]] == ["ham", "ham"]
    ):
        errors.append("cc-helper-conversational은 마지막 두 장면을 ~함 종결로 연속할 수 없습니다.")
    return errors


def scene_external_caption_enabled(scene: dict) -> bool:
    return scene.get("external_caption") is not False


def scene_text_overlay_enabled(scene: dict) -> bool:
    return scene.get("render_text_overlay") is not False


def normalize_source_dialogue(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", str(value or "")).lower()


def source_dialogue_match(expected: object, actual: object) -> dict:
    expected_text = normalize_source_dialogue(expected)
    actual_text = normalize_source_dialogue(actual)
    if not expected_text or not actual_text:
        return {
            "similarity": 0.0,
            "expected_coverage": 0.0,
            "passed": False,
        }
    matcher = SequenceMatcher(None, expected_text, actual_text)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    similarity = matcher.ratio()
    coverage = matched / len(expected_text)
    return {
        "similarity": round(similarity, 4),
        "expected_coverage": round(coverage, 4),
        "passed": bool(
            similarity >= SOURCE_TRANSCRIPT_MATCH_THRESHOLD
            and coverage >= SOURCE_TRANSCRIPT_COVERAGE_THRESHOLD
        ),
    }


def source_transcription_backends() -> dict:
    whisper = shutil.which("whisper")
    return {
        "transcript-file": True,
        "openai-whisper-cli": whisper,
        "automatic_available": bool(whisper),
    }


def transcript_segments(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    segments: list[dict] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        try:
            start = max(0.0, float(item.get("start") or 0.0))
            end = max(start, float(item.get("end") or start))
        except (TypeError, ValueError):
            continue
        text = str(item.get("text") or "").strip()
        if text:
            segments.append({"start": round(start, 3), "end": round(end, 3), "text": text})
    return segments


def transcript_record(value: object) -> dict:
    if isinstance(value, str):
        return {"text": value.strip(), "segments": []}
    if not isinstance(value, dict):
        return {"text": "", "segments": []}
    segments = transcript_segments(value.get("segments"))
    text = str(value.get("text") or value.get("transcript") or "").strip()
    if not text and segments:
        text = " ".join(segment["text"] for segment in segments).strip()
    return {"text": text, "segments": segments}


def load_source_transcript_records(path: Path, scene_ids: list[str]) -> dict[str, dict]:
    if path.suffix.lower() != ".json":
        if len(scene_ids) != 1:
            raise News2ShortsError(
                "일반 텍스트 전사 파일은 source-video 장면 하나를 선택했을 때만 사용할 수 있습니다."
            )
        return {scene_ids[0]: transcript_record(path.read_text(encoding="utf-8"))}
    value = load_json(path)
    if isinstance(value, dict) and isinstance(value.get("scenes"), list):
        records: dict[str, dict] = {}
        for item in value["scenes"]:
            if not isinstance(item, dict):
                continue
            scene_id = str(item.get("scene_id") or item.get("id") or "").strip()
            if scene_id:
                records[scene_id] = transcript_record(item)
        return records
    if isinstance(value, dict) and isinstance(value.get("scenes"), dict):
        return {
            str(scene_id): transcript_record(record)
            for scene_id, record in value["scenes"].items()
        }
    if isinstance(value, dict) and ("text" in value or "segments" in value):
        if len(scene_ids) != 1:
            raise News2ShortsError(
                "단일 Whisper JSON은 source-video 장면 하나를 선택했을 때만 사용할 수 있습니다."
            )
        return {scene_ids[0]: transcript_record(value)}
    if isinstance(value, dict):
        return {str(scene_id): transcript_record(record) for scene_id, record in value.items()}
    raise News2ShortsError("지원하지 않는 전사 파일 형식입니다.")


def run_whisper_source_transcription(
    audio_path: Path,
    *,
    output_dir: Path,
    language: str,
    model: str,
    model_dir: Path,
    allow_model_download: bool,
) -> dict:
    whisper = shutil.which("whisper")
    if not whisper:
        raise News2ShortsError(
            "자동 전사 백엔드가 없습니다. 로컬 OpenAI Whisper CLI를 준비하거나 "
            "--transcript-file로 검토된 UTF-8 전사를 제공하세요."
        )
    model_path = model_dir / f"{model}.pt"
    if not model_path.is_file() and not allow_model_download:
        raise News2ShortsError(
            f"로컬 Whisper 모델이 없습니다: {model_path}. "
            "모델 다운로드를 허용하려면 --allow-model-download를 명시하세요."
        )
    model_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            whisper,
            str(audio_path),
            "--language",
            language,
            "--task",
            "transcribe",
            "--model",
            model,
            "--model_dir",
            str(model_dir),
            "--word_timestamps",
            "True",
            "--output_format",
            "json",
            "--output_dir",
            str(output_dir),
        ]
    )
    output_path = output_dir / f"{audio_path.stem}.json"
    if not output_path.is_file():
        raise News2ShortsError(f"Whisper 전사 결과가 생성되지 않았습니다: {output_path}")
    return transcript_record(load_json(output_path))


def build_source_audio_scene_review(
    scene: dict,
    *,
    source_path: str,
    source_sha256: str,
    transcript: dict,
    timing_confirmed: bool,
) -> dict:
    scene_id = str(scene.get("id") or "").strip()
    expected_text = str(scene.get("narration") or "").strip()
    actual_text = str(transcript.get("text") or "").strip()
    segments = transcript_segments(transcript.get("segments"))
    duration = max(0.0, float(scene.get("duration") or 0.0))
    video_start = max(0.0, float(scene.get("video_start") or 0.0))
    match = source_dialogue_match(expected_text, actual_text)
    first_spoken_at = segments[0]["start"] if segments else None
    last_spoken_at = segments[-1]["end"] if segments else None
    leading_margin = round(first_spoken_at, 3) if first_spoken_at is not None else None
    trailing_margin = (
        round(max(0.0, duration - last_spoken_at), 3)
        if last_spoken_at is not None
        else None
    )
    edge_cut_risk = bool(
        segments
        and (
            leading_margin < SOURCE_AUDIO_EDGE_MARGIN_SECONDS
            or trailing_margin < SOURCE_AUDIO_EDGE_MARGIN_SECONDS
        )
    )
    reasons: list[str] = []
    if not expected_text:
        reasons.append("source-video 장면의 예상 대사인 narration이 비어 있습니다.")
    if not actual_text:
        reasons.append("전사된 발화가 없습니다.")
    elif not match["passed"]:
        reasons.append("전사 결과가 storyboard narration의 예상 대사를 충분히 포함하지 않습니다.")
    if edge_cut_risk:
        reasons.append("첫 발화 또는 마지막 발화가 컷 경계 0.15초 안에 있어 잘릴 위험이 있습니다.")
    timing_available = bool(segments)
    if not timing_available and not timing_confirmed:
        reasons.append("발화 시간 정보가 없어 컷 경계를 확인하지 못했습니다.")
    status = "passed"
    if not expected_text or not actual_text or not match["passed"] or edge_cut_risk:
        status = "mismatch"
    elif not timing_available and not timing_confirmed:
        status = "review_required"
    return {
        "scene_id": scene_id,
        "source_path": source_path,
        "source_sha256": source_sha256,
        "video_start": round(video_start, 3),
        "duration": round(duration, 3),
        "expected_text": expected_text,
        "transcript_text": actual_text,
        "segments": segments,
        "match": match,
        "timing_available": timing_available,
        "timing_confirmed": bool(timing_confirmed),
        "leading_margin_seconds": leading_margin,
        "trailing_margin_seconds": trailing_margin,
        "edge_cut_risk": edge_cut_risk,
        "status": status,
        "reasons": reasons,
    }


def validate_source_audio_review(
    project_dir: Path,
    scenes: list[dict],
    *,
    final: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    source_scenes = [scene for scene in scenes if scene_uses_source_video_audio(scene)]
    if not source_scenes:
        return errors, warnings
    target = errors if final else warnings
    review_path = project_dir / SOURCE_AUDIO_REVIEW_FILENAME
    if not review_path.is_file():
        target.append(
            f"source-video 장면의 음성 전사 검토가 없습니다: {SOURCE_AUDIO_REVIEW_FILENAME}. "
            "review-source-audio를 먼저 실행하세요."
        )
        return errors, warnings
    try:
        review = load_json(review_path)
    except News2ShortsError as exc:
        target.append(str(exc))
        return errors, warnings
    if not isinstance(review, dict):
        target.append(f"지원하지 않는 source audio review 형식입니다: {SOURCE_AUDIO_REVIEW_FILENAME}")
        return errors, warnings
    try:
        review_version = int(review.get("version") or 0)
    except (TypeError, ValueError):
        review_version = 0
    if review_version != SOURCE_AUDIO_REVIEW_VERSION:
        target.append(f"지원하지 않는 source audio review 형식입니다: {SOURCE_AUDIO_REVIEW_FILENAME}")
        return errors, warnings
    raw_reviews = review.get("scenes")
    if not isinstance(raw_reviews, list):
        target.append(f"{SOURCE_AUDIO_REVIEW_FILENAME}의 scenes는 배열이어야 합니다.")
        return errors, warnings
    by_scene_id = {
        str(item.get("scene_id") or "").strip(): item
        for item in raw_reviews
        if isinstance(item, dict) and str(item.get("scene_id") or "").strip()
    }
    for index, scene in enumerate(source_scenes, start=1):
        scene_id = str(scene.get("id") or f"source-scene-{index:02d}").strip()
        item = by_scene_id.get(scene_id)
        if item is None:
            target.append(f"source-video 장면의 음성 전사 검토가 누락됐습니다: {scene_id}")
            continue
        source_value = str(scene.get("video") or "").strip()
        if str(item.get("source_path") or "").strip() != source_value:
            target.append(f"source-video 음성 검토의 자산 경로가 변경됐습니다: {scene_id}")
            continue
        try:
            source_path = resolve_project_file(project_dir, source_value)
            source_hash = file_sha256(source_path)
        except News2ShortsError as exc:
            target.append(str(exc))
            continue
        if str(item.get("source_sha256") or "") != source_hash:
            target.append(f"source-video 음성 검토 후 영상 파일이 변경됐습니다: {scene_id}")
        try:
            current_start = round(max(0.0, float(scene.get("video_start") or 0.0)), 3)
            current_duration = round(max(0.0, float(scene.get("duration") or 0.0)), 3)
            reviewed_start = round(float(item.get("video_start") or 0.0), 3)
            reviewed_duration = round(float(item.get("duration") or 0.0), 3)
        except (TypeError, ValueError):
            target.append(f"source-video 음성 검토의 컷 시간이 잘못됐습니다: {scene_id}")
            continue
        if current_start != reviewed_start or current_duration != reviewed_duration:
            target.append(f"source-video 음성 검토 후 컷 시작점 또는 길이가 변경됐습니다: {scene_id}")
        if normalize_source_dialogue(item.get("expected_text")) != normalize_source_dialogue(
            scene.get("narration")
        ):
            target.append(f"source-video 음성 검토 후 예상 대사가 변경됐습니다: {scene_id}")
        status = str(item.get("status") or "").strip()
        if status != "passed":
            reasons = item.get("reasons") if isinstance(item.get("reasons"), list) else []
            reason_text = "; ".join(str(reason) for reason in reasons if str(reason).strip())
            suffix = f": {reason_text}" if reason_text else ""
            target.append(f"source-video 음성 전사 검토 미통과: {scene_id}{suffix}")
    return errors, warnings


def brand_intro_config(project: dict) -> dict:
    configured = project.get("brand_intro")
    try:
        project_version = int(project.get("version") or 1)
    except (TypeError, ValueError):
        project_version = 1
    result = {
        "enabled": True,
        "mode": BRAND_MODE_CORNER_LOGO if project_version >= 16 else BRAND_MODE_LEGACY_FULL,
        "asset": BRAND_INTRO_ASSET_ID,
        "position": "top-left",
        "transition": DEFAULT_BRAND_INTRO_TRANSITION,
        "transition_duration": DEFAULT_BRAND_INTRO_TRANSITION_DURATION,
    }
    if isinstance(configured, dict):
        result.update(configured)
    return result


def brand_intro_asset_path(asset_id: str) -> Path | None:
    return BRAND_INTRO_ASSET_PATHS.get(asset_id.strip())


def brand_intro_lead_in_seconds(project: dict) -> float:
    config = brand_intro_config(project)
    if config.get("enabled") is not True:
        return 0.0
    if str(config.get("mode") or BRAND_MODE_LEGACY_FULL).strip() == BRAND_MODE_CORNER_LOGO:
        return 0.0
    try:
        transition_duration = float(
            config.get("transition_duration") or DEFAULT_BRAND_INTRO_TRANSITION_DURATION
        )
    except (TypeError, ValueError):
        transition_duration = DEFAULT_BRAND_INTRO_TRANSITION_DURATION
    return max(0.0, BRAND_INTRO_SOURCE_DURATION_SECONDS - transition_duration)


def audio_bed_config(project: dict) -> dict:
    configured = project.get("audio_bed")
    return configured if isinstance(configured, dict) else {
        "enabled": False,
        "mode": "none",
        "profile": "",
        "vocals": False,
        "path": "",
    }


def requested_scene_start_seconds(scenes: list[dict], scene_id: str) -> float | None:
    elapsed = 0.0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        if str(scene.get("id") or "").strip() == scene_id:
            return elapsed
        try:
            elapsed += max(CONTINUOUS_FLOW_MIN_SCENE_SECONDS, float(scene.get("duration") or 0.0))
        except (TypeError, ValueError):
            elapsed += CONTINUOUS_FLOW_MIN_SCENE_SECONDS
    return None


def retention_timing_report(project: dict, scene_reports: list[dict]) -> dict:
    try:
        project_version = int(project.get("version") or 1)
    except (TypeError, ValueError):
        project_version = 1
    if project_version < 16:
        return {
            "not_applicable": True,
            "reason": "project-version-before-16",
            "passed": True,
        }
    profile = shorts_profile_config(project)
    delivery_mode = str(project.get("delivery_mode") or CONTINUOUS_FLOW_MODE).strip()
    deadlines = {
        "first_answer": (
            VISUAL_FIRST_ANSWER_DEADLINE_SECONDS
            if delivery_mode == VISUAL_FIRST_MODE
            else CONTINUOUS_FLOW_ANSWER_DEADLINE_SECONDS
        ),
        "truth_guard": TRUTH_GUARD_DEADLINE_SECONDS,
    }
    report_by_id = {
        str(item.get("id") or "").strip(): item
        for item in scene_reports
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    lead_in = brand_intro_lead_in_seconds(project)
    events: dict[str, dict] = {}
    for event, field in (
        ("first_answer", "first_answer_scene_id"),
        ("truth_guard", "truth_guard_scene_id"),
    ):
        scene_id = str(profile.get(field) or "").strip()
        scene_report = report_by_id.get(scene_id)
        if not scene_id or scene_report is None:
            events[event] = {
                "scene_id": scene_id,
                "actual_start": None,
                "deadline": deadlines[event],
                "passed": False,
            }
            continue
        raw_start = scene_report.get("timeline_start")
        try:
            actual_start = lead_in + float(raw_start)
        except (TypeError, ValueError):
            actual_start = None
        events[event] = {
            "scene_id": scene_id,
            "actual_start": round(actual_start, 3) if actual_start is not None else None,
            "deadline": deadlines[event],
            "passed": bool(actual_start is not None and actual_start <= deadlines[event]),
        }
    truth_guard_required = bool(str(profile.get("truth_guard") or "").strip())
    if not truth_guard_required:
        events["truth_guard"]["passed"] = True
        events["truth_guard"]["not_applicable"] = True
    return {
        "delivery_mode": delivery_mode,
        "brand_lead_in_seconds": round(lead_in, 3),
        "events": events,
        "passed": bool(
            events["first_answer"]["passed"] and events["truth_guard"]["passed"]
        ),
    }


def narration_character_count(value: object) -> int:
    return len(re.sub(r"\s+", "", str(value or "")))


def estimated_render_duration(scenes: list[dict]) -> float:
    total = 0.0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        try:
            requested = max(1.0, float(scene.get("duration") or 0.0))
        except (TypeError, ValueError):
            requested = 1.0
        narration = str(scene.get("narration") or "").strip()
        if not narration or str(scene.get("audio") or "").strip():
            total += requested
            continue
        estimated_audio = narration_character_count(narration) / TYPECAST_ESTIMATED_CHARS_PER_SECOND
        total += max(requested, estimated_audio + TYPECAST_SCENE_TAIL_SECONDS)
    return total


def render_timing_issues(
    project: dict,
    scene_reports: list[dict],
    *,
    final: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        target_duration = float(project.get("target_duration_seconds") or 0.0)
    except (TypeError, ValueError):
        target_duration = 0.0
    rendered_total = sum(max(0.0, float(item.get("rendered_duration") or 0.0)) for item in scene_reports)
    if target_duration > 0 and rendered_total > target_duration * TARGET_DURATION_WARNING_RATIO:
        message = (
            "실제 렌더 길이가 목표를 초과합니다: "
            f"{rendered_total:.1f}/{target_duration:.1f}초"
        )
        if final and rendered_total > target_duration * TARGET_DURATION_ERROR_RATIO:
            errors.append(message)
        else:
            warnings.append(message)
    try:
        project_version = int(project.get("version") or 1)
    except (TypeError, ValueError):
        project_version = 1
    if project_version >= 13:
        early_rehook_scene_id = str(
            shorts_profile_config(project).get("early_rehook_scene_id") or ""
        ).strip()
        early_report = next(
            (
                item
                for item in scene_reports
                if str(item.get("id") or "").strip() == early_rehook_scene_id
            ),
            None,
        )
        if early_report is not None and early_report.get("flow_cue_start") is not None:
            absolute_start = brand_intro_lead_in_seconds(project) + float(
                early_report.get("flow_cue_start") or 0.0
            )
            if absolute_start > EARLY_RETENTION_DEADLINE_SECONDS:
                message = (
                    "Typecast 적용 후 재후킹 시작이 인트로 포함 10초를 넘습니다: "
                    f"{absolute_start:.1f}/{EARLY_RETENTION_DEADLINE_SECONDS:.1f}초"
                )
                (errors if final else warnings).append(message)
    if project_version >= 16:
        timing = retention_timing_report(project, scene_reports)
        for event_name, label in (("first_answer", "첫 답변"), ("truth_guard", "사실 조건")):
            event = timing["events"][event_name]
            if event.get("not_applicable") is True or event.get("passed") is True:
                continue
            actual_start = event.get("actual_start")
            deadline = float(event.get("deadline") or 0.0)
            message = (
                f"{label} 장면이 실제 유지율 기준을 넘습니다: "
                f"{actual_start if actual_start is not None else 'unknown'}/{deadline:.1f}초"
            )
            (errors if final else warnings).append(message)
    for item in scene_reports:
        scene_id = str(item.get("id") or "unknown")
        beat = str(item.get("beat") or "")
        try:
            rendered_duration = float(item.get("rendered_duration") or 0.0)
        except (TypeError, ValueError):
            continue
        warning_limit = PAYOFF_SCENE_WARNING_SECONDS if beat == "payoff" else ORDINARY_SCENE_WARNING_SECONDS
        error_limit = PAYOFF_SCENE_ERROR_SECONDS if beat == "payoff" else ORDINARY_SCENE_ERROR_SECONDS
        if rendered_duration > warning_limit:
            message = (
                "Typecast 적용 후 장면이 길어졌습니다: "
                f"{scene_id}: {rendered_duration:.1f}/{warning_limit:.1f}초"
            )
            if final and rendered_duration > error_limit:
                errors.append(message)
            else:
                warnings.append(message)
    return errors, warnings


def resolve_typecast_voice(value: str) -> tuple[str, dict]:
    normalized = value.strip().lower()
    normalized = TYPECAST_VOICE_ALIASES.get(normalized, normalized)
    for key, candidate in TYPECAST_VOICE_CANDIDATES.items():
        if normalized in {
            key,
            str(candidate["voice_id"]).lower(),
            str(candidate["voice_name"]).lower(),
        }:
            return key, candidate
    allowed = ", ".join(candidate["voice_name"] for candidate in TYPECAST_VOICE_CANDIDATES.values())
    raise News2ShortsError(f"지원하지 않는 Typecast 보이스입니다: {value}. 사용 가능: auto, {allowed}")


def select_stable_default_voice(project: dict) -> tuple[str, int]:
    seed = "\x1f".join(
        str(project.get(field) or "")
        for field in ("slug", "source_url", "created_at", "title")
    )
    bucket = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % len(
        TYPECAST_DEFAULT_VOICE_BUCKETS
    )
    return TYPECAST_DEFAULT_VOICE_BUCKETS[bucket], bucket


def select_typecast_voice(project: dict, storyboard: dict, requested: str | None = None) -> dict:
    configured = narration_voice_config(project)
    mode = str(configured.get("mode") or "auto").strip().lower()
    configured_voice = str(configured.get("voice") or "").strip()
    choice = str(requested or "").strip()
    if not choice:
        choice = configured_voice if mode == "manual" else "auto"

    if choice.lower() != "auto":
        key, candidate = resolve_typecast_voice(choice)
        return {
            "mode": "manual",
            "key": key,
            **candidate,
            "selection_strategy": "manual-override",
            "popularity_basis": TYPECAST_VOICE_POPULARITY_BASIS,
            "popularity_source": TYPECAST_VOICE_POPULARITY_SOURCE,
            "reason": "프로젝트 설정 또는 --typecast-voice로 보이스를 고정했습니다.",
        }

    style_template = str(visual_style_config(project).get("template") or "classic-card")
    scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []
    planned_duration = sum(
        max(0.0, float(scene.get("duration") or 0.0))
        for scene in scenes
        if isinstance(scene, dict)
    )
    target_duration = max(float(project.get("target_duration_seconds") or 0.0), planned_duration)
    valid_scenes = [scene for scene in scenes if isinstance(scene, dict)]
    guide_scene_count = sum(
        1
        for scene in valid_scenes
        if any(keyword in str(scene.get("narration") or "") for keyword in TYPECAST_GUIDE_KEYWORDS)
    )
    guide_scene_ratio = guide_scene_count / len(valid_scenes) if valid_scenes else 0.0

    distribution_metadata: dict[str, str | int] = {}
    if project.get("sensitive_topic") is True:
        key = "seohyeon"
        reason = "공식 인기 후보 중 민감 뉴스의 정확한 전달에 맞는 뉴스형 보이스를 선택했습니다."
    elif guide_scene_ratio >= 0.5:
        key = "moonjung"
        reason = "공식 인기 후보 중 사용법·대처·절차 비중이 높은 내용에 맞는 설명형 보이스를 선택했습니다."
    elif style_template == "story-explainer" and target_duration >= 55:
        key = "kangil"
        reason = "공식 인기 후보 중 55초 이상 스토리 설명에 맞는 장문 몰입형 보이스를 선택했습니다."
    else:
        key, bucket = select_stable_default_voice(project)
        selected_name = TYPECAST_VOICE_CANDIDATES[key]["voice_name"]
        reason = (
            "민감 뉴스·절차 안내·장문 설명 전용 규칙에 해당하지 않아 "
            f"프로젝트 고정 8:2 기본 분포에서 {selected_name}를 선택했습니다."
        )
        distribution_metadata = {
            "distribution": TYPECAST_DEFAULT_VOICE_DISTRIBUTION,
            "distribution_basis": TYPECAST_DEFAULT_VOICE_DISTRIBUTION_BASIS,
            "distribution_bucket": bucket,
        }

    return {
        "mode": "auto",
        "key": key,
        **TYPECAST_VOICE_CANDIDATES[key],
        "selection_strategy": TYPECAST_VOICE_SELECTION_STRATEGY,
        "popularity_basis": TYPECAST_VOICE_POPULARITY_BASIS,
        "popularity_source": TYPECAST_VOICE_POPULARITY_SOURCE,
        "reason": reason,
        **distribution_metadata,
    }


def draw_left_lines(draw, lines: list[str], font, x: int, y: int, fill, spacing: int = 10) -> int:
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        height = box[3] - box[1]
        draw.text((x, y), line, font=font, fill=fill)
        y += height + spacing
    return y


def draw_emphasized_lines(draw, lines: list[str], font, x: int, y: int, fill, accent, phrase: str) -> int:
    phrase = phrase.strip()
    phrase_fits_line = bool(phrase and any(phrase in line for line in lines))
    for index, line in enumerate(lines):
        box = draw.textbbox((0, 0), line, font=font)
        height = box[3] - box[1]
        if phrase and phrase in line:
            before, highlighted, after = line.partition(phrase)
            cursor = x
            for text, color in ((before, fill), (highlighted, accent), (after, fill)):
                if not text:
                    continue
                draw.text((cursor, y), text, font=font, fill=color)
                text_box = draw.textbbox((0, 0), text, font=font)
                cursor += text_box[2] - text_box[0]
        elif phrase and not phrase_fits_line and index == len(lines) - 1:
            draw.text((x, y), line, font=font, fill=accent)
        else:
            draw.text((x, y), line, font=font, fill=fill)
        y += height + 10
    return y


def draw_centered_emphasized_lines(
    draw,
    lines: list[str],
    font,
    y: int,
    fill,
    accent,
    phrase: str,
    *,
    spacing: int = 14,
) -> int:
    phrase = phrase.strip()
    phrase_fits_line = bool(phrase and any(phrase in line for line in lines))
    for index, line in enumerate(lines):
        box = draw.textbbox((0, 0), line, font=font, stroke_width=1)
        line_width = box[2] - box[0]
        line_height = box[3] - box[1]
        x = (1080 - line_width) / 2
        if phrase and phrase in line:
            before, highlighted, after = line.partition(phrase)
            cursor = x
            for text, color in ((before, fill), (highlighted, accent), (after, fill)):
                if not text:
                    continue
                draw.text((cursor, y), text, font=font, fill=color, stroke_width=1, stroke_fill="#050505")
                text_box = draw.textbbox((0, 0), text, font=font, stroke_width=1)
                cursor += text_box[2] - text_box[0]
        else:
            color = accent if phrase and not phrase_fits_line and index == len(lines) - 1 else fill
            draw.text((x, y), line, font=font, fill=color, stroke_width=1, stroke_fill="#050505")
        y += line_height + spacing
    return y


def draw_fact_stack_evidence_overlay(draw, scene: dict, style: dict, font_path: Path, accent: str) -> bool:
    if str(style.get("template") or "") != "fact-stack":
        return False
    if str(scene.get("beat") or "") not in FACT_STACK_PROOF_BEATS:
        return False

    fact_index = str(scene.get("fact_index") or scene.get("progress") or "").strip()
    if fact_index and style.get("show_fact_stack_index") is True:
        index_text = f"FACT {fact_index}"
        index_font = load_font_face(font_path, 31, bold=True)
        index_box = draw.textbbox((0, 0), index_text, font=index_font)
        index_width = index_box[2] - index_box[0]
        draw.rounded_rectangle((48, 500, 92 + index_width, 562), radius=18, fill=(3, 3, 3, 220))
        draw.text((70, 512), index_text, font=index_font, fill=accent)

    evidence_label = str(scene.get("evidence_label") or scene.get("eyebrow") or "").strip()
    caption = str(scene.get("caption") or "").strip()
    evidence_value = str(scene.get("evidence_value") or caption).strip()
    if not evidence_label and not evidence_value:
        return False
    panel_top, panel_bottom = 1290, 1668
    draw.rounded_rectangle(
        (48, panel_top, 1032, panel_bottom),
        radius=32,
        fill=(3, 5, 7, 232),
        outline=(255, 255, 255, 45),
        width=2,
    )

    current_y = panel_top + 38
    if evidence_label:
        label_font, label_lines = fitted_lines(draw, evidence_label, font_path, 850, 1, 42, bold=True)
        current_y = draw_centered_lines(draw, label_lines, label_font, current_y, "#F2F4F7", spacing=8) + 10

    if evidence_value:
        value_font, value_lines = fitted_lines(draw, evidence_value, font_path, 880, 2, 94, bold=True)
        current_y = draw_centered_lines(draw, value_lines, value_font, current_y, accent, spacing=8)

    normalized_caption = re.sub(r"\s+", "", caption)
    normalized_label = re.sub(r"\s+", "", evidence_label)
    normalized_value = re.sub(r"\s+", "", evidence_value)
    if caption and normalized_caption not in {normalized_label, normalized_value}:
        caption_font, caption_lines = fitted_lines(draw, caption, font_path, 850, 1, 40, bold=True)
        caption_y = min(current_y + 10, panel_bottom - 58)
        caption_focus = str(scene.get("caption_focus") or "").strip()
        if caption_focus:
            draw_centered_emphasized_lines(
                draw,
                caption_lines,
                caption_font,
                caption_y,
                "#D7DCE3",
                accent,
                caption_focus,
                spacing=8,
            )
        else:
            draw_centered_lines(draw, caption_lines, caption_font, caption_y, "#D7DCE3")
    return True


def render_broadcast_frame(
    scene: dict,
    project: dict,
    project_dir: Path,
    destination: Path,
    *,
    draft: bool,
) -> None:
    try:
        from PIL import Image, ImageDraw, ImageOps, ImageFont
    except ImportError as exc:
        raise News2ShortsError("Pillow가 필요합니다. doctor 결과를 확인하세요.") from exc

    width, height = 1080, 1920
    style = visual_style_config(project)
    brand = str(style.get("brand_name") or "NEWS2SHORTS").strip()[:24]
    accent = str(style.get("accent_color") or "#43E6A3")
    canvas = Image.new("RGB", (width, height), "#080A0E")
    draw = ImageDraw.Draw(canvas)
    font_path = find_font()

    image_top, image_bottom = 510, 1370
    image_value = str(scene.get("image") or "").strip()
    if image_value:
        image_path = resolve_project_file(project_dir, image_value)
        try:
            source = ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
        except Exception as exc:
            raise News2ShortsError(f"이미지를 열 수 없습니다: {image_value}: {exc}") from exc
        visual = ImageOps.fit(
            source,
            (width, image_bottom - image_top),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.48),
        )
        canvas.paste(visual, (0, image_top))
    else:
        draw.rectangle((0, image_top, width, image_bottom), fill="#17212E")
        for index in range(6):
            offset = 650 + index * 92
            draw.rounded_rectangle((135, offset, 735 + (index % 2) * 110, offset + 30), radius=15, fill="#2A3E55")

    brand_font = ImageFont.truetype(str(font_path), size=39)
    small_font = ImageFont.truetype(str(font_path), size=30)
    draw.rounded_rectangle((62, 58, 91, 105), radius=6, fill=accent)
    draw.text((111, 59), brand, font=brand_font, fill="white")

    eyebrow = str(scene.get("eyebrow") or "").strip()
    if eyebrow:
        eyebrow_font, eyebrow_lines = fitted_lines(draw, eyebrow, font_path, 875, 2, 34)
        draw_left_lines(draw, eyebrow_lines, eyebrow_font, 70, 145, "#D5D9E0", spacing=6)

    headline = str(
        style.get("display_headline")
        or scene.get("headline")
        or project.get("title")
        or "이 결정, 시민에게 맞을까?"
    ).strip()
    emphasis = str(scene.get("headline_highlight") or style.get("headline_highlight") or "")
    headline_font, headline_lines = fitted_lines(draw, headline, font_path, 930, 3, 76)
    draw_emphasized_lines(draw, headline_lines, headline_font, 70, 260, "white", accent, emphasis)

    ticker = str(scene.get("ticker") or scene.get("caption") or "").strip()
    ticker_top, ticker_bottom = 1250, 1425
    draw.rectangle((0, ticker_top, width, ticker_bottom), fill="#F6F7F9")
    draw.rectangle((0, ticker_top, 150, ticker_bottom), fill="#132E57")
    ticker_brand_font = ImageFont.truetype(str(font_path), size=28)
    brand_lines = wrap_text(draw, brand, ticker_brand_font, 112)[:2]
    brand_y = ticker_top + 49
    for line in brand_lines:
        box = draw.textbbox((0, 0), line, font=ticker_brand_font)
        line_width = box[2] - box[0]
        line_height = box[3] - box[1]
        draw.text(((150 - line_width) / 2, brand_y), line, font=ticker_brand_font, fill="white")
        brand_y += line_height + 2
    if ticker:
        ticker_font, ticker_lines = fitted_lines(draw, ticker, font_path, 820, 2, 49)
        draw_left_lines(draw, ticker_lines, ticker_font, 178, ticker_top + 34, "#10264B", spacing=8)

    draw.rectangle((0, ticker_bottom, width, height), fill="#080A0E")
    cue_font = ImageFont.truetype(str(font_path), size=36)
    draw.text((70, 1510), "핵심만 60초", font=cue_font, fill="#F1F3F6")
    draw.rounded_rectangle((70, 1566, 275, 1573), radius=3, fill=accent)

    credit = str(scene.get("credit") or "").strip()
    if credit:
        credit_lines = wrap_text(draw, credit, small_font, 760)[:2]
        draw_left_lines(draw, credit_lines, small_font, 70, 1735, "#B8C0CC", spacing=5)

    footer_font = ImageFont.truetype(str(font_path), size=56)
    footer_box = draw.textbbox((0, 0), brand, font=footer_font)
    footer_width = footer_box[2] - footer_box[0]
    draw.text((width - footer_width - 68, 1610), brand, font=footer_font, fill="#F0F2F5")

    canvas.save(destination, format="PNG", optimize=True)


def build_retention_overlay(scene: dict, project: dict, *, draft: bool):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise News2ShortsError("Pillow가 필요합니다. doctor 결과를 확인하세요.") from exc

    width, height = 1080, 1920
    style = visual_style_config(project)
    template = str(style.get("template") or "")
    accent = str(style.get("accent_color") or "#FFF200")
    font_path = find_font()
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # All new retention formats share this reference-derived composition: a
    # fixed, two-line promise above evidence that changes scene by scene.
    draw.rectangle((0, 0, width, 470), fill=(3, 3, 3, 245))

    small_font = ImageFont.truetype(str(font_path), size=27)

    persistent = str(style.get("display_headline") or "").strip()
    headline = str(persistent or project.get("title") or "이 결정, 시민에게 맞을까?").strip()
    emphasis = str(style.get("headline_highlight") or "")
    headline_font, headline_lines = fitted_balanced_lines(
        draw,
        headline,
        font_path,
        950,
        2,
        118,
        bold=True,
    )
    headline_heights = [
        draw.textbbox((0, 0), line, font=headline_font, stroke_width=1)[3]
        - draw.textbbox((0, 0), line, font=headline_font, stroke_width=1)[1]
        for line in headline_lines
    ]
    headline_block_height = sum(headline_heights) + max(0, len(headline_lines) - 1) * 14
    headline_y = max(54, int((470 - headline_block_height) / 2) - 4)
    draw_centered_emphasized_lines(
        draw,
        headline_lines,
        headline_font,
        headline_y,
        "white",
        accent,
        emphasis,
    )

    caption = str(scene.get("caption") or scene.get("ticker") or "").strip()
    fact_stack_caption_handled = draw_fact_stack_evidence_overlay(draw, scene, style, font_path, accent)
    is_payoff = str(scene.get("beat") or "").strip() == "payoff"
    show_payoff = is_payoff and style.get("show_payoff_label") is True
    payoff_panel_style = str(style.get("payoff_panel_style") or "").strip()
    if show_payoff and payoff_panel_style == "editorial-card":
        payoff_title = str(scene.get("payoff_title") or "").strip()
        payoff_detail = str(scene.get("payoff_detail") or "").strip()
        payoff_punch = str(scene.get("payoff_punch") or "").strip()
        payoff_callback = str(scene.get("payoff_callback") or "").strip()
        discussion_prompt = str(scene.get("discussion_prompt") or "").strip()
        payoff_hold = payoff_punch or discussion_prompt
        if not payoff_title:
            payoff_title = caption
            for separator in (" · ", " — ", "\n"):
                if separator in caption:
                    payoff_title, payoff_detail = [part.strip() for part in caption.split(separator, 1)]
                    break

        panel_left, panel_right, panel_bottom = 48, 1032, 1702
        panel_top = 1128 if payoff_hold else 1278

        if template == "fact-stack" and payoff_callback:
            callback_font, callback_lines = fitted_lines(
                draw,
                payoff_callback,
                font_path,
                820,
                1,
                40,
                bold=True,
            )
            callback_width = max(
                (draw.textbbox((0, 0), line, font=callback_font)[2] for line in callback_lines),
                default=0,
            )
            callback_height = 72
            callback_gap = 24 if payoff_hold else 20
            callback_top = panel_top - callback_height - callback_gap
            callback_left = max(48, (width - callback_width) / 2 - 34)
            callback_right = min(1032, (width + callback_width) / 2 + 34)
            draw.rounded_rectangle(
                (callback_left, callback_top, callback_right, callback_top + callback_height),
                radius=20,
                fill=(3, 5, 7, 226),
            )
            draw_centered_lines(draw, callback_lines, callback_font, callback_top + 13, accent, spacing=4)

        draw.rounded_rectangle(
            (panel_left, panel_top, panel_right, panel_bottom),
            radius=34,
            fill=(4, 6, 8, 255),
            outline=(255, 255, 255, 60),
            width=2,
        )

        # Reserve separate vertical zones for answer, meaning, and the final
        # retention line. A version 6 payoff punch takes priority here; an
        # older discussion prompt remains compatible when no punch is set.
        # This keeps every payoff line large at 720p and prevents dynamic text
        # height from pushing one role into another.
        title_size = 68 if payoff_hold else 72
        title_y = 1192 if payoff_hold else 1342
        title_font, title_lines = fitted_lines(draw, payoff_title, font_path, 870, 2, title_size, bold=True)
        title_bottom = draw_centered_lines(draw, title_lines, title_font, title_y, "white", spacing=10)
        if payoff_detail:
            detail_size = 54 if discussion_prompt else 56
            detail_font, detail_lines = fitted_lines(
                draw,
                payoff_detail,
                font_path,
                850,
                2,
                detail_size,
                bold=True,
            )
            if payoff_hold:
                detail_y = max(title_bottom + 24, 1362)
            else:
                detail_y = max(title_bottom + 28, 1494)
            detail_bottom = draw_centered_lines(draw, detail_lines, detail_font, detail_y, accent, spacing=8)
        else:
            detail_bottom = title_bottom
        if payoff_hold:
            divider_y = max(detail_bottom + 24, 1516)
            draw.rounded_rectangle((138, divider_y, 942, divider_y + 3), radius=1, fill=(255, 255, 255, 64))
            prompt_font, prompt_lines = fitted_lines(
                draw,
                payoff_hold,
                font_path,
                850,
                1,
                66,
                bold=True,
            )
            draw_centered_lines(draw, prompt_lines, prompt_font, divider_y + 24, accent, spacing=6)
    else:
        if show_payoff:
            payoff_label = "결론"
            payoff_font = load_font_face(font_path, 50, bold=True)
            payoff_box = draw.textbbox((0, 0), payoff_label, font=payoff_font)
            payoff_width = payoff_box[2] - payoff_box[0]
            payoff_left = (width - payoff_width) / 2 - 36
            draw.rounded_rectangle(
                (payoff_left, 1418, payoff_left + payoff_width + 72, 1504),
                radius=22,
                fill=accent,
            )
            draw.text((payoff_left + 36, 1430), payoff_label, font=payoff_font, fill="#050505")
    if caption and not fact_stack_caption_handled and not (show_payoff and payoff_panel_style == "editorial-card"):
        caption_font, caption_lines = fitted_lines(draw, caption, font_path, 930, 2, 76)
        line_height = caption_font.size + 18
        caption_y = 1540 - ((len(caption_lines) - 1) * line_height) // 2
        caption_focus = str(scene.get("caption_focus") or "").strip()
        if caption_focus:
            draw_centered_stroked_emphasized_lines(
                draw,
                caption_lines,
                caption_font,
                caption_y,
                "white",
                accent,
                caption_focus,
                spacing=18,
                stroke_width=10,
            )
        else:
            for line in caption_lines:
                box = draw.textbbox((0, 0), line, font=caption_font)
                line_width = box[2] - box[0]
                draw.text(
                    ((width - line_width) / 2, caption_y),
                    line,
                    font=caption_font,
                    fill=accent,
                    stroke_width=10,
                    stroke_fill="#050505",
                )
                caption_y += line_height

    credit = str(scene.get("credit") or "").strip()
    if credit:
        credit_lines = wrap_text(draw, credit, small_font, 760)[:2]
        draw_left_lines(draw, credit_lines, small_font, 58, 1732, "#C7CDD6", spacing=4)

    source_label = str(scene.get("source_label") or "").strip()
    if source_label and style.get("show_source_label") is True:
        source_text = f"뉴스 출처: {source_label}"
        source_font = load_font_face(font_path, 25)
        source_lines = wrap_text(draw, source_text, source_font, 900)[:1]
        if source_lines:
            source_box = draw.textbbox((0, 0), source_lines[0], font=source_font)
            source_width = source_box[2] - source_box[0]
            draw.rounded_rectangle((48, 1810, 80 + source_width, 1860), radius=13, fill=(0, 0, 0, 178))
            draw.text((64, 1818), source_lines[0], font=source_font, fill="#E2E6EC")

    return overlay


def build_retention_visual(scene: dict, project_dir: Path):
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageOps
    except ImportError as exc:
        raise News2ShortsError("Pillow가 필요합니다. doctor 결과를 확인하세요.") from exc

    width, height = 1080, 1920
    canvas = Image.new("RGB", (width, height), "#111820")
    image_value = str(scene.get("image") or "").strip()
    if image_value:
        image_path = resolve_project_file(project_dir, image_value)
        try:
            source = ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
        except Exception as exc:
            raise News2ShortsError(f"이미지를 열 수 없습니다: {image_value}: {exc}") from exc
        image_fit = str(scene.get("image_fit") or "auto").strip().lower()
        if image_fit == "cover":
            visual = ImageOps.fit(
                source,
                (width, height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.46),
            )
            canvas.paste(visual)
        else:
            background = ImageOps.fit(
                source,
                (width, height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.46),
            ).filter(ImageFilter.GaussianBlur(radius=28))
            background = Image.blend(background, Image.new("RGB", (width, height), "#090C10"), 0.42)
            canvas.paste(background)
            safe_left, safe_top, safe_right, safe_bottom = 108, 500, width - 108, 1630
            visual = ImageOps.contain(
                source,
                (safe_right - safe_left, safe_bottom - safe_top),
                method=Image.Resampling.LANCZOS,
            )
            paste_x = safe_left + (safe_right - safe_left - visual.width) // 2
            paste_y = safe_top + (safe_bottom - safe_top - visual.height) // 2
            canvas.paste(visual, (paste_x, paste_y))
    else:
        draw = ImageDraw.Draw(canvas)
        for y in range(height):
            ratio = y / max(height - 1, 1)
            draw.line((0, y, width, y), fill=(14 + int(13 * ratio), 21 + int(20 * ratio), 29 + int(26 * ratio)))
        for index in range(7):
            y = 690 + index * 92
            draw.rounded_rectangle((110, y, 970 - (index % 3) * 110, y + 34), radius=17, fill="#263748")

    return canvas


def render_retention_visual(scene: dict, project_dir: Path, destination: Path) -> None:
    build_retention_visual(scene, project_dir).save(destination, format="PNG", optimize=True)


def render_retention_frame(
    scene: dict,
    project: dict,
    project_dir: Path,
    destination: Path,
    *,
    draft: bool,
) -> None:
    from PIL import Image

    canvas = build_retention_visual(scene, project_dir)

    canvas = Image.alpha_composite(canvas.convert("RGBA"), build_retention_overlay(scene, project, draft=draft)).convert("RGB")
    canvas.save(destination, format="PNG", optimize=True)


def render_retention_overlay(scene: dict, project: dict, destination: Path, *, draft: bool) -> None:
    build_retention_overlay(scene, project, draft=draft).save(destination, format="PNG", optimize=True)


def render_source_video_overlay(scene: dict, destination: Path) -> None:
    """Draw provenance only, leaving source video and embedded captions unobstructed."""

    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise News2ShortsError("Pillow가 필요합니다. doctor 결과를 확인하세요.") from exc

    width, height = 1080, 1920
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font_face(find_font(), 27)
    credit = str(scene.get("credit") or scene.get("source_label") or "").strip()
    if credit:
        lines = wrap_text(draw, credit, font, 940)[:1]
        if lines:
            text = lines[0]
            box = draw.textbbox((0, 0), text, font=font)
            text_width = box[2] - box[0]
            text_height = box[3] - box[1]
            left = 28
            top = height - text_height - 40
            draw.rounded_rectangle(
                (left - 10, top - 7, left + text_width + 10, top + text_height + 7),
                radius=8,
                fill=(0, 0, 0, 132),
            )
            draw.text((left, top), text, font=font, fill=(255, 255, 255, 224))
    overlay.save(destination, format="PNG", optimize=True)


def render_frame(
    scene: dict,
    project: dict,
    project_dir: Path,
    destination: Path,
    *,
    draft: bool,
) -> None:
    template = str(visual_style_config(project).get("template") or "classic-card")
    if template in RETENTION_TEMPLATES:
        render_retention_frame(scene, project, project_dir, destination, draft=draft)
        return
    if template == "broadcast-card":
        render_broadcast_frame(scene, project, project_dir, destination, draft=draft)
        return
    render_classic_frame(scene, project, project_dir, destination, draft=draft)


def audio_duration(path: Path) -> float:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise News2ShortsError(f"오디오 길이를 읽을 수 없습니다: {path}") from exc


def create_silent_audio(path: Path, duration: float) -> None:
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=stereo",
            "-t",
            f"{duration:.3f}",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ]
    )


def create_news_pulse_audio(path: Path, duration: float) -> None:
    duration = max(1.0, float(duration))
    fade_out_start = max(0.0, duration - 0.4)
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=110:sample_rate=48000:duration={duration:.3f}",
            "-af",
            (
                "tremolo=f=2.0:d=0.55,lowpass=f=900,volume=1.0,"
                f"afade=t=in:st=0:d=0.20,afade=t=out:st={fade_out_start:.3f}:d=0.40"
            ),
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ]
    )


def record_generated_background_music(manifest: dict, duration: float) -> None:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        assets = []
        manifest["assets"] = assets
    assets[:] = [
        item
        for item in assets
        if not isinstance(item, dict)
        or str(item.get("path") or "").strip() != VISUAL_FIRST_AUDIO_PATH
    ]
    assets.append(
        {
            "id": "audio-background-music",
            "path": VISUAL_FIRST_AUDIO_PATH,
            "kind": "generated",
            "media_type": "audio",
            "usage_role": "background-music",
            "permission_status": "owned",
            "approved": True,
            "synthetic": True,
            "vocals": False,
            "profile": VISUAL_FIRST_AUDIO_PROFILE,
            "source_method": "renderer-generated",
            "duration": round(float(duration), 3),
            "retrieved_at": iso_now(),
        }
    )


def typecast_api_key() -> str:
    api_key, _ = typecast_api_key_record()
    if not api_key:
        if typecast_keychain_check_limited():
            raise News2ShortsError(
                "Typecast API 키에 접근할 수 없습니다. 이 Codex 실행에서는 macOS 키체인 확인이 "
                f"제한될 수 있습니다. 사용자 터미널에서 `{typecast_setup_command('doctor')}`를 먼저 "
                f"실행하고, 실제로 키가 없을 때만 `{typecast_setup_command('configure-typecast')}`를 "
                "한 번 실행하세요. 로컬 TTS로 자동 대체하지 않습니다."
            )
        if sys.platform == "darwin":
            raise News2ShortsError(
                "Typecast API 키가 없습니다. "
                f"`{typecast_setup_command('configure-typecast')}`를 한 번 실행한 뒤 "
                f"`{typecast_setup_command('doctor')}`로 확인하세요."
            )
        raise News2ShortsError(
            "Typecast API 키가 없습니다. TYPECAST_API_KEY 환경변수를 설정한 뒤 doctor로 확인하세요."
        )
    return api_key


def trim_typecast_outer_silence(path: Path) -> None:
    """Keep short edge pauses while preserving every pause inside the narration."""

    trimmed = path.with_name(f".{path.stem}-outer-trim.wav")
    source_duration = audio_duration(path)
    if not math.isfinite(source_duration) or not 0.05 < source_duration <= 180.0:
        raise News2ShortsError(
            f"Typecast 원본 WAV 길이가 비정상입니다: {source_duration:.3f}초"
        )
    audio_filter = (
        "silenceremove="
        "start_periods=1:"
        "start_duration=0.05:"
        f"start_threshold={TYPECAST_SILENCE_THRESHOLD_DB}dB:"
        f"start_silence={TYPECAST_LEADING_SILENCE_KEEP_SECONDS},"
        "areverse,"
        "silenceremove="
        "start_periods=1:"
        "start_duration=0.05:"
        f"start_threshold={TYPECAST_SILENCE_THRESHOLD_DB}dB:"
        f"start_silence={TYPECAST_TRAILING_SILENCE_KEEP_SECONDS},"
        "areverse"
    )
    try:
        run_command(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-t",
                f"{source_duration:.3f}",
                "-i",
                str(path),
                "-af",
                audio_filter,
                "-ac",
                "2",
                "-ar",
                "48000",
                "-t",
                f"{source_duration:.3f}",
                "-c:a",
                "pcm_s16le",
                "-y",
                str(trimmed),
            ]
        )
        trimmed_duration = audio_duration(trimmed)
        if trimmed_duration <= 0.05:
            raise News2ShortsError("Typecast 외곽 무음 정리 후 음성이 비었습니다.")
        if trimmed_duration > source_duration + 0.5:
            raise News2ShortsError(
                "Typecast 외곽 무음 정리 결과가 원본보다 비정상적으로 깁니다: "
                f"{trimmed_duration:.3f}/{source_duration:.3f}초"
            )
        os.replace(trimmed, path)
    finally:
        trimmed.unlink(missing_ok=True)


def typecast_audio(
    path: Path,
    narration: str,
    *,
    voice_id: str,
    tempo: float,
    previous_text: str,
    next_text: str,
    delivery: str = "auto",
) -> None:
    narration = suppress_editorial_identifiers(narration)
    previous_text = suppress_editorial_identifiers(previous_text)
    next_text = suppress_editorial_identifiers(next_text)
    if len(narration) > 2000:
        raise News2ShortsError("Typecast 장면 내레이션은 2,000자 이하여야 합니다.")
    api_key = typecast_api_key()
    delivery_key = str(delivery or "auto").strip().lower()
    delivery_profile = TYPECAST_DELIVERY_PROFILES.get(delivery_key)
    if delivery_profile is None:
        raise News2ShortsError(
            "voice_delivery는 auto, contrast, verdict 중 하나여야 합니다."
        )
    if delivery_profile["emotion_type"] == "smart":
        prompt = {
            "emotion_type": "smart",
            "previous_text": previous_text[-2000:],
            "next_text": next_text[:2000],
        }
    else:
        prompt = {
            "emotion_type": "preset",
            "emotion_preset": delivery_profile["emotion_preset"],
            "emotion_intensity": delivery_profile["emotion_intensity"],
        }
    effective_tempo = min(
        2.0,
        max(0.5, round(tempo * float(delivery_profile["tempo_multiplier"]), 3)),
    )
    payload = {
        "voice_id": voice_id,
        "text": narration,
        "model": TYPECAST_MODEL,
        "language": "kor",
        "prompt": prompt,
        "output": {
            "target_lufs": -14.0,
            "audio_pitch": int(delivery_profile["audio_pitch"]),
            "audio_tempo": effective_tempo,
            "audio_format": "wav",
        },
        "seed": 42,
    }
    req = request.Request(
        TYPECAST_TTS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
            "User-Agent": "news2shorts/0.5",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60, context=verified_ssl_context()) as response:
            audio = response.read()
    except error.HTTPError as exc:
        messages = {
            401: "TYPECAST_API_KEY를 확인하세요.",
            402: "Typecast 사용량 또는 결제 상태를 확인하세요.",
            429: "Typecast 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.",
        }
        detail = messages.get(exc.code, "Typecast 콘솔과 요청 설정을 확인하세요.")
        raise News2ShortsError(f"Typecast TTS 요청 실패: HTTP {exc.code}. {detail}") from exc
    except error.URLError as exc:
        raise News2ShortsError(f"Typecast TTS 연결 실패: {exc.reason}") from exc

    if len(audio) < 12 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        raise News2ShortsError("Typecast TTS 응답이 WAV 오디오가 아닙니다.")
    path.write_bytes(audio)
    trim_typecast_outer_silence(path)


def scene_audio(
    scene: dict,
    project_dir: Path,
    work_dir: Path,
    index: int,
    *,
    no_tts: bool,
    tts_provider: str,
    voice: str,
    rate: int,
    typecast_voice_id: str,
    typecast_tempo: float,
    previous_text: str,
    next_text: str,
) -> tuple[Path, float, str]:
    configured = str(scene.get("audio") or "").strip()
    if configured:
        path = resolve_project_file(project_dir, configured)
        return path, audio_duration(path), "file"

    requested = max(1.0, float(scene.get("duration") or 0.0))
    narration = suppress_editorial_identifiers(str(scene.get("narration") or ""))
    if no_tts or not narration:
        silent_path = work_dir / f"scene-{index:02d}-silent.wav"
        create_silent_audio(silent_path, requested)
        return silent_path, requested, "silent"

    if tts_provider == "typecast":
        audio_path = work_dir / f"scene-{index:02d}-typecast.wav"
        typecast_audio(
            audio_path,
            narration,
            voice_id=typecast_voice_id,
            tempo=typecast_tempo,
            previous_text=previous_text,
            next_text=next_text,
            delivery=str(scene.get("voice_delivery") or "auto"),
        )
        return audio_path, audio_duration(audio_path), "typecast"

    say = shutil.which("say")
    if not say:
        raise News2ShortsError(
            "로컬 TTS를 찾지 못했습니다. Typecast를 사용하거나 장면 audio를 지정하거나 "
            "--no-tts를 사용하세요."
        )
    audio_path = work_dir / f"scene-{index:02d}-narration.aiff"
    run_command([say, "-v", voice, "-r", str(rate), "-o", str(audio_path), narration])
    return audio_path, audio_duration(audio_path), "local"


def continuous_flow_audio(
    scenes: list[dict],
    work_dir: Path,
    *,
    no_tts: bool,
    tts_provider: str,
    voice: str,
    rate: int,
    typecast_voice_id: str,
    typecast_tempo: float,
    output_stem: str = "continuous-flow",
) -> tuple[Path, float, str]:
    narrations = [
        suppress_editorial_identifiers(str(scene.get("narration") or "")).strip()
        for scene in scenes
        if isinstance(scene, dict)
    ]
    narration = " ".join(text for text in narrations if text)
    requested = max(
        1.0,
        sum(max(1.0, float(scene.get("duration") or 0.0)) for scene in scenes),
    )
    if no_tts or not narration:
        path = work_dir / f"{output_stem}-silent.wav"
        create_silent_audio(path, requested)
        return path, requested, "silent-continuous"

    if tts_provider == "typecast":
        path = work_dir / f"{output_stem}-typecast.wav"
        typecast_audio(
            path,
            narration,
            voice_id=typecast_voice_id,
            tempo=typecast_tempo,
            previous_text="",
            next_text="",
            delivery="auto",
        )
        return path, audio_duration(path), "typecast-continuous"

    say = shutil.which("say")
    if not say:
        raise News2ShortsError(
            "로컬 TTS를 찾지 못했습니다. Typecast를 사용하거나 --no-tts를 사용하세요."
        )
    path = work_dir / f"{output_stem}-narration.aiff"
    run_command([say, "-v", voice, "-r", str(rate), "-o", str(path), narration])
    return path, audio_duration(path), "local-continuous"


def continuous_flow_scene_durations(scenes: list[dict], audio_seconds: float) -> list[float]:
    minimums = [
        CONTINUOUS_FLOW_PAYOFF_MIN_SECONDS
        if str(scene.get("beat") or "").strip() == "payoff"
        else CONTINUOUS_FLOW_MIN_SCENE_SECONDS
        for scene in scenes
    ]
    target = max(float(audio_seconds), sum(minimums))
    weights = [
        max(1, narration_character_count(scene.get("narration")))
        for scene in scenes
    ]
    remaining = max(0.0, target - sum(minimums))
    weight_total = max(1, sum(weights))
    durations = [
        minimum + (remaining * weight / weight_total)
        for minimum, weight in zip(minimums, weights)
    ]
    durations[-1] += target - sum(durations)
    return durations


def estimated_continuous_flow_scene_reports(
    project: dict,
    scenes: list[dict],
) -> list[dict]:
    """Build a pre-TTS timing estimate solely for choosing a safe CTA scene boundary."""

    durations = [
        max(
            CONTINUOUS_FLOW_PAYOFF_MIN_SECONDS
            if str(scene.get("beat") or "").strip() == "payoff"
            else CONTINUOUS_FLOW_MIN_SCENE_SECONDS,
            float(scene.get("duration") or 0.0),
        )
        for scene in scenes
    ]
    total = sum(durations)
    try:
        target = float(project.get("target_duration_seconds") or 0.0)
    except (TypeError, ValueError):
        target = 0.0
    if durations and target > total > 0.0:
        scale = target / total
        durations = [duration * scale for duration in durations]

    reports: list[dict] = []
    cursor = 0.0
    for duration in durations:
        reports.append(
            {
                "timeline_start": round(cursor, 3),
                "timeline_end": round(cursor + duration, 3),
            }
        )
        cursor += duration
    return reports


def continuous_flow_audio_group_ranges(
    scene_count: int,
    mid_cta_selection: dict,
) -> list[tuple[int, int]]:
    """Keep every CTA edge between complete continuous-flow TTS requests."""

    if scene_count <= 0:
        return []
    if mid_cta_selection.get("enabled") is not True:
        return [(0, scene_count)]
    split_index = int(mid_cta_selection.get("insert_after_scene_index") or 0)
    if not 0 < split_index < scene_count:
        raise News2ShortsError("중간 CTA는 앞뒤 뉴스 장면이 모두 있는 경계에만 넣을 수 있습니다.")
    return [(0, split_index), (split_index, scene_count)]


def extract_audio_segment(
    source: Path,
    destination: Path,
    *,
    start: float,
    duration: float,
) -> None:
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-af",
            "apad",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(destination),
        ]
    )


def cmd_review_source_audio(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"프로젝트 디렉터리를 찾을 수 없습니다: {project_dir}")
    storyboard = load_json(project_dir / "storyboard.json")
    if not isinstance(storyboard, dict) or not isinstance(storyboard.get("scenes"), list):
        raise News2ShortsError("storyboard.json의 scenes는 배열이어야 합니다.")
    requested_scene_ids = {str(value).strip() for value in (args.scene_id or []) if str(value).strip()}
    source_scenes = [
        scene
        for scene in storyboard["scenes"]
        if isinstance(scene, dict)
        and scene_uses_source_video_audio(scene)
        and (
            not requested_scene_ids
            or str(scene.get("id") or "").strip() in requested_scene_ids
        )
    ]
    if requested_scene_ids:
        found = {str(scene.get("id") or "").strip() for scene in source_scenes}
        missing = sorted(requested_scene_ids - found)
        if missing:
            raise News2ShortsError(
                "source-video 장면을 찾지 못했습니다: " + ", ".join(missing)
            )
    if not source_scenes:
        raise News2ShortsError("검토할 audio_mode: source-video 장면이 없습니다.")

    scene_ids = [str(scene.get("id") or "").strip() for scene in source_scenes]
    transcript_path: Path | None = None
    transcript_records: dict[str, dict] = {}
    backend = str(args.backend or "auto").strip()
    if args.transcript_file:
        transcript_path = Path(args.transcript_file).expanduser().resolve()
        if not transcript_path.is_file():
            raise News2ShortsError(f"전사 파일을 찾을 수 없습니다: {transcript_path}")
        transcript_records = load_source_transcript_records(transcript_path, scene_ids)
        backend = "transcript-file"
    elif backend == "transcript-file":
        raise News2ShortsError("transcript-file 백엔드에는 --transcript-file이 필요합니다.")
    elif backend == "auto":
        backend = "openai-whisper-cli" if shutil.which("whisper") else ""
        if not backend:
            raise News2ShortsError(
                "source audio transcript_pending: 자동 전사 백엔드가 없습니다. "
                "로컬 OpenAI Whisper CLI를 준비하거나 --transcript-file을 제공하세요."
            )
    elif backend == "openai-whisper-cli" and not shutil.which("whisper"):
        raise News2ShortsError("로컬 OpenAI Whisper CLI 실행 파일을 찾지 못했습니다: whisper")

    reviews: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="news2shorts-source-audio-") as temp_name:
        temp_dir = Path(temp_name)
        for index, scene in enumerate(source_scenes, start=1):
            scene_id = str(scene.get("id") or f"source-scene-{index:02d}").strip()
            source_value = str(scene.get("video") or "").strip()
            source_path = resolve_project_file(project_dir, source_value)
            start = max(0.0, float(scene.get("video_start") or 0.0))
            duration = max(0.0, float(scene.get("duration") or 0.0))
            if duration <= 0:
                raise News2ShortsError(f"source-video 장면 duration은 0보다 커야 합니다: {scene_id}")
            audio_path = temp_dir / f"{scene_id}.wav"
            extract_audio_segment(source_path, audio_path, start=start, duration=duration)
            if backend == "transcript-file":
                transcript = transcript_records.get(scene_id)
                if transcript is None and len(source_scenes) == 1:
                    transcript = transcript_records.get("*")
                if transcript is None:
                    raise News2ShortsError(f"전사 파일에 장면 기록이 없습니다: {scene_id}")
            else:
                transcript = run_whisper_source_transcription(
                    audio_path,
                    output_dir=temp_dir / "whisper",
                    language=args.language,
                    model=args.model,
                    model_dir=Path(args.model_dir).expanduser().resolve(),
                    allow_model_download=args.allow_model_download,
                )
            reviews.append(
                build_source_audio_scene_review(
                    scene,
                    source_path=source_value,
                    source_sha256=file_sha256(source_path),
                    transcript=transcript,
                    timing_confirmed=args.confirm_timing_reviewed,
                )
            )

    passed = all(review["status"] == "passed" for review in reviews)
    report = {
        "version": SOURCE_AUDIO_REVIEW_VERSION,
        "generated_at": iso_now(),
        "status": "passed" if passed else "review_required",
        "backend": backend,
        "language": args.language,
        "model": args.model if backend == "openai-whisper-cli" else "",
        "transcript_input": (
            {
                "name": transcript_path.name,
                "sha256": file_sha256(transcript_path),
            }
            if transcript_path is not None
            else None
        ),
        "scene_count": len(reviews),
        "scenes": reviews,
        "publication_claim_boundary": (
            "전사는 영상 속 발화 검토용이며 화자의 신원이나 발언의 사실성을 증명하지 않습니다."
        ),
    }
    output_path = project_dir / SOURCE_AUDIO_REVIEW_FILENAME
    write_json(output_path, report)
    print(
        json.dumps(
            {
                "project_dir": str(project_dir),
                "report": SOURCE_AUDIO_REVIEW_FILENAME,
                "status": report["status"],
                "backend": backend,
                "scenes": [
                    {
                        "scene_id": review["scene_id"],
                        "status": review["status"],
                        "expected_text": review["expected_text"],
                        "transcript_text": review["transcript_text"],
                        "reasons": review["reasons"],
                    }
                    for review in reviews
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if passed else 2


def mux_continuous_audio(video: Path, audio: Path, destination: Path) -> None:
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-shortest",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ]
    )


def rights_record_for(manifest: dict, image: str) -> dict | None:
    normalized = Path(image).as_posix()
    for asset in manifest.get("assets", []):
        if not isinstance(asset, dict):
            continue
        if Path(str(asset.get("path") or "")).as_posix() == normalized:
            return asset
    return None


def is_http_url(value: str) -> bool:
    parsed = parse.urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_search_result_url(value: str) -> bool:
    parsed = parse.urlsplit(value)
    host = parsed.netloc.lower().removeprefix("www.")
    if host == "search.naver.com" or host == "images.google.com":
        return True
    if host == "google.com" and parsed.path.startswith(("/search", "/imgres", "/url")):
        return True
    if host == "bing.com" and (parsed.path.startswith("/search") or "images" in parsed.path):
        return True
    return False


def generated_image_size_limit(visual_sourcing: dict) -> tuple[int, int] | None:
    configured = str(visual_sourcing.get("generated_image_size") or "").strip().lower()
    match = re.fullmatch(r"(\d{2,4})x(\d{2,4})", configured)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def fact_stack_contract_issues(
    claim_ids: set[str],
    scenes: list[dict],
    profile: dict,
    *,
    strict: bool,
    final: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    strict_target = errors if final else warnings
    linked_claims: set[str] = set()
    evidence_kinds: list[str] = []
    fact_indexes: list[tuple[int, int, str]] = []
    proof_scene_count = 0
    proof_video_count = 0
    claims_before_turn: set[str] = set()
    first_turn_claims: set[str] = set()

    def scene_duration(scene: dict) -> float:
        try:
            return max(0.0, float(scene.get("duration") or 0.0))
        except (TypeError, ValueError):
            return 0.0

    for index, scene in enumerate(scenes, start=1):
        scene_id = str(scene.get("id") or f"scene-{index:02d}")
        beat = str(scene.get("beat") or "").strip()
        raw_claim_ids = scene.get("claim_ids")
        scene_claims = (
            {str(value).strip() for value in raw_claim_ids if str(value).strip()}
            if isinstance(raw_claim_ids, list)
            else set()
        )
        if raw_claim_ids is not None and not isinstance(raw_claim_ids, list):
            errors.append(f"claim_ids는 배열이어야 합니다: {scene_id}")
        missing_claims = scene_claims - claim_ids
        if missing_claims:
            errors.append(f"존재하지 않는 claim ID 참조: {scene_id}: {sorted(missing_claims)}")

        if beat in FACT_STACK_PROOF_BEATS:
            proof_scene_count += 1
            if str(scene.get("video") or "").strip():
                proof_video_count += 1
            if strict and not scene_claims:
                strict_target.append(f"팩트스택 근거 장면에 claim_ids가 없습니다: {scene_id}")
            linked_claims.update(scene_claims)

            evidence_kind = str(scene.get("evidence_kind") or "").strip()
            if strict and not evidence_kind:
                strict_target.append(f"팩트스택 근거 장면에 evidence_kind가 없습니다: {scene_id}")
            elif evidence_kind and evidence_kind not in FACT_STACK_EVIDENCE_KINDS:
                errors.append(f"지원하지 않는 fact-stack evidence_kind: {scene_id}: {evidence_kind}")
            elif evidence_kind:
                evidence_kinds.append(evidence_kind)

            if strict and not str(scene.get("evidence_label") or "").strip():
                strict_target.append(f"팩트스택 근거 장면에 evidence_label이 없습니다: {scene_id}")
            if evidence_kind in {"number", "comparison"} and not str(
                scene.get("evidence_value") or ""
            ).strip():
                strict_target.append(f"숫자·비교 근거 장면에 evidence_value가 없습니다: {scene_id}")
            if evidence_kind == "video" and not str(scene.get("video") or "").strip():
                errors.append(f"evidence_kind가 video이지만 video 자산이 없습니다: {scene_id}")
            if evidence_kind == "photo" and not str(scene.get("image") or "").strip():
                errors.append(f"evidence_kind가 photo이지만 image 자산이 없습니다: {scene_id}")

        fact_index = str(scene.get("fact_index") or "").strip()
        if strict and beat in FACT_STACK_PROOF_BEATS and not fact_index:
            strict_target.append(f"팩트스택 근거 장면에 fact_index가 없습니다: {scene_id}")
        if strict and beat not in FACT_STACK_PROOF_BEATS and fact_index:
            strict_target.append(f"fact_index는 팩트스택 근거 장면에만 사용하세요: {scene_id}")
        if fact_index:
            match = FACT_INDEX_PATTERN.fullmatch(fact_index)
            if not match:
                errors.append(f"fact_index는 N/M 형식이어야 합니다: {scene_id}: {fact_index}")
            else:
                current = int(match.group("current"))
                total = int(match.group("total"))
                if current > total:
                    errors.append(f"fact_index 현재 번호가 전체보다 큽니다: {scene_id}: {fact_index}")
                elif beat in FACT_STACK_PROOF_BEATS:
                    fact_indexes.append((current, total, scene_id))

        if beat in {"turn", "rehook"} and not first_turn_claims:
            first_turn_claims = scene_claims
        elif not first_turn_claims:
            claims_before_turn.update(scene_claims)

    if strict:
        if proof_scene_count < 3:
            strict_target.append(f"팩트스택에는 서로 다른 근거 장면이 최소 3개 필요합니다: {proof_scene_count}/3")
        if len(linked_claims) < 3:
            strict_target.append(f"팩트스택에는 서로 다른 claim 연결이 최소 3개 필요합니다: {len(linked_claims)}/3")
        if len(fact_indexes) < 3:
            strict_target.append(f"팩트스택에는 화면에 쌓이는 fact_index가 최소 3개 필요합니다: {len(fact_indexes)}/3")
        if fact_indexes:
            totals = {total for _, total, _ in fact_indexes}
            currents = [current for current, _, _ in fact_indexes]
            expected_currents = list(range(1, len(currents) + 1))
            if (
                len(totals) != 1
                or currents != expected_currents
                or next(iter(totals), 0) != len(currents)
            ):
                strict_target.append("fact_index는 1/N부터 N/N까지 빠짐없이 오름차순으로 배치하세요.")
        last_non_loop = next(
            (scene for scene in reversed(scenes) if str(scene.get("beat") or "") != "loop"),
            {},
        )
        if not str(last_non_loop.get("payoff_callback") or "").strip():
            strict_target.append("새 팩트스택 payoff에는 후크를 답과 연결하는 payoff_callback이 필요합니다.")
        if proof_video_count == 0:
            warnings.append(
                "팩트스택의 모든 근거 장면이 정지 이미지입니다. 권리가 확인된 실제 클립을 우선 검토하고, "
                "없다면 숫자·비교·문서 강조 화면으로 증거 변화를 강화하세요."
            )
        if evidence_kinds and len(set(evidence_kinds)) < 2:
            warnings.append("팩트스택의 evidence_kind가 한 종류뿐입니다. 사진·문서·숫자·지도 등 증거 유형을 섞으세요.")
        if first_turn_claims and first_turn_claims <= claims_before_turn:
            warnings.append("중간 turn/rehook이 앞 장면과 같은 claim만 반복합니다. 새로운 해석이나 조건을 연결하세요.")

    planned_total = sum(scene_duration(scene) for scene in scenes)
    if strict and planned_total > 0:
        cursor = 0.0
        first_turn_ratio: float | None = None
        payoff_text = str(profile.get("payoff") or "").strip()
        for scene in scenes:
            beat = str(scene.get("beat") or "").strip()
            narration = str(scene.get("narration") or "").strip()
            ratio = cursor / planned_total
            if first_turn_ratio is None and beat in {"turn", "rehook"}:
                first_turn_ratio = ratio
            if beat in {"context", "evidence"} and ratio < 0.45:
                if EARLY_RESOLUTION_PATTERN.search(narration) or text_similarity(narration, payoff_text) >= 0.62:
                    warnings.append(
                        f"팩트스택 결론이 너무 일찍 노출될 수 있습니다: {scene.get('id', 'unknown')}. "
                        "초반에는 격차를 열고 근거가 쌓인 뒤 원인이나 답을 공개하세요."
                    )
            cursor += scene_duration(scene)
        if first_turn_ratio is not None and not 0.35 <= first_turn_ratio <= 0.70:
            warnings.append(
                f"팩트스택 turn/rehook 위치가 권장 중간 구간을 벗어납니다: {first_turn_ratio * 100:.0f}%"
            )
    return errors, warnings


def validate_project(project_dir: Path, *, final: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        "project.json",
        "sources.json",
        "fact-sheet.json",
        "storyboard.json",
        "rights-manifest.json",
        "publish.json",
    ]
    loaded: dict[str, dict] = {}
    for filename in required:
        path = project_dir / filename
        if not path.is_file():
            errors.append(f"필수 파일 누락: {filename}")
            continue
        try:
            value = load_json(path)
            if not isinstance(value, dict):
                errors.append(f"최상위 JSON 객체가 필요합니다: {filename}")
            else:
                loaded[filename] = value
        except News2ShortsError as exc:
            errors.append(str(exc))
    if errors:
        return errors, warnings

    project = loaded["project.json"]
    sources = loaded["sources.json"].get("sources", [])
    claims = loaded["fact-sheet.json"].get("claims", [])
    storyboard = loaded["storyboard.json"]
    manifest = loaded["rights-manifest.json"]
    publish = loaded["publish.json"]
    scenes = storyboard.get("scenes", [])
    assets = manifest.get("assets", [])
    searches = manifest.get("searches", [])
    visual_sourcing = project.get("visual_sourcing") or {}

    if not isinstance(sources, list):
        errors.append("sources.json의 sources는 배열이어야 합니다.")
        sources = []
    if not isinstance(claims, list):
        errors.append("fact-sheet.json의 claims는 배열이어야 합니다.")
        claims = []
    known_claim_ids = {
        str(claim.get("id")).strip()
        for claim in claims
        if isinstance(claim, dict) and str(claim.get("id") or "").strip()
    }
    if not isinstance(scenes, list) or not scenes:
        errors.append("storyboard.json에 장면이 없습니다.")
        return errors, warnings
    if not isinstance(assets, list):
        errors.append("rights-manifest.json의 assets는 배열이어야 합니다.")
        assets = []
        manifest["assets"] = assets
    if not isinstance(searches, list):
        errors.append("rights-manifest.json의 searches는 배열이어야 합니다.")
        searches = []
    if not isinstance(visual_sourcing, dict):
        errors.append("project.json의 visual_sourcing은 객체여야 합니다.")
        visual_sourcing = {}
    source_priority = visual_sourcing.get("source_priority")
    if source_priority is not None:
        if not isinstance(source_priority, list) or not all(
            isinstance(value, str) and value.strip() for value in source_priority
        ):
            errors.append("visual_sourcing.source_priority는 비어 있지 않은 문자열 배열이어야 합니다.")
        elif tuple(source_priority) != DEFAULT_VISUAL_SOURCE_PRIORITY:
            errors.append(
                "visual_sourcing.source_priority는 뉴스 기사, 공개 커뮤니티, 공식 자료, "
                "라이선스 자료, 생성 보완 순서여야 합니다."
            )
        if visual_sourcing.get("prefer_current_news_and_community_visuals") is not True:
            errors.append(
                "visual_sourcing.source_priority를 사용하면 "
                "prefer_current_news_and_community_visuals=true가 필요합니다."
            )
        if visual_sourcing.get("community_visual_privacy_review_required") is not True:
            errors.append(
                "공개 커뮤니티 이미지를 우선 탐색하면 "
                "community_visual_privacy_review_required=true가 필요합니다."
            )
    korean_visuals_required = visual_sourcing.get("korean_visuals_required") is True
    international_visuals = visual_sourcing.get("international_source_visuals")
    international_visuals_enabled = (
        isinstance(international_visuals, dict)
        and international_visuals.get("enabled") is True
    )
    if korean_visuals_required:
        if str(visual_sourcing.get("visual_locale") or "").strip() != DEFAULT_VISUAL_LOCALE:
            errors.append("한국 이미지 전용 프로젝트는 visual_sourcing.visual_locale=ko-KR이 필요합니다.")
        if (
            str(visual_sourcing.get("foreign_visual_fallback") or "").strip()
            != DEFAULT_FOREIGN_VISUAL_FALLBACK
        ):
            errors.append(
                "한국 이미지 전용 프로젝트는 visual_sourcing.foreign_visual_fallback=blocked가 필요합니다."
            )
        if visual_sourcing.get("korean_context_review_required") is not True:
            errors.append(
                "한국 이미지 전용 프로젝트는 korean_context_review_required=true가 필요합니다."
            )
        if (
            str(visual_sourcing.get("generated_style") or "").strip()
            != DEFAULT_KOREAN_GENERATED_STYLE
        ):
            errors.append(
                "한국 이미지 전용 프로젝트의 generated_style은 korean-editorial-realism이어야 합니다."
            )
    elif international_visuals_enabled:
        assert isinstance(international_visuals, dict)
        if str(visual_sourcing.get("visual_locale") or "").strip() != INTERNATIONAL_VISUAL_LOCALE:
            errors.append(
                "국제 실제사건 프로젝트는 visual_sourcing.visual_locale=mixed-source가 필요합니다."
            )
        if (
            str(visual_sourcing.get("foreign_visual_fallback") or "").strip()
            != INTERNATIONAL_FOREIGN_VISUAL_FALLBACK
        ):
            errors.append(
                "국제 실제사건 프로젝트는 foreign_visual_fallback=source-event-only가 필요합니다."
            )
        if visual_sourcing.get("korean_context_review_required") is not False:
            errors.append(
                "국제 실제사건 프로젝트는 korean_context_review_required=false가 필요합니다."
            )
        if (
            str(visual_sourcing.get("generated_style") or "").strip()
            != INTERNATIONAL_GENERATED_STYLE
        ):
            errors.append(
                "국제 실제사건 프로젝트의 generated_style은 source-event-explainer여야 합니다."
            )
        source_country = str(international_visuals.get("source_country") or "").strip().upper()
        source_locale = str(international_visuals.get("source_locale") or "").strip()
        citizen_stake = str(international_visuals.get("citizen_stake") or "").strip()
        if not re.fullmatch(r"[A-Z]{2}", source_country):
            errors.append("국제 실제사건 프로젝트에는 ISO 2자리 source_country가 필요합니다.")
        if len(source_locale) < 2:
            errors.append("국제 실제사건 프로젝트에는 source_locale이 필요합니다.")
        if len(re.sub(r"\s+", "", citizen_stake)) < 8:
            errors.append("국제 실제사건 프로젝트에는 한국 시민 이해관계가 필요합니다.")
        if international_visuals.get("actual_event_only") is not True:
            errors.append("국제 실제사건 프로젝트는 actual_event_only=true여야 합니다.")
        if international_visuals.get("rights_review_required") is not True:
            errors.append("국제 실제사건 프로젝트는 rights_review_required=true여야 합니다.")
    visual_mode = str(visual_sourcing.get("mode") or "standard").strip()
    if visual_mode not in VISUAL_MODES:
        errors.append(
            "visual_sourcing.mode는 standard, hot-real-news, whiteboard 중 하나여야 합니다."
        )
        visual_mode = "standard"

    configured_generated_ratio = visual_sourcing.get("max_generated_scene_ratio", 0.4)
    try:
        max_generated_scene_ratio = float(configured_generated_ratio)
    except (TypeError, ValueError):
        errors.append("visual_sourcing.max_generated_scene_ratio는 0과 1 사이 숫자여야 합니다.")
        max_generated_scene_ratio = 0.4
    if not 0 <= max_generated_scene_ratio <= 1:
        errors.append("visual_sourcing.max_generated_scene_ratio는 0과 1 사이여야 합니다.")
        max_generated_scene_ratio = 0.4

    configured_real_media_ratio = visual_sourcing.get(
        "min_real_media_ratio", DEFAULT_MIN_REAL_MEDIA_RATIO
    )
    try:
        min_real_media_ratio = float(configured_real_media_ratio)
    except (TypeError, ValueError):
        errors.append("visual_sourcing.min_real_media_ratio는 0과 1 사이 숫자여야 합니다.")
        min_real_media_ratio = DEFAULT_MIN_REAL_MEDIA_RATIO
    if not 0 <= min_real_media_ratio <= 1:
        errors.append("visual_sourcing.min_real_media_ratio는 0과 1 사이여야 합니다.")
        min_real_media_ratio = DEFAULT_MIN_REAL_MEDIA_RATIO

    voice_config = project.get("narration_voice")
    if voice_config is not None:
        if not isinstance(voice_config, dict):
            errors.append("project.json의 narration_voice는 객체여야 합니다.")
        else:
            voice_mode = str(voice_config.get("mode") or "auto").strip().lower()
            if voice_mode not in {"auto", "manual"}:
                errors.append("narration_voice.mode는 auto 또는 manual이어야 합니다.")
            if voice_mode == "manual":
                voice_value = str(voice_config.get("voice") or "").strip()
                if not voice_value:
                    errors.append("manual narration_voice에는 voice가 필요합니다.")
                else:
                    try:
                        resolve_typecast_voice(voice_value)
                    except News2ShortsError as exc:
                        errors.append(str(exc))

    style = visual_style_config(project)
    style_template = str(style.get("template") or "classic-card")
    render_mode = str(style.get("render_mode") or visual_mode).strip()
    if render_mode not in VISUAL_MODES:
        errors.append("visual_style.render_mode가 지원되지 않습니다.")
    elif render_mode != visual_mode:
        errors.append("visual_style.render_mode와 visual_sourcing.mode가 일치해야 합니다.")
    try:
        project_version = int(project.get("version") or 1)
    except (TypeError, ValueError):
        project_version = 1
        errors.append("project.json의 version은 숫자여야 합니다.")
    try:
        storyboard_version = int(storyboard.get("version") or 1)
    except (TypeError, ValueError):
        storyboard_version = 1
        errors.append("storyboard.json의 version은 숫자여야 합니다.")
    strict_fact_stack = style_template == "fact-stack" and storyboard_version >= 3
    strict_quick_reveal = style_template == "quick-reveal" and project_version >= 3
    strict_story_flow = project_version >= 4 and storyboard_version >= 4
    strict_issue_lens = project_version >= 5 and storyboard_version >= 5
    strict_company_visuals = project_version >= 6
    strict_citizen_question = project_version >= 9 and storyboard_version >= 5
    strict_editorial_grounding = project_version >= 10 and storyboard_version >= 5
    strict_payoff_retention = project_version >= 11 and storyboard_version >= 6
    strict_continuous_flow = project_version >= 12
    strict_early_retention = project_version >= 13 and storyboard_version >= 6
    strict_real_media_majority = project_version >= 14
    strict_v16_retention = project_version >= 16 and storyboard_version >= 6
    strict_v17_mid_cta = project_version >= 17 and storyboard_version >= 6
    delivery_mode = str(project.get("delivery_mode") or "").strip()
    visual_first = strict_v16_retention and delivery_mode == VISUAL_FIRST_MODE
    errors.extend(validate_narration_style(project, scenes))
    if strict_v16_retention and not (korean_visuals_required or international_visuals_enabled):
        errors.append(
            "version 16 새 프로젝트는 한국 이미지 전용 또는 국제 실제사건 시각 범위가 필요합니다."
        )
    if strict_continuous_flow:
        if style_template != "quick-reveal":
            errors.append("새 프로젝트의 영상 포맷은 quick-reveal만 지원합니다.")
        if strict_v16_retention:
            if delivery_mode not in DELIVERY_MODES:
                errors.append("새 프로젝트의 delivery_mode는 continuous-flow 또는 visual-first여야 합니다.")
        elif delivery_mode != CONTINUOUS_FLOW_MODE:
            errors.append("version 15 이하 새 프로젝트의 delivery_mode는 continuous-flow여야 합니다.")
        if str(storyboard.get("format") or "").strip() != "quick-reveal":
            errors.append("새 storyboard.format은 quick-reveal이어야 합니다.")
    configured_brand_intro = project.get("brand_intro")
    brand_target = errors if final else warnings
    if project_version >= 7 and not isinstance(configured_brand_intro, dict):
        brand_target.append("새 프로젝트에는 공통 brand_intro 설정이 필요합니다.")
    elif configured_brand_intro is not None and not isinstance(configured_brand_intro, dict):
        errors.append("project.json의 brand_intro는 객체여야 합니다.")
    brand_intro = brand_intro_config(project)
    if brand_intro.get("enabled") is not True:
        errors.append("공통 인트로는 항상 enabled=true여야 합니다.")
    brand_mode = str(brand_intro.get("mode") or BRAND_MODE_LEGACY_FULL).strip()
    if brand_mode not in ALLOWED_BRAND_MODES:
        errors.append("brand_intro.mode는 corner-logo 또는 legacy-full이어야 합니다.")
    if strict_v16_retention and brand_mode != BRAND_MODE_CORNER_LOGO:
        errors.append("version 16 새 프로젝트는 brand_intro.mode=corner-logo여야 합니다.")
    brand_asset_id = str(brand_intro.get("asset") or "").strip()
    brand_asset_path = brand_intro_asset_path(brand_asset_id)
    if brand_asset_path is None:
        errors.append(
            "공통 인트로 asset은 "
            f"{', '.join(sorted(ALLOWED_BRAND_INTRO_ASSET_IDS))} 중 하나여야 합니다."
        )
    if brand_mode == BRAND_MODE_CORNER_LOGO:
        if not BRAND_LOGO_PATH.is_file():
            errors.append(f"corner-logo 자산이 없습니다: {BRAND_LOGO_PATH}")
        if str(brand_intro.get("position") or "").strip() != "top-left":
            errors.append("corner-logo position은 top-left여야 합니다.")
    else:
        transition = str(brand_intro.get("transition") or "").strip()
        if transition not in ALLOWED_BRAND_INTRO_TRANSITIONS:
            errors.append(
                "brand_intro.transition은 "
                f"{', '.join(sorted(ALLOWED_BRAND_INTRO_TRANSITIONS))}만 지원합니다."
            )
        try:
            transition_duration = float(brand_intro.get("transition_duration") or 0.0)
            if not MIN_BRAND_INTRO_TRANSITION_DURATION <= transition_duration <= MAX_BRAND_INTRO_TRANSITION_DURATION:
                errors.append(
                    "brand_intro.transition_duration은 "
                    f"{MIN_BRAND_INTRO_TRANSITION_DURATION:.2f}-{MAX_BRAND_INTRO_TRANSITION_DURATION:.2f}초여야 합니다."
                )
        except (TypeError, ValueError):
            errors.append("brand_intro.transition_duration은 숫자여야 합니다.")

    if strict_v16_retention:
        audio_bed = audio_bed_config(project)
        if visual_first:
            if audio_bed.get("enabled") is not True:
                errors.append("visual-first에는 audio_bed.enabled=true가 필요합니다.")
            if str(audio_bed.get("mode") or "").strip() != "renderer-generated":
                errors.append("visual-first audio_bed.mode는 renderer-generated여야 합니다.")
            if str(audio_bed.get("profile") or "").strip() != VISUAL_FIRST_AUDIO_PROFILE:
                errors.append(f"visual-first audio_bed.profile은 {VISUAL_FIRST_AUDIO_PROFILE}여야 합니다.")
            if audio_bed.get("vocals") is not False:
                errors.append("visual-first audio_bed.vocals는 false여야 합니다.")
            if str(audio_bed.get("path") or "").strip() != VISUAL_FIRST_AUDIO_PATH:
                errors.append(f"visual-first audio_bed.path는 {VISUAL_FIRST_AUDIO_PATH}여야 합니다.")
        elif audio_bed.get("enabled") is not False:
            errors.append("continuous-flow v16 기본 audio_bed는 enabled=false여야 합니다.")
    if strict_v17_mid_cta:
        mid_target = errors if final else warnings
        configured_mid_cta = project.get("mid_cta")
        if not isinstance(configured_mid_cta, dict):
            mid_target.append("version 17 프로젝트에는 mid_cta 설정이 필요합니다.")
        else:
            mid_cta = mid_cta_config(project)
            mid_mode = str(mid_cta.get("mode") or "").strip().lower()
            if mid_mode not in MID_CTA_MODES:
                errors.append("mid_cta.mode는 auto, enabled, disabled 중 하나여야 합니다.")
            if str(mid_cta.get("placement") or "") != MID_CTA_PLACEMENT:
                errors.append(f"mid_cta.placement는 {MID_CTA_PLACEMENT}여야 합니다.")
            if str(mid_cta.get("style") or "") != MID_CTA_STYLE:
                errors.append(f"mid_cta.style은 {MID_CTA_STYLE}이어야 합니다.")
            if str(mid_cta.get("ui_target_profile") or "") != MID_CTA_UI_TARGET_PROFILE:
                errors.append(
                    f"mid_cta.ui_target_profile은 {MID_CTA_UI_TARGET_PROFILE}이어야 합니다."
                )
            if mid_cta.get("voice_enabled") is not True:
                errors.append("mid_cta.voice_enabled는 true여야 합니다.")
            if str(mid_cta.get("voice_delivery") or "") != "verdict":
                errors.append("mid_cta.voice_delivery는 verdict여야 합니다.")
            try:
                mid_min_duration = float(mid_cta.get("min_duration") or 0.0)
                mid_max_duration = float(mid_cta.get("max_duration") or 0.0)
                if mid_min_duration != MID_CTA_MIN_DURATION or mid_max_duration != MID_CTA_MAX_DURATION:
                    errors.append(
                        f"mid_cta 길이는 {MID_CTA_MIN_DURATION:.1f}-{MID_CTA_MAX_DURATION:.1f}초여야 합니다."
                    )
            except (TypeError, ValueError):
                errors.append("mid_cta min_duration과 max_duration은 숫자여야 합니다.")
            arrow_target = mid_cta.get("arrow_target")
            if not isinstance(arrow_target, dict):
                errors.append("mid_cta.arrow_target은 x와 y를 가진 객체여야 합니다.")
            else:
                try:
                    target_x = float(arrow_target.get("x"))
                    target_y = float(arrow_target.get("y"))
                    if not 0.18 <= target_x <= 0.50 or not 0.78 <= target_y <= 0.92:
                        errors.append("mid_cta.arrow_target은 Shorts 하단 왼쪽 목표 영역 안에 있어야 합니다.")
                except (TypeError, ValueError):
                    errors.append("mid_cta.arrow_target x와 y는 숫자여야 합니다.")
            for copy_key in ("ordinary_copy", "sensitive_copy"):
                copy = mid_cta.get(copy_key)
                if not isinstance(copy, dict):
                    errors.append(f"mid_cta.{copy_key}는 문구 객체여야 합니다.")
                    continue
                for field in ("headline", "emphasis", "subline", "narration"):
                    value = str(copy.get(field) or "").strip()
                    if not value:
                        errors.append(f"mid_cta.{copy_key}.{field}가 필요합니다.")
                    elif MID_CTA_UNVERIFIED_METRIC_PATTERN.search(value):
                        errors.append(
                            f"검증되지 않은 채널 지표 표현은 중간 CTA에 사용할 수 없습니다: {copy_key}.{field}"
                        )
            if mid_mode == "enabled":
                if delivery_mode != CONTINUOUS_FLOW_MODE:
                    errors.append("mid_cta.mode=enabled는 continuous-flow에서만 사용할 수 있습니다.")
                try:
                    if float(project.get("target_duration_seconds") or 0.0) < MID_CTA_MIN_BODY_SECONDS:
                        errors.append(
                            f"mid_cta.mode=enabled에는 목표 길이 {MID_CTA_MIN_BODY_SECONDS:.0f}초 이상이 필요합니다."
                        )
                except (TypeError, ValueError):
                    errors.append("target_duration_seconds는 숫자여야 합니다.")
    if brand_asset_path is not None and not brand_asset_path.is_file():
        errors.append(f"공통 인트로 자산이 없습니다: {brand_asset_path}")
    declared_companies: dict[str, dict[str, object]] = {}
    if strict_company_visuals:
        company_visuals = visual_sourcing.get("company_visuals")
        target = errors if final else warnings
        if not isinstance(company_visuals, dict):
            target.append("새 프로젝트에는 visual_sourcing.company_visuals 기록이 필요합니다.")
        else:
            if company_visuals.get("mentions_reviewed") is not True:
                target.append("기업명 등장 여부 검토를 완료하고 company_visuals.mentions_reviewed=true로 설정하세요.")
            companies = company_visuals.get("companies")
            if not isinstance(companies, list):
                target.append("company_visuals.companies는 핵심 기업 배열이어야 합니다.")
            else:
                known_scene_ids = {
                    str(scene.get("id") or f"scene-{index:02d}")
                    for index, scene in enumerate(scenes, start=1)
                    if isinstance(scene, dict)
                }
                for index, company in enumerate(companies, start=1):
                    if not isinstance(company, dict):
                        target.append(f"핵심 기업 기록은 객체여야 합니다: company-{index:02d}")
                        continue
                    name = str(company.get("name") or "").strip()
                    company_key = normalized_company_name(name)
                    scene_ids = company.get("scene_ids")
                    if not company_key:
                        target.append(f"이름이 없는 핵심 기업 기록: company-{index:02d}")
                        continue
                    if company_key in declared_companies:
                        target.append(f"중복 핵심 기업 기록: {name}")
                        continue
                    if not isinstance(scene_ids, list) or not scene_ids or not all(
                        str(value).strip() for value in scene_ids
                    ):
                        target.append(f"핵심 기업의 첫 주요 언급 scene_ids가 필요합니다: {name}")
                        continue
                    normalized_scene_ids = {str(value).strip() for value in scene_ids}
                    missing_company_scenes = normalized_scene_ids - known_scene_ids
                    if missing_company_scenes:
                        target.append(
                            f"핵심 기업이 존재하지 않는 장면을 참조합니다: {name}: {sorted(missing_company_scenes)}"
                        )
                    declared_companies[company_key] = {
                        "name": name,
                        "scene_ids": normalized_scene_ids,
                    }
    declared_people: dict[str, dict[str, object]] = {}
    if strict_editorial_grounding:
        grounding_target = errors if final else warnings
        grounding = project.get("editorial_grounding")
        if not isinstance(grounding, dict):
            grounding_target.append("새 프로젝트에는 editorial_grounding 기록이 필요합니다.")
        else:
            known_scene_ids = {
                str(scene.get("id") or f"scene-{index:02d}")
                for index, scene in enumerate(scenes, start=1)
                if isinstance(scene, dict)
            }
            scene_by_id = {
                str(scene.get("id") or f"scene-{index:02d}"): scene
                for index, scene in enumerate(scenes, start=1)
                if isinstance(scene, dict)
            }
            if grounding.get("locations_reviewed") is not True:
                grounding_target.append("기사의 핵심 지역명 등장 여부를 검토하고 locations_reviewed=true로 설정하세요.")
            locations = grounding.get("locations")
            if not isinstance(locations, list):
                grounding_target.append("editorial_grounding.locations는 핵심 지역 배열이어야 합니다.")
            else:
                seen_locations: set[str] = set()
                for index, location in enumerate(locations, start=1):
                    if not isinstance(location, dict):
                        grounding_target.append(f"핵심 지역 기록은 객체여야 합니다: location-{index:02d}")
                        continue
                    name = str(location.get("name") or "").strip()
                    location_key = normalized_company_name(name)
                    location_scene_ids = location.get("scene_ids")
                    if len(location_key) < 2:
                        grounding_target.append(f"이름이 없는 핵심 지역 기록: location-{index:02d}")
                        continue
                    if location_key in seen_locations:
                        grounding_target.append(f"중복 핵심 지역 기록: {name}")
                        continue
                    seen_locations.add(location_key)
                    if not isinstance(location_scene_ids, list) or not location_scene_ids:
                        grounding_target.append(f"핵심 지역의 첫 맥락 scene_ids가 필요합니다: {name}")
                        continue
                    normalized_scene_ids = {str(value).strip() for value in location_scene_ids if str(value).strip()}
                    missing_location_scenes = normalized_scene_ids - known_scene_ids
                    if missing_location_scenes:
                        grounding_target.append(
                            f"핵심 지역이 존재하지 않는 장면을 참조합니다: {name}: {sorted(missing_location_scenes)}"
                        )
                    location_copy = " ".join(
                        " ".join(
                            str(scene_by_id[scene_id].get(field) or "")
                            for field in ("eyebrow", "headline", "caption", "narration")
                        )
                        for scene_id in normalized_scene_ids
                        if scene_id in scene_by_id
                    )
                    if name not in location_copy:
                        grounding_target.append(
                            f"핵심 지역명은 지정한 첫 맥락 장면의 화면 또는 내레이션에 그대로 보여야 합니다: {name}"
                        )

            if grounding.get("people_reviewed") is not True:
                grounding_target.append("중앙 실명 인물 등장 여부를 검토하고 people_reviewed=true로 설정하세요.")
            people = grounding.get("people")
            if not isinstance(people, list):
                grounding_target.append("editorial_grounding.people은 중앙 인물 배열이어야 합니다.")
            else:
                for index, person in enumerate(people, start=1):
                    if not isinstance(person, dict):
                        grounding_target.append(f"중앙 인물 기록은 객체여야 합니다: person-{index:02d}")
                        continue
                    name = str(person.get("name") or "").strip()
                    person_key = normalized_company_name(name)
                    role = str(person.get("role") or "").strip()
                    visual_status = str(person.get("visual_status") or "").strip()
                    person_scene_ids = person.get("scene_ids")
                    raw_asset_path = str(person.get("asset_path") or "").strip()
                    asset_path = Path(raw_asset_path).as_posix() if raw_asset_path else ""
                    if len(person_key) < 2:
                        grounding_target.append(f"이름이 없는 중앙 인물 기록: person-{index:02d}")
                        continue
                    if person_key in declared_people:
                        grounding_target.append(f"중복 중앙 인물 기록: {name}")
                        continue
                    if role not in ALLOWED_PERSON_ROLES:
                        grounding_target.append(
                            f"지원하지 않는 인물 role입니다: {name}: {role or 'empty'}"
                        )
                    if visual_status not in ALLOWED_PERSON_VISUAL_STATUSES:
                        grounding_target.append(
                            f"중앙 인물 visual_status는 used, privacy_excluded, rights_blocked 중 하나여야 합니다: {name}"
                        )
                    if not isinstance(person_scene_ids, list) or not person_scene_ids:
                        grounding_target.append(f"중앙 인물의 첫 주요 언급 scene_ids가 필요합니다: {name}")
                        normalized_scene_ids = set()
                    else:
                        normalized_scene_ids = {
                            str(value).strip() for value in person_scene_ids if str(value).strip()
                        }
                        missing_person_scenes = normalized_scene_ids - known_scene_ids
                        if missing_person_scenes:
                            grounding_target.append(
                                f"중앙 인물이 존재하지 않는 장면을 참조합니다: {name}: {sorted(missing_person_scenes)}"
                            )
                    if visual_status == "used" and not asset_path:
                        grounding_target.append(f"실사진 사용 인물에는 asset_path가 필요합니다: {name}")
                    if visual_status != "used" and asset_path:
                        grounding_target.append(f"실사진을 제외한 인물은 asset_path를 비워두세요: {name}")
                    declared_people[person_key] = {
                        "name": name,
                        "role": role,
                        "scene_ids": normalized_scene_ids,
                        "visual_status": visual_status,
                        "asset_path": asset_path,
                    }

            accountability = grounding.get("accountability")
            if not isinstance(accountability, dict):
                grounding_target.append("editorial_grounding.accountability 기록이 필요합니다.")
            else:
                accountability_mode = str(accountability.get("mode") or "").strip()
                if accountability_mode not in ALLOWED_ACCOUNTABILITY_MODES:
                    grounding_target.append("accountability.mode는 verified 또는 not_applicable이어야 합니다.")
                elif accountability_mode == "verified":
                    trigger = str(accountability.get("trigger") or "").strip()
                    consequence = str(accountability.get("consequence") or "").strip()
                    accountability_claim_ids = accountability.get("claim_ids")
                    accountability_scene_ids = accountability.get("scene_ids")
                    if len(re.sub(r"\s+", "", trigger)) < 4:
                        grounding_target.append("검증된 분노·책임 포인트에는 구체적인 행위·누락 trigger가 필요합니다.")
                    if len(re.sub(r"\s+", "", consequence)) < 4:
                        grounding_target.append("검증된 분노·책임 포인트에는 시민 피해·신뢰 훼손 consequence가 필요합니다.")
                    if not isinstance(accountability_claim_ids, list) or not accountability_claim_ids:
                        grounding_target.append("검증된 분노·책임 포인트에는 fact-sheet claim_ids가 필요합니다.")
                    else:
                        missing_accountability_claims = {
                            str(value).strip() for value in accountability_claim_ids if str(value).strip()
                        } - known_claim_ids
                        if missing_accountability_claims:
                            grounding_target.append(
                                "분노·책임 포인트가 존재하지 않는 claim_ids를 참조합니다: "
                                f"{sorted(missing_accountability_claims)}"
                            )
                    if not isinstance(accountability_scene_ids, list) or not accountability_scene_ids:
                        grounding_target.append("검증된 분노·책임 포인트에는 impact scene_ids가 필요합니다.")
                    else:
                        normalized_accountability_scenes = {
                            str(value).strip() for value in accountability_scene_ids if str(value).strip()
                        }
                        missing_accountability_scenes = normalized_accountability_scenes - known_scene_ids
                        if missing_accountability_scenes:
                            grounding_target.append(
                                "분노·책임 포인트가 존재하지 않는 장면을 참조합니다: "
                                f"{sorted(missing_accountability_scenes)}"
                            )
                        accountability_copy = " ".join(
                            " ".join(
                                str(scene_by_id[scene_id].get(field) or "")
                                for field in ("eyebrow", "headline", "caption", "narration", "evidence_label", "evidence_value")
                            )
                            for scene_id in normalized_accountability_scenes
                            if scene_id in scene_by_id
                        )
                        if trigger and consequence and not has_shared_significant_term(
                            f"{trigger} {consequence}", accountability_copy
                        ):
                            grounding_target.append(
                                "검증된 행위·누락과 시민 피해가 지정한 장면의 화면 또는 내레이션에 드러나야 합니다."
                            )
                elif len(re.sub(r"\s+", "", str(accountability.get("reason") or ""))) < 8:
                    grounding_target.append(
                        "분노·책임 포인트가 없으면 not_applicable 판단 이유를 구체적으로 기록하세요."
                    )
    if style_template not in SUPPORTED_TEMPLATES:
        errors.append(f"지원하지 않는 영상 포맷입니다: {style_template}")
    if project_version >= 4:
        selection = project.get("format_selection")
        target = errors if final else warnings
        if not isinstance(selection, dict):
            target.append("새 프로젝트에는 format_selection 기록이 필요합니다.")
        else:
            selection_mode = str(selection.get("mode") or "").strip()
            selected_format = str(selection.get("selected") or "").strip()
            selection_reason = str(selection.get("reason") or "").strip()
            selection_confidence = str(selection.get("confidence") or "").strip()
            if selection_mode not in {"auto", "manual"}:
                target.append("format_selection.mode는 auto 또는 manual이어야 합니다.")
            if selected_format != style_template:
                target.append(
                    "format_selection.selected와 visual_style.template이 일치해야 합니다: "
                    f"{selected_format or 'empty'}/{style_template}"
                )
            if len(re.sub(r"\s+", "", selection_reason)) < 8:
                target.append("format_selection.reason에 뉴스 구조와 선택 근거를 구체적으로 적으세요.")
            if selection_confidence not in {"low", "medium", "high"}:
                target.append("format_selection.confidence는 low, medium, high 중 하나여야 합니다.")
            if selection_mode == "auto" and style_template == "fact-stack":
                usable_claims = [
                    claim
                    for claim in claims
                    if isinstance(claim, dict)
                    and str(claim.get("statement") or "").strip()
                    and str(claim.get("status") or "").strip() in {"confirmed", "attributed", "attributed_claim"}
                ]
                distinct_claims = {
                    re.sub(r"\s+", "", str(claim.get("statement") or ""))
                    for claim in usable_claims
                }
                if len(distinct_claims) < 3:
                    target.append(
                        "자동 선택한 fact-stack에는 서로 다른 검증 주장 3개 이상이 필요합니다. "
                        "quick-reveal로 낮추세요."
                    )
        cta_tail = project.get("cta_tail")
        if not isinstance(cta_tail, dict):
            target.append("새 프로젝트에는 공통 cta_tail 설정이 필요합니다.")
        else:
            if cta_tail.get("enabled") is not True:
                target.append("새 프로젝트의 공통 참여 CTA 테일은 enabled=true여야 합니다.")
            if not isinstance(cta_tail.get("keep_after_mid_cta", False), bool):
                errors.append("cta_tail.keep_after_mid_cta는 true 또는 false여야 합니다.")
            try:
                cta_duration = float(cta_tail.get("duration") or 0.0)
                if not MIN_CTA_TAIL_DURATION <= cta_duration <= MAX_CTA_TAIL_DURATION:
                    target.append(
                        f"cta_tail.duration은 {MIN_CTA_TAIL_DURATION:.1f}-{MAX_CTA_TAIL_DURATION:.1f}초여야 합니다."
                    )
                elif strict_v16_retention and cta_duration > DEFAULT_CTA_TAIL_DURATION:
                    target.append(
                        f"version 16 cta_tail.duration은 {DEFAULT_CTA_TAIL_DURATION:.1f}초 이하여야 합니다."
                    )
            except (TypeError, ValueError):
                target.append("cta_tail.duration은 숫자여야 합니다.")
            if not str(cta_tail.get("headline") or "").strip():
                target.append("cta_tail.headline이 필요합니다.")
            if not str(cta_tail.get("prompt") or "").strip():
                target.append("cta_tail.prompt가 필요합니다.")
            if cta_tail.get("voice_enabled") is False and not visual_first:
                target.append("공통 CTA 음성은 voice_enabled=true여야 합니다. 무음 렌더는 --no-tts로 지정하세요.")
            if visual_first and cta_tail.get("voice_enabled") is not False:
                target.append("visual-first CTA는 voice_enabled=false여야 합니다.")
            if project_version >= 8:
                if not str(cta_tail.get("narration") or "").strip():
                    target.append("cta_tail.narration이 필요합니다.")
                if not str(cta_tail.get("comment_headline") or "").strip():
                    target.append("cta_tail.comment_headline이 필요합니다.")
                comment_prompt = str(cta_tail.get("comment_prompt") or "").strip()
                if not comment_prompt:
                    target.append("cta_tail.comment_prompt가 필요합니다.")
                elif "댓글" not in comment_prompt:
                    target.append("cta_tail.comment_prompt에는 댓글 행동이 명확히 보여야 합니다.")
                comment_narration = str(cta_tail.get("comment_narration") or "").strip()
                if not comment_narration:
                    target.append("cta_tail.comment_narration이 필요합니다.")
                elif "여러분의 생각을 댓글로 남겨주세요" not in comment_narration:
                    target.append(
                        "cta_tail.comment_narration에는 "
                        "'여러분의 생각을 댓글로 남겨주세요'가 필요합니다."
                    )
    profile = shorts_profile_config(project)
    if style_template in RETENTION_TEMPLATES:
        target = errors if final else warnings
        hook_type = str(profile.get("hook_type") or storyboard.get("hook_type") or "").strip()
        if hook_type not in HOOK_TYPES:
            target.append(f"지원하지 않는 후크 유형입니다: {hook_type or 'empty'}")
        for field, label in (("hook", "선택한 후크"), ("open_loop", "오픈 루프"), ("payoff", "보상")):
            if not str(profile.get(field) or "").strip():
                target.append(f"집중 유지 프로필에 {label}가 없습니다.")
        if strict_quick_reveal:
            hook_stake = str(profile.get("hook_stake") or "").strip()
            first_scene = scenes[0] if isinstance(scenes[0], dict) else {}
            first_claim_ids = first_scene.get("claim_ids")
            first_frame_copy = " ".join(
                str(value or "").strip()
                for value in (
                    style.get("display_headline"),
                    first_scene.get("headline"),
                    first_scene.get("caption"),
                )
            )
            first_narration = str(first_scene.get("narration") or "").strip()
            first_source_audio = scene_uses_source_video_audio(first_scene)
            if len(re.sub(r"\s+", "", hook_stake)) < 8:
                target.append(
                    "새 퀵리빌은 shorts_profile.hook_stake에 첫 숫자·주장이 왜 중요한지 한 문장으로 적어야 합니다."
                )
            else:
                if not has_shared_significant_term(hook_stake, first_frame_copy):
                    target.append(
                        "퀵리빌 첫 화면이 hook_stake와 연결되지 않습니다. 숫자만 쓰지 말고 결과·공백·부담 등 의미를 함께 보여주세요."
                    )
                if (
                    not visual_first
                    and not first_source_audio
                    and not has_shared_significant_term(hook_stake, first_narration)
                ):
                    target.append(
                        "퀵리빌 첫 대사가 hook_stake를 설명하지 않습니다. 첫 문장부터 왜 중요한 숫자·주장인지 말하세요."
                    )
            if not isinstance(first_claim_ids, list) or not first_claim_ids:
                target.append("새 퀵리빌의 첫 장면에는 hook_stake를 뒷받침하는 claim_ids가 필요합니다.")
            else:
                missing_hook_claims = {str(value) for value in first_claim_ids} - known_claim_ids
                if missing_hook_claims:
                    errors.append(f"퀵리빌 첫 장면의 claim_ids가 존재하지 않습니다: {sorted(missing_hook_claims)}")
        if strict_early_retention:
            early_rehook = str(profile.get("midpoint_rehook") or "").strip()
            early_rehook_scene_id = str(profile.get("early_rehook_scene_id") or "").strip()
            withheld_detail = str(profile.get("withheld_detail") or "").strip()
            truth_guard = str(profile.get("truth_guard") or "").strip()
            payoff_text = str(profile.get("payoff") or "").strip()
            if len(re.sub(r"\s+", "", early_rehook)) < 8:
                target.append(
                    "10초 이탈 방지를 위해 midpoint_rehook에 새 사실을 하나 밝히면서 다음 답을 남기는 문장이 필요합니다."
                )
            if not early_rehook_scene_id:
                target.append("10초 이내 재후킹 장면을 early_rehook_scene_id로 지정하세요.")
            if len(re.sub(r"\s+", "", withheld_detail)) < 6:
                target.append(
                    "withheld_detail에는 초반에 바로 말하지 않고 결론까지 미룰 검증된 답의 일부를 적으세요."
                )
            if len(re.sub(r"\s+", "", truth_guard)) < 6:
                target.append(
                    "truth_guard에는 오해를 막기 위해 10초 안에 반드시 밝힐 조건·불확실성을 적으세요."
                )
            early_scene_by_id = {
                str(scene.get("id") or "").strip(): scene
                for scene in scenes
                if isinstance(scene, dict) and str(scene.get("id") or "").strip()
            }
            early_scene = early_scene_by_id.get(early_rehook_scene_id)
            if early_rehook_scene_id and early_scene is None:
                target.append("early_rehook_scene_id가 storyboard 장면과 연결되지 않습니다.")
            elif early_scene is not None:
                early_beat = str(early_scene.get("beat") or "").strip()
                if early_beat not in {"evidence", "turn", "impact", "rehook"}:
                    target.append(
                        "10초 이내 재후킹은 evidence, turn, impact, rehook 장면 중 하나여야 합니다."
                    )
                early_start = requested_scene_start_seconds(scenes, early_rehook_scene_id)
                if early_start is not None:
                    absolute_start = brand_intro_lead_in_seconds(project) + early_start
                    if absolute_start > EARLY_RETENTION_DEADLINE_SECONDS:
                        target.append(
                            "재후킹 시작이 인트로 포함 10초를 넘습니다: "
                            f"{absolute_start:.1f}/{EARLY_RETENTION_DEADLINE_SECONDS:.1f}초"
                        )
                early_claim_ids = early_scene.get("claim_ids")
                if not isinstance(early_claim_ids, list) or not early_claim_ids:
                    target.append("10초 이내 재후킹 장면에는 새 사실을 뒷받침하는 claim_ids가 필요합니다.")
                early_narration = str(early_scene.get("narration") or "").strip()
                early_visible_copy = " ".join(
                    str(early_scene.get(field) or "").strip()
                    for field in ("headline", "caption", "evidence_label", "evidence_value")
                )
                early_delivery_copy = early_visible_copy if visual_first else early_narration
                if early_rehook and not has_shared_significant_term(early_rehook, early_delivery_copy):
                    target.append(
                        "midpoint_rehook의 핵심 표현이 지정 장면 화면 또는 narration에 실제로 드러나지 않습니다."
                    )
                if early_rehook and payoff_text and text_similarity(early_rehook, payoff_text) >= 0.8:
                    target.append("10초 재후킹에서 결론을 전부 말하고 있습니다. 새 사실 하나만 밝히고 답의 일부는 남기세요.")
                early_index = scenes.index(early_scene)
                early_narration_prefix = " ".join(
                    " ".join(
                        str(scene.get(field) or "").strip()
                        for field in (
                            ("headline", "caption", "evidence_label", "evidence_value")
                            if visual_first
                            else ("narration",)
                        )
                    )
                    for scene in scenes[: early_index + 1]
                    if isinstance(scene, dict)
                )
                if truth_guard and not has_shared_significant_term(truth_guard, early_narration_prefix):
                    target.append(
                        "truth_guard의 조건·불확실성이 초반 화면 또는 narration에 없습니다. 궁금증 때문에 사실 조건을 숨길 수 없습니다."
                    )
            if withheld_detail and payoff_text and not has_shared_significant_term(withheld_detail, payoff_text):
                target.append("withheld_detail은 마지막 payoff에서 실제로 회수되는 답과 연결되어야 합니다.")
        if strict_v16_retention:
            scene_ids = {
                str(scene.get("id") or "").strip()
                for scene in scenes
                if isinstance(scene, dict) and str(scene.get("id") or "").strip()
            }
            first_answer_scene_id = str(profile.get("first_answer_scene_id") or "").strip()
            truth_guard_scene_id = str(profile.get("truth_guard_scene_id") or "").strip()
            truth_guard = str(profile.get("truth_guard") or "").strip()
            if not first_answer_scene_id:
                errors.append("version 16 shorts_profile.first_answer_scene_id가 필요합니다.")
            elif first_answer_scene_id not in scene_ids:
                errors.append("first_answer_scene_id가 storyboard 장면과 연결되지 않습니다.")
            else:
                first_answer_start = requested_scene_start_seconds(scenes, first_answer_scene_id)
                answer_deadline = (
                    VISUAL_FIRST_ANSWER_DEADLINE_SECONDS
                    if visual_first
                    else CONTINUOUS_FLOW_ANSWER_DEADLINE_SECONDS
                )
                if first_answer_start is not None:
                    first_answer_start += brand_intro_lead_in_seconds(project)
                    if first_answer_start > answer_deadline:
                        target.append(
                            "첫 답변 장면이 유지율 기준을 넘습니다: "
                            f"{first_answer_start:.1f}/{answer_deadline:.1f}초"
                        )
            if truth_guard:
                if not truth_guard_scene_id:
                    errors.append("truth_guard가 있으면 shorts_profile.truth_guard_scene_id가 필요합니다.")
                elif truth_guard_scene_id not in scene_ids:
                    errors.append("truth_guard_scene_id가 storyboard 장면과 연결되지 않습니다.")
                else:
                    truth_guard_start = requested_scene_start_seconds(scenes, truth_guard_scene_id)
                    if truth_guard_start is not None:
                        truth_guard_start += brand_intro_lead_in_seconds(project)
                        if truth_guard_start > TRUTH_GUARD_DEADLINE_SECONDS:
                            target.append(
                                "사실 조건 장면이 유지율 기준을 넘습니다: "
                                f"{truth_guard_start:.1f}/{TRUTH_GUARD_DEADLINE_SECONDS:.1f}초"
                            )
            if visual_first:
                if not VISUAL_FIRST_MIN_SCENES <= len(scenes) <= VISUAL_FIRST_MAX_SCENES:
                    errors.append(
                        "visual-first 장면 수는 "
                        f"{VISUAL_FIRST_MIN_SCENES}-{VISUAL_FIRST_MAX_SCENES}개여야 합니다."
                    )
                planned_body = sum(
                    max(1.0, float(scene.get("duration") or 0.0))
                    for scene in scenes
                    if isinstance(scene, dict)
                )
                cta_config = project.get("cta_tail")
                cta_seconds = (
                    float(cta_config.get("duration") or 0.0)
                    if isinstance(cta_config, dict) and cta_config.get("enabled") is True
                    else 0.0
                )
                planned_complete = planned_body + cta_seconds
                if not VISUAL_FIRST_MIN_DURATION_SECONDS <= planned_complete <= VISUAL_FIRST_MAX_DURATION_SECONDS:
                    target.append(
                        "visual-first 본문과 CTA 합계는 "
                        f"{VISUAL_FIRST_MIN_DURATION_SECONDS}-{VISUAL_FIRST_MAX_DURATION_SECONDS}초여야 합니다: "
                        f"{planned_complete:.1f}초"
                    )
                early_state_count = 0
                cursor = 0.0
                early_video = False
                for scene in scenes:
                    if not isinstance(scene, dict):
                        continue
                    if cursor < VISUAL_FIRST_EARLY_WINDOW_SECONDS:
                        early_state_count += 1
                        early_video = early_video or bool(str(scene.get("video") or "").strip())
                    cursor += max(1.0, float(scene.get("duration") or 0.0))
                if early_state_count < VISUAL_FIRST_MIN_EARLY_STATES and not early_video:
                    target.append(
                        "visual-first 첫 3초에는 서로 다른 화면 3개 또는 실제 video 장면이 필요합니다."
                    )
                for scene in scenes:
                    if not isinstance(scene, dict):
                        continue
                    scene_id = str(scene.get("id") or "unknown")
                    if str(scene.get("narration") or "").strip():
                        errors.append(f"visual-first narration은 비워야 합니다: {scene_id}")
                    if not str(scene.get("caption") or scene.get("headline") or "").strip():
                        errors.append(f"visual-first 화면 문구가 필요합니다: {scene_id}")
                    scene_claim_ids = scene.get("claim_ids")
                    if not isinstance(scene_claim_ids, list) or not scene_claim_ids:
                        errors.append(f"visual-first 장면에는 claim_ids가 필요합니다: {scene_id}")
        if style_template != "quick-reveal" and not str(profile.get("midpoint_rehook") or "").strip():
            target.append("집중 유지 프로필에 중간 재후킹이 없습니다.")
        if strict_fact_stack and style.get("show_fact_stack_index") is not True:
            target.append("새 팩트스택은 visual_style.show_fact_stack_index를 true로 설정해야 합니다.")
        storyboard_format = str(storyboard.get("format") or "").strip()
        if storyboard_format and storyboard_format != style_template:
            warnings.append(f"storyboard format과 visual_style.template이 다릅니다: {storyboard_format}/{style_template}")
        if strict_issue_lens:
            issue_focus = str(profile.get("issue_focus") or "").strip()
            viewer_stake = str(profile.get("viewer_stake") or "").strip()
            tension_question = str(profile.get("tension_question") or "").strip()
            visual_attention_device = str(profile.get("visual_attention_device") or "").strip()
            visual_attention_scene_id = str(profile.get("visual_attention_scene_id") or "").strip()
            visual_attention_reason = str(profile.get("visual_attention_reason") or "").strip()
            first_scene = scenes[0] if isinstance(scenes[0], dict) else {}
            first_frame_copy = " ".join(
                str(value or "").strip()
                for value in (
                    style.get("display_headline"),
                    first_scene.get("headline"),
                    first_scene.get("caption"),
                )
            )
            first_narration = str(first_scene.get("narration") or "").strip()
            first_source_audio = scene_uses_source_video_audio(first_scene)
            hook_text = str(profile.get("hook") or "").strip()
            payoff_text = str(profile.get("payoff") or "").strip()

            if strict_citizen_question:
                first_visible_questions = (
                    style.get("display_headline"),
                    first_scene.get("headline"),
                    first_scene.get("caption"),
                )
                if not ends_with_question(hook_text):
                    target.append("새 프로젝트의 선택한 hook은 시민 관점의 구체적인 질문으로 끝나야 합니다.")
                if not visual_first and not first_source_audio and not ends_with_question(first_narration):
                    target.append("새 프로젝트의 첫 내레이션은 설명이 아니라 훅 질문 한 문장으로 끝나야 합니다.")
                if not any(ends_with_question(value) for value in first_visible_questions):
                    target.append("새 프로젝트의 첫 화면 headline 또는 caption에는 훅 질문이 보여야 합니다.")
                if not visual_first and not first_source_audio and is_summary_lead(first_narration):
                    target.append("첫 장면을 뉴스 요약·소식 소개로 시작하지 말고 시민의 의문을 바로 물으세요.")
                if not has_citizen_stake(
                    f"{viewer_stake} {hook_text} "
                    f"{first_frame_copy if visual_first or first_source_audio else first_narration}"
                ):
                    target.append(
                        "viewer_stake와 첫 훅에는 시민·소비자의 생활, 비용, 안전, 권리 중 하나가 구체적으로 보여야 합니다."
                    )
                if tension_question and not has_shared_significant_term(tension_question, hook_text):
                    target.append("선택한 hook은 시민 관점의 tension_question을 그대로 이어가야 합니다.")

            if len(re.sub(r"\s+", "", issue_focus)) < 10:
                target.append(
                    "새 프로젝트는 shorts_profile.issue_focus에 행정 절차가 아닌 검증된 핵심 모순·실패한 기대를 적어야 합니다."
                )
            if len(re.sub(r"\s+", "", viewer_stake)) < 8:
                target.append(
                    "새 프로젝트는 shorts_profile.viewer_stake에 비용·불편·위험·공백·형평성 등 시청자 이해관계를 적어야 합니다."
                )
            if len(re.sub(r"\s+", "", tension_question)) < 8:
                target.append(
                    "새 프로젝트는 shorts_profile.tension_question에 주제·모순이 보이는 구체적 반문을 적어야 합니다."
                )
            else:
                normalized_question = re.sub(r"[^0-9A-Za-z가-힣]", "", tension_question.lower())
                if not re.search(r"[?？]\s*$", tension_question):
                    target.append("tension_question은 시청자가 바로 이해할 수 있는 질문형으로 끝나야 합니다.")
                if normalized_question in GENERIC_TENSION_QUESTIONS:
                    target.append(
                        "tension_question이 너무 추상적입니다. '이게 맞나?'대신 대상·해법·남은 문제를 직접 물으세요."
                    )
                if issue_focus and viewer_stake and not has_shared_significant_term(
                    f"{issue_focus} {viewer_stake}", tension_question
                ):
                    target.append(
                        "tension_question이 핵심 모순·시청자 영향과 연결되지 않습니다. 절차 현황이 아닌 실제 해법의 타당성을 물으세요."
                    )
            if issue_focus:
                if not has_shared_significant_term(issue_focus, hook_text):
                    target.append("선택한 hook이 issue_focus의 핵심 모순을 직접 드러내지 않습니다.")
                if not has_shared_significant_term(issue_focus, first_frame_copy):
                    target.append("첫 화면이 issue_focus와 연결되지 않습니다. 절차가 아닌 핵심 모순을 보여주세요.")
                if (
                    not visual_first
                    and not first_source_audio
                    and not has_shared_significant_term(issue_focus, first_narration)
                ):
                    target.append("첫 대사가 issue_focus와 연결되지 않습니다. 첫 문장부터 이상한 지점을 말하세요.")
            if viewer_stake and not has_shared_significant_term(
                viewer_stake, f"{hook_text} {first_frame_copy} {first_narration}"
            ):
                target.append("훅과 첫 장면에 viewer_stake의 비용·불편·위험·공백·형평성이 보이지 않습니다.")
            if issue_focus and payoff_text and not has_shared_significant_term(
                f"{issue_focus} {viewer_stake}", payoff_text
            ):
                target.append("payoff가 처음에 이슈화한 핵심 모순·시청자 영향을 회수하지 않습니다.")

            if visual_attention_device not in ALLOWED_VISUAL_ATTENTION_DEVICES:
                target.append(
                    "visual_attention_device는 reaction-meme, contrast-composite, consequence-photo, "
                    "evidence-closeup, motion-proof 중 하나여야 합니다."
                )
            if len(re.sub(r"\s+", "", visual_attention_reason)) < 8:
                target.append("시선 장치가 핵심 모순을 어떻게 강화하는지 visual_attention_reason에 적으세요.")
            scene_by_id = {
                str(scene.get("id") or "").strip(): scene
                for scene in scenes
                if isinstance(scene, dict) and str(scene.get("id") or "").strip()
            }
            attention_scene = scene_by_id.get(visual_attention_scene_id)
            if attention_scene is None:
                target.append("유효한 visual_attention_scene_id로 훅·재후킹·반전·영향 장면을 지정하세요.")
            else:
                attention_beat = str(attention_scene.get("beat") or "").strip()
                attention_role = str(attention_scene.get("visual_role") or "evidence").strip()
                if not str(attention_scene.get("image") or attention_scene.get("video") or "").strip():
                    target.append(f"시선 장치 장면에 image 또는 video가 필요합니다: {visual_attention_scene_id}")
                if visual_attention_device == "reaction-meme":
                    if project.get("sensitive_topic") is True:
                        target.append("민감 뉴스에는 visual_attention_device로 reaction-meme을 선택할 수 없습니다.")
                    if attention_role != "reaction-meme":
                        target.append("반응 밈 시선 장치 장면은 visual_role=reaction-meme이어야 합니다.")
                elif attention_beat not in VISUAL_ATTENTION_BEATS:
                    target.append(
                        "밈 이외의 시선 장치는 hook, rehook, turn, impact 장면 중 하나에 배치하세요: "
                        f"{visual_attention_scene_id}: {attention_beat or 'empty'}"
                    )
                if visual_attention_device == "motion-proof" and not str(attention_scene.get("video") or "").strip():
                    target.append("motion-proof 시선 장치는 실제 video 클립 장면을 지정해야 합니다.")

    manifest_paths = {
        Path(str(asset.get("path") or "")).as_posix()
        for asset in assets
        if isinstance(asset, dict) and asset.get("path")
    }
    valid_searches: list[dict] = []
    for index, search in enumerate(searches, start=1):
        if not isinstance(search, dict):
            errors.append(f"시각 자료 검색 기록은 객체여야 합니다: search-{index:02d}")
            continue
        valid_searches.append(search)
        search_id = search.get("id") or f"search-{index:02d}"
        target = errors if final else warnings
        if not str(search.get("query") or "").strip():
            target.append(f"query가 없는 시각 자료 검색 기록: {search_id}")
        if not str(search.get("searched_at") or "").strip():
            target.append(f"searched_at이 없는 시각 자료 검색 기록: {search_id}")
        scene_ids = search.get("scene_ids")
        if not isinstance(scene_ids, list) or not scene_ids or not all(str(value).strip() for value in scene_ids):
            target.append(f"scene_ids가 없는 시각 자료 검색 기록: {search_id}")
        outcome = str(search.get("outcome") or "").strip()
        if outcome not in ALLOWED_SEARCH_OUTCOMES:
            target.append(f"지원하지 않는 시각 자료 검색 outcome: {search_id}: {outcome or 'empty'}")
        selected = Path(str(search.get("selected_asset_path") or "")).as_posix()
        if outcome == "collected" and (not selected or selected not in manifest_paths):
            target.append(f"수집 자산과 연결되지 않은 시각 자료 검색 기록: {search_id}")
        if outcome in {"generated", "no_usable_asset"} and not str(search.get("note") or "").strip():
            target.append(f"판단 메모가 없는 시각 자료 검색 기록: {search_id}")

    invalid_sources = [item for item in sources if not isinstance(item, dict)]
    if invalid_sources:
        errors.append("sources.json의 각 source는 객체여야 합니다.")
    sources = [item for item in sources if isinstance(item, dict)]
    source_ids = {str(item.get("id")) for item in sources if item.get("id")}
    source_origins: set[str] = set()
    for item in sources:
        source_url = str(item.get("url") or "")
        origin = parse.urlsplit(source_url).netloc.lower().removeprefix("www.")
        if origin:
            source_origins.add(origin)
        elif item.get("publisher"):
            source_origins.add(str(item["publisher"]).strip().lower())
        if source_url and parse.urlsplit(source_url).scheme not in {"http", "https"}:
            errors.append(f"지원하지 않는 source URL: {source_url}")
        if not item.get("publisher"):
            warnings.append(f"publisher가 비어 있습니다: {item.get('id', 'unknown')}")
        if not item.get("published_at"):
            warnings.append(f"published_at이 비어 있습니다: {item.get('id', 'unknown')}")
    required_source_count = 3 if project.get("sensitive_topic") else 2
    if len(source_origins) < required_source_count:
        message = f"독립 출처가 부족합니다: {len(source_origins)}/{required_source_count}"
        (errors if final else warnings).append(message)

    if not claims:
        (errors if final else warnings).append("fact-sheet.json에 검증된 주장이 없습니다.")
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("fact-sheet.json의 각 claim은 객체여야 합니다.")
            continue
        statement = str(claim.get("statement") or "").strip()
        linked = {str(value) for value in claim.get("source_ids", [])}
        if not statement:
            errors.append(f"내용이 없는 주장: {claim.get('id', 'unknown')}")
        if not linked:
            (errors if final else warnings).append(f"출처가 없는 주장: {claim.get('id', 'unknown')}")
        missing = linked - source_ids
        if missing:
            errors.append(f"존재하지 않는 source ID 참조: {claim.get('id', 'unknown')}: {sorted(missing)}")
        if final and project.get("sensitive_topic") and claim.get("status") == "confirmed" and len(linked) < 2:
            errors.append(f"민감 뉴스의 confirmed 주장은 두 출처가 필요합니다: {claim.get('id', 'unknown')}")

    screen_copy_mode = str(style.get("screen_copy_mode") or "").strip()
    screen_copy_target = errors if final else warnings
    if screen_copy_mode == SCREEN_COPY_MODE_NOUN_PHRASES:
        for issue in screen_copy_issues("display_headline", style.get("display_headline")):
            screen_copy_target.append(f"명사형 화면 문구 규칙: {issue}")

    planned_total = 0.0
    synthetic_used = False
    storyboard_has_visuals = False
    used_real_news_photo = False
    real_media_scene_count = 0
    visual_scene_count = 0
    validated_asset_paths: set[str] = set()
    used_asset_kinds: set[str] = set()
    image_motions: list[str] = []
    important_beat_motions: list[str] = []
    zoom_scene_count = 0
    still_scene_count = 0
    reaction_meme_count = 0
    consecutive_zoom_count = 0
    max_consecutive_zoom_count = 0
    visual_sequence: list[str] = []
    synthetic_scene_flags: list[bool] = []
    used_company_visuals: set[str] = set()
    used_person_visuals: set[str] = set()
    used_images: dict[str, str] = {}
    seen_beats: set[str] = set()
    scene_duration_limits = {
        "quick-reveal": 4.0,
        "fact-stack": 4.0,
        "story-explainer": 4.0,
        "broadcast-card": 6.0,
    }
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            errors.append(f"장면은 객체여야 합니다: scene-{index:02d}")
            continue
        scene_id = scene.get("id") or f"scene-{index:02d}"
        if not str(scene.get("headline") or "").strip():
            errors.append(f"headline이 없습니다: {scene_id}")
        if not str(scene.get("caption") or scene.get("narration") or "").strip():
            errors.append(f"caption 또는 narration이 필요합니다: {scene_id}")
        caption = str(scene.get("caption") or scene.get("ticker") or "").strip()
        if style_template in RETENTION_TEMPLATES and len(caption) > 42:
            warnings.append(f"한 화면 자막이 깁니다: {scene_id}: {len(caption)}자")
        scene_editorial_text = " ".join(
            str(scene.get(field) or "").strip()
            for field in (
                "eyebrow",
                "headline",
                "caption",
                "payoff_title",
                "payoff_detail",
                "payoff_punch",
                "discussion_prompt",
                "narration",
            )
        )
        if UNSTABLE_RELATIVE_TIME_PATTERN.search(scene_editorial_text):
            warnings.append(
                f"게시일에 따라 틀리는 상대 시행 시점 문구가 있습니다: {scene_id}. "
                "실제 게시 일정이 확정되지 않았다면 '시행 중', '이제 시행' 또는 검증된 절대 시점을 사용하세요."
            )
        if IMMEDIATE_TOW_PATTERN.search(scene_editorial_text):
            warnings.append(
                f"신고 직후 자동 견인으로 오해할 수 있는 문구가 있습니다: {scene_id}. "
                "출처가 즉시 견인을 명시하지 않았다면 이동 권고·불응·지자체 요청 조건을 유지하세요."
            )
        if screen_copy_mode == SCREEN_COPY_MODE_NOUN_PHRASES:
            for field in (
                "eyebrow",
                "headline",
                "headline_highlight",
                "caption",
                "caption_focus",
                "evidence_label",
                "evidence_value",
                "payoff_title",
                "payoff_detail",
                "payoff_punch",
                "payoff_callback",
                "discussion_prompt",
            ):
                for issue in screen_copy_issues(field, scene.get(field)):
                    screen_copy_target.append(f"명사형 화면 문구 규칙: {scene_id}: {issue}")
        caption_focus = str(scene.get("caption_focus") or "").strip()
        if caption_focus and caption_focus not in caption:
            errors.append(f"caption_focus는 caption에 포함된 정확한 문구여야 합니다: {scene_id}")
        beat = str(scene.get("beat") or "").strip()
        voice_delivery = str(scene.get("voice_delivery") or "auto").strip().lower()
        if voice_delivery not in TYPECAST_DELIVERY_PROFILES:
            errors.append(
                f"voice_delivery는 auto, contrast, verdict 중 하나여야 합니다: {scene_id}"
            )
        visual_role = str(scene.get("visual_role") or "evidence").strip()
        if visual_role not in ALLOWED_VISUAL_ROLES:
            (errors if final else warnings).append(
                f"지원하지 않는 visual_role: {scene_id}: {visual_role or 'empty'}"
            )
        if visual_role == "reaction-meme":
            reaction_meme_count += 1
            target = errors if final else warnings
            if project.get("sensitive_topic") is True:
                target.append(f"민감 뉴스에는 reaction-meme을 사용할 수 없습니다: {scene_id}")
            if beat not in REACTION_MEME_BEATS:
                target.append(
                    f"reaction-meme은 context 또는 rehook 장면에만 사용할 수 있습니다: {scene_id}: {beat}"
                )
            if str(scene.get("fact_index") or "").strip():
                target.append(f"reaction-meme은 팩트 증거 번호를 가질 수 없습니다: {scene_id}")
        if style_template in RETENTION_TEMPLATES:
            if beat not in SCENE_BEATS:
                (errors if final else warnings).append(f"지원하지 않는 집중 유지 beat: {scene_id}: {beat or 'empty'}")
            else:
                seen_beats.add(beat)
            if style.get("show_source_label") is True:
                target = errors if final else warnings
                source_label = str(scene.get("source_label") or "").strip()
                linked_scene_sources = scene.get("source_ids")
                if not source_label:
                    target.append(f"작은 뉴스 출처 표시가 없습니다: {scene_id}")
                if not isinstance(linked_scene_sources, list) or not linked_scene_sources:
                    target.append(f"뉴스 출처 source_ids가 없습니다: {scene_id}")
                else:
                    missing_scene_sources = {str(value) for value in linked_scene_sources} - source_ids
                    if missing_scene_sources:
                        errors.append(
                            f"존재하지 않는 뉴스 출처 source ID 참조: {scene_id}: {sorted(missing_scene_sources)}"
                        )
            if strict_story_flow and beat != "loop":
                story_link = scene.get("story_link")
                target = errors if final else warnings
                if not isinstance(story_link, dict):
                    target.append(f"장면 연결을 설명하는 story_link가 필요합니다: {scene_id}")
                else:
                    answers = str(story_link.get("answers") or "").strip()
                    next_gap = str(story_link.get("next_gap") or "").strip()
                    if beat == "hook":
                        if not next_gap:
                            target.append(f"hook story_link.next_gap이 필요합니다: {scene_id}")
                    elif beat == "payoff":
                        if not answers:
                            target.append(f"payoff story_link.answers가 필요합니다: {scene_id}")
                        if next_gap:
                            target.append(f"payoff는 새 궁금증을 남기지 않아야 합니다: {scene_id}")
                    else:
                        if not answers:
                            target.append(f"이전 장면을 잇는 story_link.answers가 필요합니다: {scene_id}")
                        if not next_gap:
                            target.append(f"다음 장면으로 넘길 story_link.next_gap이 필요합니다: {scene_id}")
        try:
            scene_duration = max(0.0, float(scene.get("duration") or 0.0))
            planned_total += scene_duration
            limit = scene_duration_limits.get(style_template)
            if limit is not None and scene_duration > limit:
                warnings.append(f"{style_template} 장면이 {limit:.0f}초를 넘습니다: {scene_id}: {scene_duration:.1f}초")
        except (TypeError, ValueError):
            errors.append(f"duration이 숫자가 아닙니다: {scene_id}")
        if strict_continuous_flow and str(scene.get("audio") or "").strip():
            errors.append(
                f"continuous-flow에서는 장면별 audio를 사용할 수 없습니다: {scene_id}"
            )
        image = str(scene.get("image") or "").strip()
        video = str(scene.get("video") or "").strip()
        audio_mode = scene_audio_mode(scene)
        if audio_mode not in ALLOWED_SCENE_AUDIO_MODES:
            errors.append(
                f"audio_mode은 narration 또는 source-video여야 합니다: {scene_id}: {audio_mode or 'empty'}"
            )
        if audio_mode == SOURCE_VIDEO_AUDIO_MODE and not video:
            errors.append(f"source-video audio_mode에는 video 자산이 필요합니다: {scene_id}")
        if "external_caption" in scene and not isinstance(scene.get("external_caption"), bool):
            errors.append(f"external_caption은 불리언이어야 합니다: {scene_id}")
        if "render_text_overlay" in scene and not isinstance(scene.get("render_text_overlay"), bool):
            errors.append(f"render_text_overlay는 불리언이어야 합니다: {scene_id}")
        if image and video:
            errors.append(f"image와 video를 동시에 지정할 수 없습니다: {scene_id}")
        if image:
            normalized_image = Path(image).as_posix()
            previous_scene_id = used_images.get(normalized_image)
            if previous_scene_id:
                errors.append(
                    "같은 이미지를 다시 사용할 수 없습니다: "
                    f"{previous_scene_id}/{scene_id}: {normalized_image}"
                )
            else:
                used_images[normalized_image] = str(scene_id)
        if image and style_template in RETENTION_TEMPLATES:
            still_scene_count += 1
            image_fit = str(scene.get("image_fit") or "auto").strip().lower()
            if image_fit not in ALLOWED_IMAGE_FITS:
                errors.append(f"지원하지 않는 image_fit: {scene_id}: {image_fit or 'empty'}")
            motion_default = "none" if strict_story_flow else "zoom-in"
            motion = str(scene.get("motion") or motion_default).strip()
            normalized_motion = "zoom-in" if motion == "slow-zoom" else motion
            if motion not in ALLOWED_IMAGE_MOTIONS:
                errors.append(f"지원하지 않는 image motion: {scene_id}: {motion or 'empty'}")
            else:
                image_motions.append(normalized_motion)
                if beat in {"hook", "turn", "impact", "payoff"}:
                    important_beat_motions.append(normalized_motion)
                if normalized_motion in {"zoom-in", "zoom-out"}:
                    zoom_scene_count += 1
                    consecutive_zoom_count += 1
                    max_consecutive_zoom_count = max(max_consecutive_zoom_count, consecutive_zoom_count)
                else:
                    consecutive_zoom_count = 0
            for field in ("focus_x", "focus_y"):
                try:
                    focus = float(scene.get(field, 0.5))
                    if not 0.0 <= focus <= 1.0:
                        errors.append(f"{field}는 0에서 1 사이여야 합니다: {scene_id}: {focus}")
                except (TypeError, ValueError):
                    errors.append(f"{field}가 숫자가 아닙니다: {scene_id}")
            try:
                zoom_scale = float(scene.get("zoom_scale", 1.0 if strict_story_flow else 1.055))
                if not 1.0 <= zoom_scale <= 1.25:
                    errors.append(f"zoom_scale은 1.0에서 1.25 사이여야 합니다: {scene_id}: {zoom_scale}")
                elif normalized_motion == "none" and zoom_scale != 1.0:
                    warnings.append(f"motion이 none이라 zoom_scale이 적용되지 않습니다: {scene_id}")
                elif normalized_motion in {"zoom-in", "zoom-out"} and strict_story_flow and zoom_scale <= 1.0:
                    (errors if final else warnings).append(
                        f"강조 줌에는 1.0보다 큰 zoom_scale이 필요합니다: {scene_id}"
                    )
            except (TypeError, ValueError):
                errors.append(f"zoom_scale이 숫자가 아닙니다: {scene_id}")
            motion_start = scene.get("motion_start")
            motion_duration = scene.get("motion_duration")
            motion_emphasis = str(scene.get("motion_emphasis") or "").strip()
            if normalized_motion in {"zoom-in", "zoom-out"} and strict_story_flow:
                target = errors if final else warnings
                try:
                    motion_start_value = float(motion_start)
                    motion_duration_value = float(motion_duration)
                    planned_scene_duration = max(0.0, float(scene.get("duration") or 0.0))
                    if motion_start_value < 0:
                        target.append(f"motion_start는 0 이상이어야 합니다: {scene_id}")
                    if not MIN_MOTION_DURATION <= motion_duration_value <= MAX_MOTION_DURATION:
                        target.append(
                            f"motion_duration은 {MIN_MOTION_DURATION:.2f}-{MAX_MOTION_DURATION:.1f}초여야 합니다: "
                            f"{scene_id}: {motion_duration_value:.2f}"
                        )
                    if planned_scene_duration and motion_start_value + motion_duration_value > planned_scene_duration + 0.01:
                        target.append(
                            f"강조 줌 구간이 장면 길이를 넘습니다: {scene_id}: "
                            f"{motion_start_value + motion_duration_value:.2f}/{planned_scene_duration:.2f}초"
                        )
                except (TypeError, ValueError):
                    target.append(f"강조 줌에는 숫자 motion_start와 motion_duration이 필요합니다: {scene_id}")
                if len(re.sub(r"\s+", "", motion_emphasis)) < 2:
                    target.append(f"강조 줌에는 motion_emphasis가 필요합니다: {scene_id}")
                else:
                    emphasis_context = " ".join(
                        str(scene.get(field) or "")
                        for field in ("narration", "caption", "evidence_label", "evidence_value")
                    )
                    if not has_shared_significant_term(motion_emphasis, emphasis_context):
                        target.append(
                            f"motion_emphasis가 대사나 화면 근거와 연결되지 않습니다: {scene_id}: {motion_emphasis}"
                        )
            elif normalized_motion == "none" and strict_story_flow:
                if motion_emphasis or motion_start not in (None, 0, 0.0, "") or motion_duration not in (None, 0, 0.0, ""):
                    warnings.append(f"motion이 none인 장면의 강조 줌 필드는 비워두세요: {scene_id}")
        elif style_template in RETENTION_TEMPLATES:
            consecutive_zoom_count = 0
        if video and style_template not in RETENTION_TEMPLATES:
            errors.append(f"video 장면은 신규 집중 유지 포맷에서만 지원합니다: {scene_id}")
        video_start = 0.0
        if video:
            try:
                video_start = float(scene.get("video_start") or 0.0)
                if video_start < 0:
                    errors.append(f"video_start는 0 이상이어야 합니다: {scene_id}")
            except (TypeError, ValueError):
                errors.append(f"video_start가 숫자가 아닙니다: {scene_id}")
        visual = video or image
        if style_template in RETENTION_TEMPLATES and not visual:
            (errors if final else warnings).append(f"실제 image 또는 video 자산이 없는 장면: {scene_id}")
        visual_sequence.append(visual)
        if visual:
            storyboard_has_visuals = True
            visual_scene_count += 1
            visual_path: Path | None = None
            try:
                visual_path = resolve_project_file(project_dir, visual)
                if video:
                    video_info = probe_video(visual_path)
                    if not video_info["has_video"]:
                        errors.append(f"영상 스트림이 없는 video 자산: {video}")
                    elif audio_mode == SOURCE_VIDEO_AUDIO_MODE and not video_info["has_audio"]:
                        errors.append(f"source-video audio_mode인데 오디오 스트림이 없습니다: {scene_id}: {video}")
                    elif video_start >= video_info["duration"]:
                        errors.append(f"video_start가 클립 길이 이상입니다: {scene_id}: {video_start:.1f}/{video_info['duration']:.1f}초")
            except News2ShortsError as exc:
                errors.append(str(exc))
            record = rights_record_for(manifest, visual)
            if record is None:
                (errors if final else warnings).append(f"권리 기록이 없는 시각 자산: {visual}")
            else:
                target = errors if final else warnings
                kind = str(record.get("kind") or "").strip()
                media_type = str(record.get("media_type") or "").strip()
                raw_company_names = record.get("company_names") or []
                company_names: list[str] = []
                if not isinstance(raw_company_names, list):
                    target.append(f"company_names는 배열이어야 합니다: {visual}")
                else:
                    company_names = [str(value).strip() for value in raw_company_names if str(value).strip()]
                company_visual_type = str(record.get("company_visual_type") or "").strip()
                if company_visual_type and not company_names:
                    target.append(f"기업 시각자료에는 company_names가 필요합니다: {visual}")
                if company_names:
                    if company_visual_type not in ALLOWED_COMPANY_VISUAL_TYPES:
                        target.append(
                            "company_visual_type은 logo, official-image, licensed-photo, branded-product, "
                            f"facility-signage 중 하나여야 합니다: {visual}"
                        )
                    if record.get("company_identity_reviewed") is not True:
                        target.append(f"기업 식별 육안 검수가 완료되지 않은 시각 자산: {visual}")
                    if kind == "generated" or record.get("synthetic") is True:
                        target.append(f"기업 로고·브랜드 이미지는 생성형 이미지로 대체할 수 없습니다: {visual}")
                    for company_name in company_names:
                        company_key = normalized_company_name(company_name)
                        declared_company = declared_companies.get(company_key)
                        if declared_company and str(scene_id) in declared_company["scene_ids"]:
                            used_company_visuals.add(company_key)
                raw_person_names = record.get("person_names") or []
                person_names: list[str] = []
                if not isinstance(raw_person_names, list):
                    target.append(f"person_names는 배열이어야 합니다: {visual}")
                else:
                    person_names = [str(value).strip() for value in raw_person_names if str(value).strip()]
                if person_names:
                    if record.get("person_identity_reviewed") is not True:
                        target.append(f"인물 식별 육안 검수가 완료되지 않은 시각 자산: {visual}")
                    if kind == "generated" or record.get("synthetic") is True:
                        target.append(f"실명 인물은 생성형 이미지로 대체할 수 없습니다: {visual}")
                    for person_name in person_names:
                        person_key = normalized_company_name(person_name)
                        declared_person = declared_people.get(person_key)
                        if (
                            declared_person
                            and declared_person["visual_status"] == "used"
                            and declared_person["asset_path"] == Path(visual).as_posix()
                            and str(scene_id) in declared_person["scene_ids"]
                        ):
                            used_person_visuals.add(person_key)
                if visual not in validated_asset_paths:
                    validated_asset_paths.add(visual)
                    if kind:
                        used_asset_kinds.add(kind)
                    if not record.get("approved"):
                        target.append(f"권리 승인이 완료되지 않은 시각 자산: {visual}")
                    if kind not in ALLOWED_ASSET_KINDS:
                        target.append(f"지원하지 않는 자산 kind: {visual}: {kind or 'empty'}")
                    if kind == "unreviewed":
                        if record.get("approved") is not False:
                            errors.append(f"unreviewed 자산은 approved=false여야 합니다: {visual}")
                        if record.get("local_review_only") is not True:
                            errors.append(f"unreviewed 자산은 local_review_only=true여야 합니다: {visual}")
                        if not is_http_url(str(record.get("source_url") or "")):
                            errors.append(f"unreviewed 자산에도 canonical source_url이 필요합니다: {visual}")
                        permission_status = str(record.get("permission_status") or "unknown").strip()
                        if permission_status not in {"unknown", "review_required"}:
                            errors.append(
                                f"unreviewed 자산 permission_status는 unknown 또는 review_required여야 합니다: {visual}"
                            )
                        if record.get("whiteboard_text_free_reviewed") not in {True, False}:
                            errors.append(
                                f"unreviewed 자산에는 whiteboard_text_free_reviewed 불리언이 필요합니다: {visual}"
                            )
                    if strict_real_media_majority and media_type not in ALLOWED_MEDIA_TYPES:
                        target.append(
                            "새 프로젝트 시각 자산에는 media_type이 필요합니다: "
                            f"{visual}: {media_type or 'empty'}"
                        )
                    if strict_real_media_majority and video and media_type != "video":
                        target.append(f"video 장면의 media_type은 video여야 합니다: {visual}")
                    if strict_real_media_majority and image and media_type == "video":
                        target.append(f"image 장면의 media_type은 video일 수 없습니다: {visual}")
                    if visual_role == "reaction-meme":
                        usage_role = str(record.get("usage_role") or "").strip()
                        meme_origin = str(record.get("meme_origin") or "").strip()
                        if usage_role != "reaction-meme":
                            target.append(f"밈 자산에는 usage_role=reaction-meme 기록이 필요합니다: {visual}")
                        if meme_origin not in ALLOWED_MEME_ORIGINS:
                            target.append(
                                f"밈 자산 meme_origin은 licensed, owned, original 중 하나여야 합니다: {visual}"
                            )
                        if kind not in {"licensed", "owned", "generated"}:
                            target.append(f"밈 자산은 licensed, owned, generated만 허용합니다: {visual}")
                    if not str(record.get("retrieved_at") or "").strip():
                        target.append(f"retrieved_at이 없는 시각 자산: {visual}")
                    if korean_visuals_required:
                        if str(record.get("visual_locale") or "").strip() != DEFAULT_VISUAL_LOCALE:
                            errors.append(f"한국 이미지 전용 장면의 visual_locale은 ko-KR이어야 합니다: {visual}")
                        if record.get("korean_context_reviewed") is not True:
                            errors.append(f"한국 배경 육안 검수가 완료되지 않은 시각 자산: {visual}")
                        if len(str(record.get("korean_context_note") or "").strip()) < 12:
                            errors.append(
                                "한국어 표지판·국내 도로·건축·차량 환경 등 한국 배경 근거가 필요합니다: "
                                f"{visual}"
                            )
                    elif international_visuals_enabled:
                        assert isinstance(international_visuals, dict)
                        asset_locale = str(record.get("visual_locale") or "").strip()
                        source_locale = str(international_visuals.get("source_locale") or "").strip()
                        source_country = str(international_visuals.get("source_country") or "").strip().upper()
                        if asset_locale == DEFAULT_VISUAL_LOCALE:
                            if record.get("korean_context_reviewed") is not True:
                                errors.append(f"한국 대응 자료의 한국 배경 검수가 필요합니다: {visual}")
                            if len(str(record.get("korean_context_note") or "").strip()) < 12:
                                errors.append(f"한국 대응 자료의 배경 근거가 필요합니다: {visual}")
                        else:
                            if asset_locale not in {source_locale, "neutral"}:
                                errors.append(
                                    f"국제 실제사건 장면의 visual_locale은 {source_locale} 또는 neutral이어야 합니다: {visual}"
                                )
                            if str(record.get("source_country") or "").strip().upper() != source_country:
                                errors.append(f"국제 실제사건 장면의 source_country가 다릅니다: {visual}")
                            if record.get("source_event_context_reviewed") is not True:
                                errors.append(f"국제 실제사건 맥락 검수가 필요합니다: {visual}")
                            if len(str(record.get("source_event_context_note") or "").strip()) < 12:
                                errors.append(f"국제 실제사건 맥락 근거가 필요합니다: {visual}")
                            if record.get("actual_event_media") is not True and media_type in {"photo", "video"}:
                                errors.append(f"국제 실사 자료는 actual_event_media=true여야 합니다: {visual}")
                    if kind in {"licensed", "official"}:
                        source_url = str(record.get("source_url") or "").strip()
                        if not is_http_url(source_url):
                            target.append(f"원본 source URL이 없는 수집 자산: {visual}")
                        elif is_search_result_url(source_url):
                            target.append(f"검색 결과 URL을 원본으로 기록한 자산: {visual}")
                        if not str(record.get("creator") or record.get("publisher") or "").strip():
                            target.append(f"creator 또는 publisher가 없는 수집 자산: {visual}")
                        if not str(record.get("license") or "").strip():
                            target.append(f"license 또는 사용 근거가 없는 수집 자산: {visual}")
                        if not str(record.get("attribution") or "").strip():
                            target.append(f"attribution이 없는 수집 자산: {visual}")
                        if visual_sourcing.get("web_search_enabled") and record.get("source_method") != "web_search":
                            target.append(f"source_method가 web_search가 아닌 수집 자산: {visual}")
                    qualifies_as_real_media = (
                        kind in {"licensed", "official", "owned"}
                        and record.get("synthetic") is False
                        and record.get("approved") is True
                        and record.get("news_relevance_reviewed") is True
                        and (
                            (bool(image) and media_type == "photo")
                            or (bool(video) and media_type == "video")
                        )
                    )
                    if strict_real_media_majority and qualifies_as_real_media:
                        real_media_scene_count += 1
                        if image and media_type == "photo":
                            used_real_news_photo = True
                    elif (
                        not strict_real_media_majority
                        and image
                        and kind in {"licensed", "official", "owned"}
                        and record.get("synthetic") is False
                        and record.get("approved") is True
                        and record.get("news_relevance_reviewed") is True
                    ):
                        used_real_news_photo = True
                    generated_limit = generated_image_size_limit(visual_sourcing)
                    if kind == "generated" and visual_sourcing.get("visual_quality_review_required") is True:
                        if record.get("visual_quality_reviewed") is not True:
                            target.append(f"육안 품질 검수를 완료하지 않은 생성 이미지: {visual}")
                    if kind == "generated" and image and visual_path and generated_limit:
                        try:
                            from PIL import Image

                            with Image.open(visual_path) as generated_image:
                                generated_width, generated_height = generated_image.size
                            max_width, max_height = generated_limit
                            if generated_width > max_width or generated_height > max_height:
                                target.append(
                                    "생성 이미지가 기본 크기를 넘습니다: "
                                    f"{visual}: {generated_width}x{generated_height}/{max_width}x{max_height}"
                                )
                        except Exception as exc:
                            errors.append(f"생성 이미지 크기를 확인할 수 없습니다: {visual}: {exc}")
                if strict_quick_reveal:
                    relevance_level = str(record.get("relevance_level") or "").strip()
                    relevance_note = str(record.get("relevance_note") or "").strip()
                    if relevance_level not in ALLOWED_VISUAL_RELEVANCE_LEVELS:
                        target.append(
                            "새 퀵리빌 시각 자산에는 relevance_level이 필요합니다: "
                            f"{scene_id}: {visual}: direct 또는 contextual"
                        )
                    if not relevance_note:
                        target.append(
                            f"새 퀵리빌 시각 자산에 장면 주장과의 연관성 메모가 없습니다: {scene_id}: {visual}"
                        )
                    if (
                        relevance_level in ALLOWED_VISUAL_RELEVANCE_LEVELS
                        and beat in QUICK_REVEAL_DIRECT_VISUAL_BEATS
                        and relevance_level != "direct"
                    ):
                        target.append(
                            "퀵리빌 핵심 장면은 주장과 직접 일치하는 인물·사건·대상·문서 이미지여야 합니다: "
                            f"{scene_id}: {visual}"
                        )
                    if (
                        kind in {"licensed", "official", "owned"}
                        and record.get("synthetic") is False
                        and record.get("news_relevance_reviewed") is not True
                    ):
                        target.append(f"기사 연관성 육안 검수가 완료되지 않은 퀵리빌 수집 자산: {scene_id}: {visual}")
                if scene.get("synthetic") and record.get("synthetic") is not True:
                    target.append(f"장면과 권리 기록의 synthetic 상태가 다릅니다: {visual}")
                if not scene.get("synthetic") and record.get("synthetic") is True:
                    target.append(f"장면과 권리 기록의 synthetic 상태가 다릅니다: {visual}")
        synthetic_used = synthetic_used or bool(scene.get("synthetic"))
        synthetic_scene_flags.append(bool(scene.get("synthetic")))

    if strict_company_visuals:
        target = errors if final else warnings
        for company_key, company in declared_companies.items():
            if company_key not in used_company_visuals:
                target.append(
                    "핵심 기업의 첫 주요 언급 장면에 권리 승인 로고 또는 실제 기업 이미지가 없습니다: "
                    f"{company['name']}. 사용 가능한 자료가 없으면 최종 렌더를 중단하고 권리 장애를 보고하세요."
                )
    if strict_editorial_grounding:
        target = errors if final else warnings
        for person_key, person in declared_people.items():
            if person["visual_status"] == "used" and person_key not in used_person_visuals:
                target.append(
                    "실사진 사용으로 기록한 중앙 인물이 지정 장면의 권리 승인 자산과 연결되지 않았습니다: "
                    f"{person['name']}"
                )
            if (
                person["role"] in {"public_official", "public_figure"}
                and person["visual_status"] != "used"
            ):
                warnings.append(
                    "중앙 공인 실사진을 사용하지 못했습니다. 검색·권리 장애 기록과 대체 근거 화면을 확인하세요: "
                    f"{person['name']}"
                )

    if style_template == "fact-stack":
        contract_errors, contract_warnings = fact_stack_contract_issues(
            known_claim_ids,
            [scene for scene in scenes if isinstance(scene, dict)],
            profile,
            strict=strict_fact_stack,
            final=final,
        )
        errors.extend(message for message in contract_errors if message not in errors)
        warnings.extend(message for message in contract_warnings if message not in warnings)

    if style_template in RETENTION_TEMPLATES:
        valid_scenes = [scene for scene in scenes if isinstance(scene, dict)]
        estimated_total = estimated_render_duration(valid_scenes)
        try:
            target_duration = float(project.get("target_duration_seconds") or 0.0)
        except (TypeError, ValueError):
            target_duration = 0.0
        if target_duration > 0 and estimated_total > target_duration * TARGET_DURATION_WARNING_RATIO:
            message = (
                "Typecast 예상 길이가 목표를 초과합니다: "
                f"{estimated_total:.1f}/{target_duration:.1f}초. 대사를 줄인 뒤 렌더하세요."
            )
            if final and estimated_total > target_duration * TARGET_DURATION_ERROR_RATIO:
                errors.append(message)
            else:
                warnings.append(message)

    if visual_sourcing.get("web_search_enabled") and storyboard_has_visuals and not valid_searches:
        (errors if final else warnings).append("웹 시각 자료 검색이 활성화됐지만 rights-manifest.json에 검색 기록이 없습니다.")
    if visual_sourcing.get("prefer_collected_assets") and used_asset_kinds == {"generated"}:
        warnings.append("모든 장면이 생성 자산입니다. 상업 이용 가능한 공식·라이선스 자산을 다시 검토하세요.")
    if synthetic_scene_flags:
        synthetic_share = sum(synthetic_scene_flags) / len(synthetic_scene_flags)
        if synthetic_share > max_generated_scene_ratio:
            warnings.append(
                "생성 시각자료 비중이 높습니다: "
                f"{sum(synthetic_scene_flags)}/{len(synthetic_scene_flags)} "
                f"(기준 {max_generated_scene_ratio:.0%}). 실제 사진·공식 자료·영상·도표를 다시 검토하세요."
            )
        longest_synthetic_run = 0
        current_synthetic_run = 0
        for is_synthetic in synthetic_scene_flags:
            current_synthetic_run = current_synthetic_run + 1 if is_synthetic else 0
            longest_synthetic_run = max(longest_synthetic_run, current_synthetic_run)
        synthetic_run_limit = 3
        if longest_synthetic_run >= synthetic_run_limit:
            warnings.append(
                f"생성 시각자료가 {synthetic_run_limit}장면 이상 연속됩니다. "
                "실제 사진·공식 자료·도표로 시각 리듬을 바꾸세요."
            )
    if strict_real_media_majority and visual_scene_count:
        real_media_share = real_media_scene_count / visual_scene_count
        if real_media_share < min_real_media_ratio:
            target = errors if final else warnings
            target.append(
                "실사 시각자료 비중이 낮습니다: "
                f"{real_media_scene_count}/{visual_scene_count} "
                f"(기준 {min_real_media_ratio:.0%}). "
                "권리와 기사 연관성을 확인한 실제 사진·영상 위주로 장면을 다시 구성하세요."
            )
    if visual_sourcing.get("real_news_photo_required") is True and not used_real_news_photo:
        target = errors if final else warnings
        requirement = (
            "licensed·official·owned 사진 중 media_type=photo, approved, synthetic=false, "
            "news_relevance_reviewed=true인 자산"
            if strict_real_media_majority
            else "licensed·official·owned 사진 중 approved, synthetic=false, news_relevance_reviewed=true인 자산"
        )
        target.append(
            "권리와 기사 연관성을 확인한 실제 뉴스 사진이 없습니다. "
            f"{requirement}을 최소 1개 사용하세요."
        )
    if (
        len(image_motions) >= 4
        and len(set(image_motions)) == 1
        and image_motions[0] != "none"
    ):
        warnings.append("모든 정지 장면의 motion이 같습니다. 장면 의도에 맞는 zoom-in, zoom-out, none 배치를 확인하세요.")
    if strict_story_flow and still_scene_count:
        zoom_ratio = zoom_scene_count / still_scene_count
        if zoom_ratio > 0.5:
            (errors if final else warnings).append(
                f"강조 줌이 정지 장면의 절반을 넘습니다: {zoom_scene_count}/{still_scene_count}. "
                "강조할 장면만 남기고 나머지는 none으로 설정하세요."
            )
        elif zoom_ratio > 0.35:
            warnings.append(
                f"강조 줌 비중이 높습니다: {zoom_scene_count}/{still_scene_count}. "
                "실제 강조 구간인지 다시 확인하세요."
            )
        if max_consecutive_zoom_count > 2:
            (errors if final else warnings).append(
                f"강조 줌이 {max_consecutive_zoom_count}장면 연속됩니다. 최대 두 장면까지만 연속 사용하세요."
            )
    if strict_story_flow:
        max_meme_count = max(1, (len(scenes) + 4) // 5)
        if reaction_meme_count > max_meme_count:
            (errors if final else warnings).append(
                f"reaction-meme 비중이 높습니다: {reaction_meme_count}/{len(scenes)}. "
                f"최대 {max_meme_count}장면만 사용하세요."
            )
    for index in range(1, len(visual_sequence)):
        current_scene = scenes[index] if isinstance(scenes[index], dict) else {}
        if (
            visual_sequence[index]
            and visual_sequence[index] == visual_sequence[index - 1]
            and str(current_scene.get("video") or "").strip()
        ):
            warnings.append(f"연속 장면이 같은 시각 자산을 사용합니다: scene-{index:02d}/scene-{index + 1:02d}")

    if style_template in RETENTION_TEMPLATES:
        target = errors if final else warnings
        first_scene = scenes[0] if isinstance(scenes[0], dict) else {}
        if str(first_scene.get("beat") or "") != "hook":
            target.append("첫 장면 beat는 hook이어야 합니다.")
        if "payoff" not in seen_beats:
            target.append("오프닝 약속을 회수하는 payoff 장면이 없습니다.")
        valid_scenes = [scene for scene in scenes if isinstance(scene, dict)]
        last_non_loop = next(
            (scene for scene in reversed(valid_scenes) if str(scene.get("beat") or "") != "loop"),
            {},
        )
        if "payoff" in seen_beats and str(last_non_loop.get("beat") or "") != "payoff":
            target.append("마지막 본문 장면은 결론을 회수하는 payoff여야 합니다.")
        elif str(last_non_loop.get("beat") or "") == "payoff" and not str(last_non_loop.get("caption") or "").strip():
            target.append("payoff 장면에는 결론을 화면에 보여주는 caption이 필요합니다.")
        if style.get("show_payoff_label") is True:
            try:
                payoff_duration = float(last_non_loop.get("duration") or 0.0)
            except (TypeError, ValueError):
                payoff_duration = 0.0
            if payoff_duration < 3.5:
                target.append("결론을 읽을 수 있도록 payoff 장면을 최소 3.5초 유지하세요.")
        discussion_prompt = str(last_non_loop.get("discussion_prompt") or "").strip()
        if str(style.get("payoff_panel_style") or "").strip() == "editorial-card":
            payoff_title = str(last_non_loop.get("payoff_title") or "").strip()
            payoff_detail = str(last_non_loop.get("payoff_detail") or "").strip()
            payoff_punch = str(last_non_loop.get("payoff_punch") or "").strip()
            if not payoff_title:
                target.append("편집형 결론 카드에 payoff_title이 필요합니다.")
            if not payoff_detail:
                target.append("편집형 결론 카드에 시청자 행동 또는 의미를 적은 payoff_detail이 필요합니다.")
            if len(payoff_title) > 32:
                warnings.append("payoff_title이 깁니다. 한두 줄의 완결된 답으로 줄이세요.")
            if len(payoff_detail) > 52:
                warnings.append("payoff_detail이 깁니다. 확인할 조건이나 의미만 남기세요.")
            payoff_scene_index = valid_scenes.index(last_non_loop)
            earlier_visible_copy: list[tuple[str, str, str]] = []
            for earlier_scene in valid_scenes[:payoff_scene_index]:
                earlier_scene_id = str(earlier_scene.get("id") or "earlier-scene")
                for earlier_field in (
                    "caption",
                    "evidence_label",
                    "evidence_value",
                    "payoff_title",
                    "payoff_detail",
                    "payoff_punch",
                ):
                    earlier_value = str(earlier_scene.get(earlier_field) or "").strip()
                    if earlier_value:
                        earlier_visible_copy.append(
                            (earlier_scene_id, earlier_field, earlier_value)
                        )
            for payoff_field, payoff_value in (
                ("payoff_title", payoff_title),
                ("payoff_detail", payoff_detail),
                ("payoff_punch", payoff_punch),
            ):
                normalized_payoff_value = re.sub(
                    r"[^0-9A-Za-z가-힣]", "", payoff_value.lower()
                )
                if len(normalized_payoff_value) < 4:
                    continue
                for earlier_scene_id, earlier_field, earlier_value in earlier_visible_copy:
                    normalized_earlier_value = re.sub(
                        r"[^0-9A-Za-z가-힣]", "", earlier_value.lower()
                    )
                    if (
                        normalized_payoff_value == normalized_earlier_value
                        or text_similarity(payoff_value, earlier_value) >= 0.9
                    ):
                        target.append(
                            "결론 카드가 앞서 공개한 자막을 반복합니다: "
                            f"{payoff_field} ↔ {earlier_scene_id}.{earlier_field}. "
                            "결론에는 새 행동, 조건 또는 의미를 남기세요."
                        )
                        break
            if strict_payoff_retention:
                payoff_delivery = str(last_non_loop.get("voice_delivery") or "auto").strip().lower()
                if not payoff_punch:
                    target.append(
                        "마지막 이탈을 막을 payoff_punch가 필요합니다. "
                        "앞선 요약이 아니라 남은 핵심, 시민 영향 또는 정확한 다음 조건을 적으세요."
                    )
                elif max(
                    text_similarity(payoff_title, payoff_punch),
                    text_similarity(payoff_detail, payoff_punch),
                ) >= 0.82:
                    target.append(
                        "payoff_punch가 결론 제목이나 상세를 다시 말합니다. "
                        "시청자가 기억할 새 의미나 남은 핵심으로 바꾸세요."
                    )
                if any(term in payoff_punch for term in GENERIC_UNKNOWN_PAYOFF_TERMS):
                    target.append(
                        "payoff_punch를 일반적인 미확인 상태로 끝낼 수 없습니다. "
                        "중요한 한정은 앞선 narration 또는 truth_guard에 남기고, "
                        "확인된 시민 부담이나 구체적 모순으로 마무리하세요."
                    )
                if not strict_continuous_flow and payoff_delivery not in TYPECAST_PAYOFF_DELIVERIES:
                    target.append(
                        "새 payoff 장면은 voice_delivery를 contrast 또는 verdict로 지정해 "
                        "Typecast 강조 전달을 사용하세요."
                    )
            if discussion_prompt and not discussion_prompt.endswith("?"):
                warnings.append("discussion_prompt는 시청자가 답할 수 있는 질문형 문장으로 끝내세요.")
            if len(discussion_prompt) > 36:
                warnings.append("discussion_prompt가 깁니다. 주제를 포함한 짧은 질문으로 줄이세요.")
        profile_hook = str(profile.get("hook") or "").strip()
        profile_payoff = str(profile.get("payoff") or "").strip()
        payoff_caption = str(last_non_loop.get("caption") or "").strip()
        payoff_narration = str(last_non_loop.get("narration") or "").strip()
        normalized_payoff = re.sub(r"[^0-9A-Za-z가-힣]", "", profile_payoff.lower())
        normalized_caption = re.sub(r"[^0-9A-Za-z가-힣]", "", payoff_caption.lower())
        if len(normalized_payoff) < MIN_PAYOFF_LENGTH:
            target.append("payoff가 너무 짧습니다. 현재 상태와 시청자가 알아야 할 결과를 한 문장에 함께 적으세요.")
        if normalized_payoff in WEAK_PAYOFF_TEXTS or normalized_caption in WEAK_PAYOFF_TEXTS:
            target.append("payoff가 추상적인 문구로 끝납니다. 검증된 상태, 원인, 영향 또는 다음 조건을 구체적으로 밝히세요.")
        if not payoff_narration and not visual_first:
            target.append("payoff 장면에는 결론을 완결된 문장으로 말하는 narration이 필요합니다.")
        if strict_payoff_retention and payoff_narration and not visual_first:
            payoff_punch = str(last_non_loop.get("payoff_punch") or "").strip()
            if len(re.findall(r"[.!?…]+", payoff_narration)) < 2:
                target.append(
                    "payoff narration은 확인된 답과 마지막 붙잡기를 두 개 이상의 말하기 박자로 "
                    "분리하세요."
                )
            if payoff_punch and not has_shared_significant_term(payoff_punch, payoff_narration):
                target.append(
                    "payoff_punch의 핵심 표현을 narration에서도 말해 화면과 음성의 마지막 강조를 맞추세요."
                )
        if (
            screen_copy_mode == SCREEN_COPY_MODE_NOUN_PHRASES
            and discussion_prompt
            and payoff_narration
            and not visual_first
        ):
            if not payoff_narration.endswith("?"):
                target.append(
                    "discussion_prompt가 있으면 payoff narration도 사실 결론 뒤의 상황형 반문으로 끝내세요."
                )
            if not re.search(r"[.!]\s*[^.!?]+\?$", payoff_narration):
                target.append(
                    "payoff narration은 사실 결론을 먼저 말한 뒤 별도 반문을 붙여야 합니다. "
                    "질문만으로 결론을 대체할 수 없습니다."
                )
        if text_similarity(profile_hook, profile_payoff) >= MAX_PAYOFF_HOOK_SIMILARITY:
            target.append("payoff가 hook을 다시 말하는 수준입니다. 새 답, 원인 또는 영향을 결론에 추가하세요.")
        if style_template != "quick-reveal" and not ({"rehook", "turn"} & seen_beats):
            target.append("중간 이탈을 막을 rehook 또는 turn 장면이 없습니다.")

    try:
        first_duration = float(scenes[0].get("duration") or 0.0) if isinstance(scenes[0], dict) else 0.0
    except (TypeError, ValueError):
        first_duration = 0.0
    first_limit = 2.5 if style_template in RETENTION_TEMPLATES else 4.0
    if first_duration > first_limit:
        (errors if final and strict_early_retention else warnings).append(
            f"첫 장면이 {first_limit:.1f}초를 넘습니다. 첫 질문을 줄이고 10초 이내 재후킹 공간을 확보하세요."
        )
    general_minimum = 8.0 if visual_first else 12.0 if strict_v16_retention else 15.0
    if planned_total and not general_minimum <= planned_total <= 180:
        warnings.append(f"계획 영상 길이가 일반 Shorts 범위를 벗어납니다: {planned_total:.1f}초")
    format_ranges = {
        "quick-reveal": (
            (VISUAL_FIRST_MIN_DURATION_SECONDS, VISUAL_FIRST_MAX_DURATION_SECONDS, VISUAL_FIRST_MIN_SCENES, VISUAL_FIRST_MAX_SCENES)
            if visual_first
            else (CONTINUOUS_FLOW_MIN_DURATION_SECONDS, CONTINUOUS_FLOW_MAX_DURATION_SECONDS, 4, 9)
        ),
        "fact-stack": (20.0, 55.0, 6, 12),
        "story-explainer": (35.0, 120.0, 8, 20),
    }
    if style_template in format_ranges:
        minimum, maximum, min_scenes, max_scenes = format_ranges[style_template]
        if planned_total and not minimum <= planned_total <= maximum:
            warnings.append(f"{style_template} 권장 길이는 {minimum:.0f}-{maximum:.0f}초입니다: {planned_total:.1f}초")
        if not min_scenes <= len(scenes) <= max_scenes:
            warnings.append(f"{style_template} 권장 장면 수는 {min_scenes}-{max_scenes}개입니다: {len(scenes)}개")

    if synthetic_used and not publish.get("contains_synthetic_media"):
        (errors if final else warnings).append("합성 이미지가 있지만 publish.json 표시가 false입니다.")
    if final and not publish.get("source_lines"):
        errors.append("publish.json에 source_lines가 없습니다.")

    try:
        publish_version = int(publish.get("version") or 1)
    except (TypeError, ValueError):
        publish_version = 1
    if publish_version >= 2:
        target = errors if final else warnings
        for field, label in (
            ("title", "제목"),
            ("description", "설명"),
            ("pinned_comment", "고정 댓글"),
        ):
            if not str(publish.get(field) or "").strip():
                target.append(f"publish.json에 업로드용 {label}이 없습니다.")
        title_value = str(publish.get("title") or "")
        description_value = str(publish.get("description") or "")
        if len(title_value) > YOUTUBE_TITLE_LIMIT:
            target.append(
                f"publish.json의 업로드 제목이 {YOUTUBE_TITLE_LIMIT}자를 넘습니다: "
                f"{len(title_value)}/{YOUTUBE_TITLE_LIMIT}자"
            )
        if len(description_value) > YOUTUBE_DESCRIPTION_LIMIT:
            target.append(
                f"publish.json의 업로드 설명이 {YOUTUBE_DESCRIPTION_LIMIT}자를 넘습니다: "
                f"{len(description_value)}/{YOUTUBE_DESCRIPTION_LIMIT}자"
            )
        if publish_version >= 4:
            if contains_publish_link(description_value):
                target.append(
                    "publish.json의 업로드 설명에는 링크를 넣을 수 없습니다. "
                    "출처는 매체명과 기사명만 적고 URL은 sources.json에만 보관하세요."
                )
            if contains_public_production_disclosure(description_value):
                target.append(
                    "publish.json의 공개 설명에는 사진 제공처·라이선스·자료사진 여부나 "
                    "Typecast·TTS·합성음성 같은 제작 내부 문구를 넣을 수 없습니다. "
                    "권리와 합성 정보는 rights-manifest.json, render-report.json, "
                    "contains_synthetic_media, altered_content에만 유지하세요."
                )
            source_lines = publish.get("source_lines")
            if not isinstance(source_lines, list) or not any(
                str(source_line).strip() for source_line in source_lines
            ):
                target.append("publish.json의 source_lines에는 링크 없는 매체명·기사명이 필요합니다.")
            elif any(contains_publish_link(source_line) for source_line in source_lines):
                target.append(
                    "publish.json의 source_lines에는 URL을 넣을 수 없습니다. "
                    "매체명 — 기사명 형식으로 작성하세요."
                )
        if publish_version >= 5:
            if PUBLISH_HASHTAG_PATTERN.search(description_value):
                target.append(
                    "publish.json의 업로드 설명에는 해시태그를 넣지 마세요. "
                    "해시태그는 제목과 tags 필드에서만 관리하세요."
                )
            repeated_sentences = duplicated_title_sentences(title_value, description_value)
            if repeated_sentences:
                target.append(
                    "publish.json의 업로드 설명이 제목을 반복합니다. "
                    "제목은 질문형 훅으로 두고 설명은 답·근거·확인사항부터 작성하세요: "
                    f"{repeated_sentences[0]}"
                )
        tags = publish.get("tags")
        if not isinstance(tags, list) or not any(str(tag).strip() for tag in tags):
            target.append("publish.json에 업로드용 tags가 없습니다.")
        display_title = title_with_hashtags(title_value, tags)
        if display_title and not re.search(r"#[0-9A-Za-z가-힣_]+", display_title):
            target.append(
                "업로드 제목에 붙일 해시태그 공간이 없습니다. "
                "publish.json 제목을 줄이거나 tags를 확인하세요."
            )

        upload_settings = publish.get("upload_settings")
        if not isinstance(upload_settings, dict):
            target.append("publish.json의 upload_settings는 객체여야 합니다.")
        else:
            if upload_settings.get("audience") not in {"made_for_kids", "not_made_for_kids"}:
                target.append("upload_settings.audience는 made_for_kids 또는 not_made_for_kids여야 합니다.")
            if not str(upload_settings.get("category") or "").strip():
                target.append("upload_settings.category가 없습니다.")
            altered_content = upload_settings.get("altered_content")
            if altered_content not in {"yes", "no", "review_required"}:
                target.append("upload_settings.altered_content는 yes, no, review_required 중 하나여야 합니다.")
            elif final and altered_content == "review_required":
                errors.append("최종 업로드 전 altered_content 공개 여부 검토가 필요합니다.")
            if not isinstance(upload_settings.get("allow_comments"), bool):
                target.append("upload_settings.allow_comments는 true 또는 false여야 합니다.")
            if publish_version >= 3:
                thumbnail_method = upload_settings.get("thumbnail_method")
                if thumbnail_method not in {"video_frame", "file_upload"}:
                    target.append("upload_settings.thumbnail_method는 video_frame 또는 file_upload여야 합니다.")
                thumbnail_status = str(upload_settings.get("thumbnail_status") or "").strip()
                thumbnail_file_value = str(upload_settings.get("thumbnail_file") or "").strip()
                if thumbnail_status and thumbnail_status not in {"pending", "ready", "blocked_rights"}:
                    target.append(
                        "upload_settings.thumbnail_status는 pending, ready, blocked_rights 중 하나여야 합니다."
                    )
                if thumbnail_method == "file_upload" and not thumbnail_file_value:
                    if thumbnail_status == "blocked_rights":
                        (errors if final else warnings).append(
                            "file_upload 썸네일이 권리 승인 이미지 부족으로 차단됐습니다."
                        )
                    else:
                        target.append("file_upload 썸네일에는 upload_settings.thumbnail_file이 필요합니다.")
                if not str(upload_settings.get("thumbnail_note") or "").strip():
                    target.append("upload_settings.thumbnail_note에 선택 장면·시점 또는 썸네일 파일 안내가 필요합니다.")
                if project_version >= 9:
                    thumbnail_hook = str(upload_settings.get("thumbnail_hook") or "").strip()
                    thumbnail_note = str(upload_settings.get("thumbnail_note") or "").strip()
                    thumbnail_file = str(upload_settings.get("thumbnail_file") or "").strip()
                    if thumbnail_method != "file_upload":
                        target.append("새 프로젝트의 썸네일은 영상 프레임이 아닌 별도 file_upload 이미지여야 합니다.")
                    if not ends_with_question(thumbnail_hook):
                        target.append("새 프로젝트의 thumbnail_hook은 누구나 궁금해할 구체적인 질문형이어야 합니다.")
                    if "별도" not in thumbnail_note:
                        target.append("thumbnail_note에는 영상과 별도로 생성한 썸네일임을 명시해야 합니다.")
                    if final and thumbnail_file:
                        try:
                            thumbnail_path = resolve_project_file(project_dir, thumbnail_file, must_exist=False)
                        except News2ShortsError as exc:
                            errors.append(str(exc))
                        else:
                            if not thumbnail_path.is_file():
                                errors.append(f"최종 업로드용 별도 썸네일 파일이 없습니다: {thumbnail_file}")
                    if project_version >= 13:
                        thumbnail_subhook = str(upload_settings.get("thumbnail_subhook") or "").strip()
                        thumbnail_badge = str(upload_settings.get("thumbnail_badge") or "").strip()
                        thumbnail_style = str(upload_settings.get("thumbnail_style") or "").strip().lower()
                        if len(re.sub(r"\s+", "", thumbnail_subhook)) < 6:
                            target.append("thumbnail_subhook에는 검증된 숫자·조건·시민 영향을 짧게 적으세요.")
                        elif not has_shared_significant_term(
                            thumbnail_subhook,
                            f"{profile.get('hook_stake', '')} {profile.get('viewer_stake', '')} {profile.get('payoff', '')}",
                        ):
                            target.append("thumbnail_subhook이 검증된 훅 지분·시민 영향·결론과 연결되지 않습니다.")
                        normalized_badge = re.sub(r"\s+", "", thumbnail_badge)
                        if len(normalized_badge) < 3:
                            target.append("thumbnail_badge에는 주제별 긴장 단서를 3자 이상 적으세요.")
                        elif len(normalized_badge) > 14:
                            target.append("thumbnail_badge는 14자 이하의 주제별 긴장 단서로 줄이세요.")
                        elif normalized_badge in GENERIC_THUMBNAIL_BADGES:
                            target.append("thumbnail_badge가 너무 일반적입니다. 사건의 조건·가격·공백·반전을 짧게 지목하세요.")
                        if thumbnail_style not in THUMBNAIL_STYLES:
                            target.append("thumbnail_style은 auto, presenter-led, evidence-led 중 하나여야 합니다.")
                        if project.get("sensitive_topic") is True and thumbnail_style == "presenter-led":
                            target.append("민감 뉴스에는 presenter-led 썸네일을 사용할 수 없습니다.")
                        if final and (
                            thumbnail_style == "presenter-led"
                            or str(upload_settings.get("thumbnail_presenter_file") or "").strip()
                        ):
                            try:
                                thumbnail_presenter_asset(
                                    project_dir,
                                    manifest,
                                    upload_settings,
                                    required=True,
                                )
                            except News2ShortsError as exc:
                                errors.append(str(exc))
                if not str(upload_settings.get("playlist") or "").strip():
                    target.append("upload_settings.playlist에는 추천 재생목록 또는 '선택 안 함'이 필요합니다.")
                if not str(upload_settings.get("video_language") or "").strip():
                    target.append("upload_settings.video_language가 없습니다.")
                if not isinstance(upload_settings.get("paid_promotion"), bool):
                    target.append("upload_settings.paid_promotion은 true 또는 false여야 합니다.")
                age_restriction = upload_settings.get("age_restriction")
                if age_restriction not in {"none", "18_plus", "review_required"}:
                    target.append("upload_settings.age_restriction은 none, 18_plus, review_required 중 하나여야 합니다.")
                elif final and age_restriction == "review_required":
                    errors.append("최종 업로드 전 연령 제한 여부 검토가 필요합니다.")
                visibility = upload_settings.get("visibility")
                if visibility not in {"private", "unlisted", "public", "scheduled"}:
                    target.append("upload_settings.visibility는 private, unlisted, public, scheduled 중 하나여야 합니다.")
                schedule_at = str(upload_settings.get("schedule_at") or "").strip()
                if visibility == "scheduled" and not schedule_at:
                    target.append("예약 공개에는 upload_settings.schedule_at이 필요합니다.")
                elif schedule_at:
                    try:
                        scheduled_at = dt.datetime.fromisoformat(schedule_at)
                        if visibility == "scheduled" and scheduled_at.tzinfo is None:
                            target.append("예약 공개 schedule_at에는 시간대가 필요합니다.")
                    except ValueError:
                        target.append("upload_settings.schedule_at은 ISO 8601 날짜·시간이어야 합니다.")

    source_audio_errors, source_audio_warnings = validate_source_audio_review(
        project_dir,
        [scene for scene in scenes if isinstance(scene, dict)],
        final=final,
    )
    errors.extend(source_audio_errors)
    warnings.extend(source_audio_warnings)

    if final:
        approvals = project.get("approvals") or {}
        required_approvals = [
            "editorial_reviewed",
            "rights_reviewed",
            "synthetic_disclosure_reviewed",
        ]
        missing = [name for name in required_approvals if approvals.get(name) is not True]
        if missing:
            errors.append(f"최종 렌더 승인 미완료: {', '.join(missing)}")
    return errors, warnings


def probe_video(path: Path) -> dict:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    return {
        "path": str(path),
        "duration": float(data.get("format", {}).get("duration", 0.0)),
        "video_codec": video.get("codec_name") if video else None,
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "audio_codec": audio.get("codec_name") if audio else None,
        "has_video": video is not None,
        "has_audio": audio is not None,
    }


def compose_brand_intro(project: dict, body: Path, destination: Path) -> dict:
    config = brand_intro_config(project)
    if config.get("enabled") is not True:
        raise News2ShortsError("공통 인트로는 비활성화할 수 없습니다.")
    mode = str(config.get("mode") or BRAND_MODE_LEGACY_FULL).strip()
    if mode not in ALLOWED_BRAND_MODES:
        raise News2ShortsError("brand_intro.mode는 corner-logo 또는 legacy-full이어야 합니다.")
    if mode == BRAND_MODE_CORNER_LOGO:
        if not BRAND_LOGO_PATH.is_file():
            raise News2ShortsError(f"corner-logo 자산이 없습니다: {BRAND_LOGO_PATH}")
        body_info = probe_video(body)
        if not body_info["has_video"] or not body_info["has_audio"]:
            raise News2ShortsError("뉴스 본편에는 영상과 오디오 스트림이 모두 필요합니다.")
        run_command(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(body),
                "-i",
                str(BRAND_LOGO_PATH),
                "-filter_complex",
                f"[1:v]scale={BRAND_LOGO_SIZE}:{BRAND_LOGO_SIZE}[logo];"
                f"[0:v][logo]overlay={BRAND_LOGO_MARGIN}:{BRAND_LOGO_MARGIN}:format=auto,format=yuv420p[v]",
                "-map",
                "[v]",
                "-map",
                "0:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-r",
                "30",
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                "-y",
                str(destination),
            ]
        )
        output_info = probe_video(destination)
        return {
            "enabled": True,
            "mode": BRAND_MODE_CORNER_LOGO,
            "asset": BRAND_INTRO_ASSET_ID,
            "asset_path": "assets/news-hanmyeon-channel-logo.png",
            "source_duration": 0.0,
            "lead_in_seconds": 0.0,
            "has_audio": False,
            "position": "top-left",
            "size": BRAND_LOGO_SIZE,
            "margin": BRAND_LOGO_MARGIN,
            "transition": None,
            "transition_duration": 0.0,
            "transition_scope": "none",
            "news_scene_transition": "cut",
            "rendered_total_duration": round(float(output_info["duration"]), 3),
        }
    asset_id = str(config.get("asset") or "").strip()
    asset_path = brand_intro_asset_path(asset_id)
    if asset_path is None:
        raise News2ShortsError(
            "공통 인트로 asset은 "
            f"{', '.join(sorted(ALLOWED_BRAND_INTRO_ASSET_IDS))} 중 하나여야 합니다."
        )
    if not asset_path.is_file():
        raise News2ShortsError(f"공통 인트로 자산이 없습니다: {asset_path}")

    transition = str(config.get("transition") or DEFAULT_BRAND_INTRO_TRANSITION).strip()
    if transition not in ALLOWED_BRAND_INTRO_TRANSITIONS:
        raise News2ShortsError(f"지원하지 않는 공통 인트로 전환 효과입니다: {transition}")
    try:
        configured_duration = float(
            config.get("transition_duration") or DEFAULT_BRAND_INTRO_TRANSITION_DURATION
        )
    except (TypeError, ValueError) as exc:
        raise News2ShortsError("brand_intro.transition_duration은 숫자여야 합니다.") from exc
    if not MIN_BRAND_INTRO_TRANSITION_DURATION <= configured_duration <= MAX_BRAND_INTRO_TRANSITION_DURATION:
        raise News2ShortsError(
            "brand_intro.transition_duration은 "
            f"{MIN_BRAND_INTRO_TRANSITION_DURATION:.2f}-{MAX_BRAND_INTRO_TRANSITION_DURATION:.2f}초여야 합니다."
        )

    intro_info = probe_video(asset_path)
    body_info = probe_video(body)
    if not intro_info["has_video"] or not intro_info["has_audio"]:
        raise News2ShortsError("공통 인트로에는 영상과 오디오 스트림이 모두 필요합니다.")
    if not body_info["has_video"] or not body_info["has_audio"]:
        raise News2ShortsError("뉴스 본편에는 영상과 오디오 스트림이 모두 필요합니다.")
    transition_duration = min(
        configured_duration,
        max(0.0, intro_info["duration"] - (1 / 30)),
        max(0.0, body_info["duration"] - (1 / 30)),
    )
    if transition_duration < MIN_BRAND_INTRO_TRANSITION_DURATION:
        raise News2ShortsError("공통 인트로 또는 뉴스 본편이 전환 효과를 적용하기에 너무 짧습니다.")
    transition_offset = intro_info["duration"] - transition_duration
    output_width, output_height = OUTPUT_VIDEO_SIZE
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(asset_path),
            "-i",
            str(body),
            "-filter_complex",
            f"[0:v]scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
            f"crop={output_width}:{output_height},fps=30,setsar=1,settb=AVTB,setpts=PTS-STARTPTS[intro_v];"
            f"[1:v]scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
            f"crop={output_width}:{output_height},fps=30,setsar=1,settb=AVTB,setpts=PTS-STARTPTS[body_v];"
            f"[intro_v][body_v]xfade=transition={transition}:duration={transition_duration:.3f}:"
            f"offset={transition_offset:.3f},format=yuv420p[v];"
            "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            "asetpts=PTS-STARTPTS[intro_a];"
            "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            "asetpts=PTS-STARTPTS[body_a];"
            f"[intro_a][body_a]acrossfade=d={transition_duration:.3f}:c1=tri:c2=tri[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ]
    )
    output_info = probe_video(destination)
    return {
        "enabled": True,
        "mode": BRAND_MODE_LEGACY_FULL,
        "asset": asset_id,
        "asset_path": asset_path.relative_to(PLUGIN_ROOT).as_posix(),
        "source_duration": round(float(intro_info["duration"]), 3),
        "lead_in_seconds": round(float(transition_offset), 3),
        "has_audio": True,
        "transition": transition,
        "transition_duration": round(transition_duration, 3),
        "transition_scope": "intro-to-news-body",
        "news_scene_transition": "cut",
        "rendered_total_duration": round(float(output_info["duration"]), 3),
    }


def render_static_scene(
    frame: Path,
    audio: Path,
    destination: Path,
    duration: float,
    *,
    motion: str,
    overlay: Path | None = None,
    focus_x: float = 0.5,
    focus_y: float = 0.5,
    zoom_scale: float = 1.055,
    motion_start: float = 0.0,
    motion_duration: float = 0.0,
) -> None:
    output_width, output_height = OUTPUT_VIDEO_SIZE
    normalized_motion = "zoom-in" if motion == "slow-zoom" else motion
    focus_x = min(1.0, max(0.0, focus_x))
    focus_y = min(1.0, max(0.0, focus_y))
    zoom_scale = min(1.25, max(1.0, zoom_scale))
    motion_start = min(max(0.0, motion_start), max(0.0, duration))
    if motion_duration <= 0:
        motion_duration = max(0.0, duration - motion_start)
    motion_duration = min(max(1 / 30, motion_duration), max(1 / 30, duration - motion_start))
    start_frame = max(0, round(motion_start * 30))
    motion_frames = max(1, round(motion_duration * 30))
    end_frame = start_frame + motion_frames
    zoom_step = max(0.0001, (zoom_scale - 1.0) / motion_frames)
    if normalized_motion == "zoom-in":
        visual_filter = (
            "zoompan=z='"
            f"if(lt(on,{start_frame}),1,"
            f"if(lt(on,{end_frame}),min(1+(on-{start_frame})*{zoom_step:.7f},{zoom_scale:.4f}),"
            f"{zoom_scale:.4f}))':"
            f"x='max(0,min(iw-iw/zoom,iw*{focus_x:.4f}-(iw/zoom/2)))':"
            f"y='max(0,min(ih-ih/zoom,ih*{focus_y:.4f}-(ih/zoom/2)))':"
            f"d=1:s={output_width}x{output_height}:fps=30"
        )
    elif normalized_motion == "zoom-out":
        visual_filter = (
            "zoompan=z='"
            f"if(lt(on,{start_frame}),{zoom_scale:.4f},"
            f"if(lt(on,{end_frame}),max({zoom_scale:.4f}-(on-{start_frame})*{zoom_step:.7f},1),1))':"
            f"x='max(0,min(iw-iw/zoom,iw*{focus_x:.4f}-(iw/zoom/2)))':"
            f"y='max(0,min(ih-ih/zoom,ih*{focus_y:.4f}-(ih/zoom/2)))':"
            f"d=1:s={output_width}x{output_height}:fps=30"
        )
    else:
        visual_filter = f"scale={output_width}:{output_height}:flags=lanczos,fps=30"

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-framerate",
        "30",
        "-i",
        str(frame),
    ]
    audio_index = 1
    if overlay:
        command.extend(["-loop", "1", "-framerate", "30", "-i", str(overlay)])
        audio_index = 2
    command.extend(["-i", str(audio), "-t", f"{duration:.3f}"])
    output_filter = "format=yuv420p"
    if overlay:
        command.extend(
            [
                "-filter_complex",
                f"[0:v]{visual_filter}[visual];"
                f"[1:v]scale={output_width}:{output_height}:flags=lanczos[overlay];"
                f"[visual][overlay]overlay=0:0:format=auto,{output_filter}[v]",
                "-map",
                "[v]",
                "-map",
                f"{audio_index}:a:0",
            ]
        )
    else:
        command.extend(
            [
                "-vf",
                f"{visual_filter},{output_filter}",
                "-map",
                "0:v:0",
                "-map",
                f"{audio_index}:a:0",
            ]
        )
    command.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-af",
            "apad",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ]
    )
    run_command(command)


def render_video_scene(
    video: Path,
    overlay: Path,
    audio: Path,
    destination: Path,
    duration: float,
    *,
    start: float,
) -> None:
    output_width, output_height = OUTPUT_VIDEO_SIZE
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start > 0:
        command.extend(["-ss", f"{start:.3f}"])
    command.extend(
        [
            "-i",
            str(video),
            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(overlay),
            "-i",
            str(audio),
            "-t",
            f"{duration:.3f}",
            "-filter_complex",
            f"[0:v]scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
            f"crop={output_width}:{output_height},fps=30,setsar=1,tpad=stop_mode=clone:stop_duration=90,"
            f"trim=duration={duration:.3f},setpts=PTS-STARTPTS[base];"
            f"[1:v]scale={output_width}:{output_height}:flags=lanczos[overlay];"
            "[base][overlay]overlay=0:0:format=auto,format=yuv420p[v]",
            "-map",
            "[v]",
            "-map",
            "2:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-af",
            "apad",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ]
    )
    run_command(command)


def render_clean_video_scene(
    video: Path,
    audio: Path,
    destination: Path,
    duration: float,
    *,
    start: float,
) -> None:
    """Render a cropped scene with narration but without news text overlays."""
    output_width, output_height = OUTPUT_VIDEO_SIZE
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start > 0:
        command.extend(["-ss", f"{start:.3f}"])
    command.extend(
        [
            "-i",
            str(video),
            "-i",
            str(audio),
            "-t",
            f"{duration:.3f}",
            "-filter_complex",
            f"[0:v]scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
            f"crop={output_width}:{output_height},fps=30,setsar=1,tpad=stop_mode=clone:stop_duration=90,"
            f"trim=duration={duration:.3f},setpts=PTS-STARTPTS,format=yuv420p[v]",
            "-map",
            "[v]",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-af",
            "apad",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ]
    )
    run_command(command)


def concatenate_mp4_files(paths: list[Path], destination: Path, list_path: Path) -> None:
    if not paths:
        raise News2ShortsError("편집 호환 패키지에 연결할 장면이 없습니다.")
    list_path.write_text(
        "".join(f"file '{path.as_posix()}'\n" for path in paths),
        encoding="utf-8",
    )
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ]
    )


def concatenate_audio_files(paths: list[Path], destination: Path, list_path: Path) -> None:
    if not paths:
        raise News2ShortsError("연결할 오디오가 없습니다.")
    list_path.write_text(
        "".join(f"file '{path.as_posix()}'\n" for path in paths),
        encoding="utf-8",
    )
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-ac",
            "2",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(destination),
        ]
    )


def normalize_editor_audio(source: Path, destination: Path) -> None:
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(destination),
        ]
    )


def srt_timestamp(seconds: float) -> str:
    total_milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def editor_package_target(project_dir: Path, output_name: str) -> Path:
    stem = Path(output_name).stem.strip() or "short"
    safe_stem = re.sub(r"[^0-9A-Za-z가-힣._-]+", "-", stem).strip("-.") or "short"
    return resolve_project_file(
        project_dir,
        f"{EDITOR_PACKAGE_ROOT}/{safe_stem}",
        must_exist=False,
    )


def create_editor_package(
    project_dir: Path,
    project: dict,
    storyboard: dict,
    rendered_output: Path,
    output_name: str,
    work_dir: Path,
    editor_scenes: list[dict],
    mid_cta_path: Path | None,
    mid_cta_audio: Path | None,
    mid_cta_report: dict,
    cta_path: Path | None,
    cta_audio: Path | None,
    cta_report: dict,
    background_music: Path | None,
    *,
    overwrite: bool,
) -> dict:
    target = editor_package_target(project_dir, output_name)
    package_root = work_dir / "editor-package"
    scenes_dir = package_root / "scenes"
    overlays_dir = package_root / "overlays"
    audio_dir = package_root / "audio"
    metadata_dir = package_root / "metadata"
    for directory in (scenes_dir, overlays_dir, audio_dir, metadata_dir):
        directory.mkdir(parents=True, exist_ok=True)

    shutil.copy2(rendered_output, package_root / "reference.mp4")
    brand_config = brand_intro_config(project)
    brand_mode = str(brand_config.get("mode") or BRAND_MODE_LEGACY_FULL).strip()
    intro_asset_id = str(brand_config.get("asset") or "").strip()
    if brand_mode == BRAND_MODE_CORNER_LOGO:
        if not BRAND_LOGO_PATH.is_file():
            raise News2ShortsError(f"편집 패키지용 corner-logo 자산이 없습니다: {BRAND_LOGO_PATH}")
        shutil.copy2(BRAND_LOGO_PATH, package_root / "brand-logo.png")
    else:
        intro_asset_path = brand_intro_asset_path(intro_asset_id)
        if intro_asset_path is None or not intro_asset_path.is_file():
            raise News2ShortsError(f"편집 패키지용 공통 인트로 자산을 찾을 수 없습니다: {intro_asset_id}")
        shutil.copy2(intro_asset_path, package_root / "brand-intro.mp4")

    packaged_scenes: list[dict] = []
    clean_scene_paths: list[Path] = []
    for index, item in enumerate(editor_scenes, start=1):
        scene = item["scene"]
        scene_id = str(scene.get("id") or f"scene-{index:02d}")
        scene_name = f"scene-{index:02d}"
        packaged_scene = scenes_dir / f"{scene_name}.mp4"
        shutil.copy2(item["clean_path"], packaged_scene)
        clean_scene_paths.append(packaged_scene)

        packaged_audio = audio_dir / f"{scene_name}.wav"
        normalize_editor_audio(item["audio_path"], packaged_audio)

        packaged_overlay: Path | None = None
        overlay_path = item.get("overlay_path")
        if isinstance(overlay_path, Path) and overlay_path.is_file():
            packaged_overlay = overlays_dir / f"{scene_name}.png"
            shutil.copy2(overlay_path, packaged_overlay)

        packaged_scenes.append(
            {
                "id": scene_id,
                "beat": str(scene.get("beat") or ""),
                "duration": round(float(item["duration"]), 3),
                "audio_duration": round(float(item["audio_duration"]), 3),
                "audio_mode": scene_audio_mode(scene),
                "external_caption": scene_external_caption_enabled(scene),
                "render_text_overlay": scene_text_overlay_enabled(scene),
                "narration": suppress_editorial_identifiers(str(scene.get("narration") or "")),
                "headline": suppress_editorial_identifiers(str(scene.get("headline") or "")),
                "caption": suppress_editorial_identifiers(str(scene.get("caption") or "")),
                "source_asset": str(scene.get("video") or scene.get("image") or ""),
                "scene_clip": packaged_scene.relative_to(package_root).as_posix(),
                "audio_file": packaged_audio.relative_to(package_root).as_posix(),
                "overlay_file": (
                    packaged_overlay.relative_to(package_root).as_posix()
                    if packaged_overlay
                    else None
                ),
                "text_layers_editable": False,
            }
        )

    packaged_mid_cta: Path | None = None
    packaged_mid_cta_audio: Path | None = None
    mid_insert_after_index = 0
    if mid_cta_report.get("enabled") is True and mid_cta_path and mid_cta_path.is_file():
        mid_insert_after_index = int(mid_cta_report.get("insert_after_scene_index") or 0)
        packaged_mid_cta = scenes_dir / "mid-cta.mp4"
        shutil.copy2(mid_cta_path, packaged_mid_cta)
        clean_scene_paths.insert(mid_insert_after_index, packaged_mid_cta)
        if mid_cta_audio and mid_cta_audio.is_file():
            packaged_mid_cta_audio = audio_dir / "mid-cta.wav"
            normalize_editor_audio(mid_cta_audio, packaged_mid_cta_audio)

    packaged_cta: Path | None = None
    packaged_cta_audio: Path | None = None
    if cta_report.get("enabled") is True and cta_path and cta_path.is_file():
        packaged_cta = scenes_dir / "cta-tail.mp4"
        shutil.copy2(cta_path, packaged_cta)
        clean_scene_paths.append(packaged_cta)
        if cta_audio and cta_audio.is_file():
            packaged_cta_audio = audio_dir / "cta-tail.wav"
            normalize_editor_audio(cta_audio, packaged_cta_audio)

    clean_body = work_dir / "editor-news-body.mp4"
    concatenate_mp4_files(
        clean_scene_paths,
        clean_body,
        work_dir / "editor-concat.txt",
    )
    packaged_background_music: Path | None = None
    if background_music and background_music.is_file():
        packaged_background_music = audio_dir / "background-music.wav"
        normalize_editor_audio(background_music, packaged_background_music)
        clean_body_with_music = work_dir / "editor-news-body-with-music.mp4"
        mux_continuous_audio(clean_body, background_music, clean_body_with_music)
        clean_body = clean_body_with_music
    editable_video = package_root / "editable.mp4"
    editable_intro_report = compose_brand_intro(project, clean_body, editable_video)
    body_offset = max(0.0, float(editable_intro_report.get("lead_in_seconds") or 0.0))

    timeline_rows: list[dict] = []
    if brand_mode == BRAND_MODE_LEGACY_FULL:
        timeline_rows.append(
            {
                "index": 0,
                "scene_id": "brand-intro",
                "kind": "intro",
                "start": 0.0,
                "end": round(float(editable_intro_report.get("source_duration") or 0.0), 3),
                "duration": round(float(editable_intro_report.get("source_duration") or 0.0), 3),
                "headline": "",
                "caption": "",
                "narration": "",
                "scene_clip": "brand-intro.mp4",
                "overlay_file": "",
                "audio_file": "embedded",
            }
        )
    srt_blocks: list[str] = []
    cursor = body_offset
    cue_index = 1
    for index, scene_info in enumerate(packaged_scenes, start=1):
        start = cursor
        end = start + float(scene_info["duration"])
        scene_info["timeline_start"] = round(start, 3)
        scene_info["timeline_end"] = round(end, 3)
        timeline_rows.append(
            {
                "index": index,
                "scene_id": scene_info["id"],
                "kind": "news-scene",
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": scene_info["duration"],
                "headline": scene_info["headline"],
                "caption": scene_info["caption"],
                "narration": scene_info["narration"],
                "scene_clip": scene_info["scene_clip"],
                "overlay_file": scene_info["overlay_file"] or "",
                "audio_file": scene_info["audio_file"],
            }
        )
        if scene_info["narration"] and scene_info["external_caption"]:
            srt_blocks.append(
                f"{cue_index}\n{srt_timestamp(start)} --> {srt_timestamp(end)}\n"
                f"{scene_info['narration']}\n"
            )
            cue_index += 1
        cursor = end
        if packaged_mid_cta and index == mid_insert_after_index:
            mid_duration = float(mid_cta_report.get("duration") or 0.0)
            mid_end = cursor + mid_duration
            timeline_rows.append(
                {
                    "index": index + 0.5,
                    "scene_id": "mid-cta",
                    "kind": "mid-cta",
                    "start": round(cursor, 3),
                    "end": round(mid_end, 3),
                    "duration": round(mid_duration, 3),
                    "headline": str(mid_cta_report.get("headline") or ""),
                    "caption": " · ".join(
                        value
                        for value in (
                            str(mid_cta_report.get("emphasis") or "").strip(),
                            str(mid_cta_report.get("subline") or "").strip(),
                        )
                        if value
                    ),
                    "narration": str(mid_cta_report.get("narration") or ""),
                    "scene_clip": packaged_mid_cta.relative_to(package_root).as_posix(),
                    "overlay_file": "",
                    "audio_file": (
                        packaged_mid_cta_audio.relative_to(package_root).as_posix()
                        if packaged_mid_cta_audio
                        else "embedded"
                    ),
                }
            )
            cursor = mid_end

    if packaged_cta:
        cta_duration = float(cta_report.get("duration") or 0.0)
        cta_end = cursor + cta_duration
        cta_narration = suppress_editorial_identifiers(str(cta_report.get("narration") or ""))
        timeline_rows.append(
            {
                "index": len(packaged_scenes) + 1,
                "scene_id": "cta-tail",
                "kind": "cta",
                "start": round(cursor, 3),
                "end": round(cta_end, 3),
                "duration": round(cta_duration, 3),
                "headline": str(cta_report.get("headline") or ""),
                "caption": str(cta_report.get("prompt") or ""),
                "narration": cta_narration,
                "scene_clip": packaged_cta.relative_to(package_root).as_posix(),
                "overlay_file": "",
                "audio_file": (
                    packaged_cta_audio.relative_to(package_root).as_posix()
                    if packaged_cta_audio
                    else "embedded"
                ),
            }
        )
        if cta_narration:
            srt_blocks.append(
                f"{cue_index}\n{srt_timestamp(cursor)} --> {srt_timestamp(cta_end)}\n"
                f"{cta_narration}\n"
            )

    (package_root / "captions.srt").write_text(
        "\n".join(srt_blocks),
        encoding="utf-8",
    )
    timeline_fields = [
        "index",
        "scene_id",
        "kind",
        "start",
        "end",
        "duration",
        "headline",
        "caption",
        "narration",
        "scene_clip",
        "overlay_file",
        "audio_file",
    ]
    with (package_root / "timeline.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=timeline_fields)
        writer.writeheader()
        writer.writerows(timeline_rows)

    for metadata_name in (
        "storyboard.json",
        "rights-manifest.json",
        "sources.json",
        SOURCE_AUDIO_REVIEW_FILENAME,
    ):
        source = project_dir / metadata_name
        if source.is_file():
            shutil.copy2(source, metadata_dir / metadata_name)

    guide = """news2shorts 편집 호환 패키지

CapCut Desktop/Web
1. editable.mp4를 새 프로젝트에 가져옵니다.
2. captions.srt를 자막 파일로 가져옵니다.
3. 장면별 교체가 필요하면 scenes 폴더의 MP4를 사용합니다.

Vrew
1. editable.mp4로 새 영상 프로젝트를 만듭니다.
2. 자막 파일 불러오기가 가능한 버전에서는 captions.srt를 가져옵니다.
3. 원래 화면 구성이 필요하면 overlays PNG를 해당 장면 위에 배치합니다.

reference.mp4는 플러그인의 완성 화면 비교용입니다.
외부 편집기의 변경 사항은 storyboard.json으로 자동 역수입되지 않습니다.
"""
    (package_root / "사용방법.txt").write_text(guide, encoding="utf-8")

    manifest = {
        "version": EDITOR_PACKAGE_VERSION,
        "generated_at": iso_now(),
        "mode": "one-way-export",
        "round_trip_supported": False,
        "compatibility": ["CapCut Desktop", "CapCut Web", "Vrew", "SRT-compatible editors"],
        "canvas": {"width": OUTPUT_VIDEO_SIZE[0], "height": OUTPUT_VIDEO_SIZE[1], "fps": 30},
        "reference_video": "reference.mp4",
        "editable_video": "editable.mp4",
        "captions": "captions.srt",
        "timeline": "timeline.csv",
        "intro": "brand-intro.mp4" if brand_mode == BRAND_MODE_LEGACY_FULL else None,
        "brand_logo": "brand-logo.png" if brand_mode == BRAND_MODE_CORNER_LOGO else None,
        "brand_mode": brand_mode,
        "intro_body_offset": round(body_offset, 3),
        "background_music": (
            packaged_background_music.relative_to(package_root).as_posix()
            if packaged_background_music
            else None
        ),
        "mid_cta": (
            packaged_mid_cta.relative_to(package_root).as_posix()
            if packaged_mid_cta
            else None
        ),
        "cta": packaged_cta.relative_to(package_root).as_posix() if packaged_cta else None,
        "scene_count": len(packaged_scenes),
        "scenes": packaged_scenes,
        "notes": [
            "editable.mp4는 뉴스 장면의 고정 텍스트 오버레이를 제거한 편집용 영상입니다.",
            "overlays PNG의 글자는 이미지이므로 편집기에서 문구 자체를 수정할 수 없습니다.",
            "권리와 출처 기록은 metadata 폴더에 보존됩니다.",
        ],
    }
    write_json(package_root / "edit-manifest.json", manifest)

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not overwrite:
            raise News2ShortsError(
                f"편집 호환 패키지가 이미 있습니다: {target}. 덮어쓰려면 --overwrite를 사용하세요."
            )
        shutil.rmtree(target)
    shutil.move(str(package_root), str(target))

    relative_target = target.relative_to(project_dir).as_posix()
    editable_info = probe_video(target / "editable.mp4")
    return {
        "enabled": True,
        "version": EDITOR_PACKAGE_VERSION,
        "path": relative_target,
        "reference_video": f"{relative_target}/reference.mp4",
        "editable_video": f"{relative_target}/editable.mp4",
        "captions": f"{relative_target}/captions.srt",
        "timeline": f"{relative_target}/timeline.csv",
        "mid_cta": (
            f"{relative_target}/scenes/mid-cta.mp4" if packaged_mid_cta else None
        ),
        "scene_count": len(packaged_scenes),
        "compatibility": manifest["compatibility"],
        "round_trip_supported": False,
        "video": editable_info,
    }


def payoff_discussion_prompt(storyboard: dict) -> str:
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list):
        return ""
    for scene in reversed(scenes):
        if not isinstance(scene, dict) or str(scene.get("beat") or "").strip() == "loop":
            continue
        return str(scene.get("discussion_prompt") or "").strip()
    return ""


def mid_cta_config(project: dict) -> dict:
    configured = project.get("mid_cta")
    result = {
        "mode": "disabled",
        "placement": MID_CTA_PLACEMENT,
        "min_duration": MID_CTA_MIN_DURATION,
        "max_duration": MID_CTA_MAX_DURATION,
        "style": MID_CTA_STYLE,
        "voice_enabled": True,
        "voice_delivery": "verdict",
        "sfx_enabled": True,
        "ui_target_profile": MID_CTA_UI_TARGET_PROFILE,
        "arrow_target": {
            "x": MID_CTA_DEFAULT_TARGET_X,
            "y": MID_CTA_DEFAULT_TARGET_Y,
        },
        "ordinary_copy": {
            "headline": "보고 계신데...",
            "emphasis": "구독은 아직이네요",
            "subline": "채널명 옆 구독, 한 번만",
            "narration": "구독은 아직이네요.",
        },
        "sensitive_copy": {
            "headline": "잠깐만요",
            "emphasis": "구독은 아직",
            "subline": "채널명 옆 구독, 한 번만",
            "narration": "구독 한 번만 부탁드려요.",
        },
    }
    if not isinstance(configured, dict):
        return result
    for key in (
        "mode",
        "placement",
        "min_duration",
        "max_duration",
        "style",
        "voice_enabled",
        "voice_delivery",
        "sfx_enabled",
        "ui_target_profile",
    ):
        if key in configured:
            result[key] = configured[key]
    for key in ("arrow_target", "ordinary_copy", "sensitive_copy"):
        value = configured.get(key)
        if isinstance(value, dict):
            merged = dict(result[key])
            merged.update(value)
            result[key] = merged
    return result


def select_mid_cta(
    project: dict,
    scenes: list[dict],
    scene_reports: list[dict],
) -> dict:
    try:
        project_version = int(project.get("version") or 1)
    except (TypeError, ValueError):
        project_version = 1
    config = mid_cta_config(project)
    mode = str(config.get("mode") or "disabled").strip().lower()
    base = {
        "enabled": False,
        "mode": mode,
        "placement": str(config.get("placement") or MID_CTA_PLACEMENT),
    }
    if project_version < 17:
        return {**base, "reason": "version 16 이하 프로젝트는 중간 CTA를 자동 적용하지 않습니다."}
    if mode == "disabled":
        return {**base, "reason": "사용자가 중간 CTA를 제외했습니다."}
    if str(project.get("delivery_mode") or "").strip() != CONTINUOUS_FLOW_MODE:
        return {**base, "reason": "visual-first에는 중간 음성 CTA를 넣지 않습니다."}
    if not scene_reports:
        return {**base, "reason": "렌더된 뉴스 장면이 없습니다."}
    body_duration = max(
        0.0,
        float(scene_reports[-1].get("timeline_end") or 0.0),
    )
    if body_duration < MID_CTA_MIN_BODY_SECONDS:
        return {
            **base,
            "reason": f"뉴스 본문이 {MID_CTA_MIN_BODY_SECONDS:.0f}초 미만입니다.",
            "body_duration": round(body_duration, 3),
        }
    candidates: list[tuple[float, int, dict, dict]] = []
    for index, (scene, report) in enumerate(zip(scenes, scene_reports), start=1):
        beat = str(scene.get("beat") or "").strip()
        boundary = float(report.get("timeline_end") or 0.0)
        ratio = boundary / body_duration if body_duration else 0.0
        if (
            beat in MID_CTA_ALLOWED_BEATS
            and MID_CTA_TARGET_MIN_RATIO <= ratio <= MID_CTA_TARGET_MAX_RATIO
        ):
            candidates.append((abs(ratio - MID_CTA_TARGET_RATIO), index, scene, report))
    if not candidates:
        return {
            **base,
            "reason": "본문 40~60% 구간에 rehook 또는 turn 경계가 없습니다.",
            "body_duration": round(body_duration, 3),
        }
    _, scene_index, scene, report = min(candidates, key=lambda item: (item[0], item[1]))
    copy_key = "sensitive_copy" if project.get("sensitive_topic") is True else "ordinary_copy"
    copy = config.get(copy_key)
    assert isinstance(copy, dict)
    target = config.get("arrow_target")
    assert isinstance(target, dict)
    return {
        "enabled": True,
        "mode": mode,
        "placement": MID_CTA_PLACEMENT,
        "reason": "본문 중앙에 가장 가까운 rehook 또는 turn 장면 뒤에 배치했습니다.",
        "insert_after_scene_id": str(scene.get("id") or f"scene-{scene_index:02d}"),
        "insert_after_scene_index": scene_index,
        "body_duration": round(body_duration, 3),
        "boundary_ratio": round(float(report.get("timeline_end") or 0.0) / body_duration, 4),
        "headline": str(copy.get("headline") or "").strip(),
        "emphasis": str(copy.get("emphasis") or "").strip(),
        "subline": str(copy.get("subline") or "").strip(),
        "narration": str(copy.get("narration") or "").strip(),
        "min_duration": float(config.get("min_duration") or MID_CTA_MIN_DURATION),
        "max_duration": float(config.get("max_duration") or MID_CTA_MAX_DURATION),
        "style": str(config.get("style") or MID_CTA_STYLE),
        "voice_enabled": config.get("voice_enabled") is not False,
        "voice_delivery": str(config.get("voice_delivery") or "verdict"),
        "sfx_enabled": config.get("sfx_enabled") is not False,
        "ui_target_profile": str(config.get("ui_target_profile") or MID_CTA_UI_TARGET_PROFILE),
        "arrow_target": {
            "x": float(target.get("x", MID_CTA_DEFAULT_TARGET_X)),
            "y": float(target.get("y", MID_CTA_DEFAULT_TARGET_Y)),
        },
    }


def brand_close_selection(mid_cta_report: dict) -> dict:
    return {
        "enabled": True,
        "variant": "brand-close",
        "headline": "뉴스한면",
        "prompt": "다음 소식도 바로",
        "narration": "",
        "discussion_prompt": "",
        "selection_strategy": "mid-cta-brand-close-v1",
        "selection_reason": "중간 CTA에서 구독을 요청해 마지막에는 브랜드 마감만 사용합니다.",
        "distribution": None,
        "distribution_basis": None,
        "distribution_bucket": None,
        "duration": BRAND_CLOSE_DURATION,
        "voice_enabled": False,
        "style": "common-dark-yellow",
        "mid_cta_insert_after_scene_id": mid_cta_report.get("insert_after_scene_id"),
    }


def select_cta_tail_variant(project: dict, storyboard: dict) -> dict:
    config = project.get("cta_tail")
    if not isinstance(config, dict) or config.get("enabled") is not True:
        return {"enabled": False}

    discussion_prompt = payoff_discussion_prompt(storyboard)
    bucket: int | None = None
    distribution: str | None = None
    distribution_basis: str | None = None
    if project.get("sensitive_topic") is True:
        variant = "subscribe"
        reason = "민감 뉴스에서는 일반 참여 질문 대신 중립적인 빠른 소식 CTA를 사용합니다."
    elif discussion_prompt:
        variant = "comment"
        reason = "결론에 검증된 주제별 discussion_prompt가 있어 댓글 CTA로 이어갑니다."
    else:
        seed = "\x1f".join(
            [
                "cta-tail-v1",
                *(str(project.get(field) or "") for field in ("slug", "source_url", "created_at", "title")),
            ]
        )
        bucket = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % len(
            CTA_TAIL_VARIANTS
        )
        variant = CTA_TAIL_VARIANTS[bucket]
        reason = "주제별 질문이 없어 프로젝트 고정 1:1 기본 배분으로 CTA를 선택했습니다."
        distribution = CTA_TAIL_DEFAULT_DISTRIBUTION
        distribution_basis = CTA_TAIL_DEFAULT_DISTRIBUTION_BASIS

    if variant == "comment":
        headline = discussion_prompt or str(
            config.get("comment_headline") or DEFAULT_COMMENT_CTA_HEADLINE
        ).strip()
        prompt = str(config.get("comment_prompt") or DEFAULT_COMMENT_CTA_PROMPT).strip()
        narration = str(
            config.get("comment_narration") or DEFAULT_COMMENT_CTA_NARRATION
        ).strip()
        if not discussion_prompt:
            narration = DEFAULT_COMMENT_CTA_FALLBACK_NARRATION
    else:
        headline = str(config.get("headline") or "빠른 소식 계속").strip()
        prompt = str(config.get("prompt") or "구독 · 좋아요").strip()
        narration = str(config.get("narration") or DEFAULT_CTA_NARRATION).strip()

    return {
        "enabled": True,
        "variant": variant,
        "headline": headline,
        "prompt": prompt,
        "narration": narration,
        "discussion_prompt": discussion_prompt,
        "selection_strategy": CTA_TAIL_SELECTION_STRATEGY,
        "selection_reason": reason,
        "distribution": distribution,
        "distribution_basis": distribution_basis,
        "distribution_bucket": bucket,
    }


def select_tail_after_mid_cta(
    project: dict,
    storyboard: dict,
    mid_cta_report: dict,
) -> dict:
    config = project.get("cta_tail")
    if not isinstance(config, dict) or config.get("keep_after_mid_cta") is not True:
        return brand_close_selection(mid_cta_report)
    selection = select_cta_tail_variant(project, storyboard)
    if selection.get("enabled") is not True:
        return selection
    selection.update(
        {
            "selection_strategy": CTA_TAIL_AFTER_MID_SELECTION_STRATEGY,
            "selection_reason": (
                "사용자가 중간 구독 CTA와 별도의 마지막 CTA를 모두 요청해 함께 유지합니다."
            ),
            "mid_cta_insert_after_scene_id": mid_cta_report.get("insert_after_scene_id"),
        }
    )
    return selection


def create_cta_audio(path: Path, duration: float) -> None:
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=660:sample_rate=48000:duration=0.14",
            "-t",
            f"{duration:.3f}",
            "-af",
            "volume=0.05,afade=t=out:st=0.08:d=0.06,apad",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ]
    )


def create_brand_close_audio(path: Path, duration: float) -> None:
    second_ms = max(180, round(max(0.25, duration - 0.25) * 1000))
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=620:sample_rate=48000:duration=0.11",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=760:sample_rate=48000:duration=0.10",
            "-filter_complex",
            f"[0:a]volume=0.35,afade=t=out:st=0.06:d=0.05[a1];"
            f"[1:a]volume=0.25,afade=t=out:st=0.05:d=0.05,adelay={second_ms}|{second_ms}[a2];"
            f"[a1][a2]amix=inputs=2:duration=longest,apad,atrim=duration={duration:.3f}[a]",
            "-map",
            "[a]",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ]
    )


def create_mid_cta_sfx(path: Path, duration: float) -> None:
    arrival_ms = max(0, round(min(1.0, max(0.45, duration - 0.45)) * 1000))
    second_ms = arrival_ms + 70
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=720:sample_rate=48000:duration=0.07",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1080:sample_rate=48000:duration=0.05",
            "-filter_complex",
            f"[0:a]volume=0.055,adelay={arrival_ms}|{arrival_ms}[a1];"
            f"[1:a]volume=0.03,adelay={second_ms}|{second_ms}[a2];"
            f"[a1][a2]amix=inputs=2:duration=longest,apad,atrim=duration={duration:.3f}[a]",
            "-map",
            "[a]",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ]
    )


def mix_mid_cta_audio(
    voice_audio: Path | None,
    sfx_audio: Path,
    destination: Path,
    duration: float,
) -> None:
    if voice_audio is None:
        normalize_editor_audio(sfx_audio, destination)
        return
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(voice_audio),
            "-i",
            str(sfx_audio),
            "-filter_complex",
            f"[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"apad,atrim=duration={duration:.3f}[voice];"
            f"[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"apad,atrim=duration={duration:.3f}[sfx];"
            "[voice][sfx]amix=inputs=2:duration=longest:normalize=0,"
            f"alimiter=limit=0.95,atrim=duration={duration:.3f}[a]",
            "-map",
            "[a]",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(destination),
        ]
    )


def render_mid_cta_frames(selection: dict, frames_dir: Path, duration: float) -> int:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise News2ShortsError("중간 CTA 렌더에는 Pillow가 필요합니다.") from exc
    frames_dir.mkdir(parents=True, exist_ok=True)
    width, height = OUTPUT_VIDEO_SIZE
    fps = 30
    frame_count = max(1, round(duration * fps))
    font_path = find_font()
    headline_font = load_font_face(font_path, 41, bold=True)
    emphasis_font = load_font_face(font_path, 61, bold=True)
    subline_font = load_font_face(font_path, 38, bold=True)
    logo = Image.open(BRAND_LOGO_PATH).convert("RGBA").resize((68, 68))
    target = selection.get("arrow_target") if isinstance(selection.get("arrow_target"), dict) else {}
    target_x = min(0.50, max(0.18, float(target.get("x", MID_CTA_DEFAULT_TARGET_X)))) * width
    target_y = min(0.92, max(0.78, float(target.get("y", MID_CTA_DEFAULT_TARGET_Y)))) * height

    def centered_text(draw, text: str, font, y: int, fill: tuple[int, int, int, int]) -> None:
        box = draw.textbbox((0, 0), text, font=font)
        draw.text(((width - (box[2] - box[0])) // 2, y), text, font=font, fill=fill)

    for frame_index in range(frame_count):
        second = frame_index / fps
        canvas = Image.new("RGBA", (width, height), "#090A0C")
        canvas.alpha_composite(logo, (24, 24))
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        fade_in = min(1.0, second / 0.12)
        fade_out = min(1.0, max(0.0, duration - second) / 0.15)
        alpha = max(0, min(255, round(255 * min(fade_in, fade_out))))
        draw.rounded_rectangle(
            (74, 265, 646, 835),
            radius=46,
            fill=(17, 21, 26, alpha),
            outline=(43, 49, 57, alpha),
            width=4,
        )
        draw.rounded_rectangle((286, 338, 434, 350), radius=6, fill=(255, 242, 0, alpha))
        centered_text(draw, str(selection.get("headline") or ""), headline_font, 420, (255, 255, 255, alpha))
        centered_text(draw, str(selection.get("emphasis") or ""), emphasis_font, 515, (255, 242, 0, alpha))
        centered_text(draw, str(selection.get("subline") or ""), subline_font, 655, (255, 255, 255, alpha))
        progress = min(1.0, max(0.0, (second - 0.25) / max(0.20, duration - 0.65)))
        eased = 1.0 - (1.0 - progress) ** 3
        start_x, start_y = 410.0, 785.0
        arrow_x = start_x + (target_x - start_x) * eased
        arrow_y = start_y + (target_y - start_y) * eased + 8.0 * math.sin(progress * 4.0 * math.pi)
        draw.line(
            (arrow_x, arrow_y - 58, arrow_x, arrow_y),
            fill=(255, 242, 0, alpha),
            width=16,
        )
        draw.polygon(
            [
                (arrow_x - 28, arrow_y - 15),
                (arrow_x + 28, arrow_y - 15),
                (arrow_x, arrow_y + 22),
            ],
            fill=(255, 242, 0, alpha),
        )
        if progress > 0.72:
            ring_progress = min(1.0, (progress - 0.72) / 0.18)
            ring_alpha = round(alpha * ring_progress * (1.0 - max(0.0, progress - 0.92) / 0.08))
            draw.ellipse(
                (target_x - 60, target_y - 44, target_x + 60, target_y + 44),
                outline=(255, 242, 0, max(0, ring_alpha)),
                width=7,
            )
        output = Image.alpha_composite(canvas, layer).convert("RGB")
        output.save(frames_dir / f"{frame_index:04d}.png", format="PNG", compress_level=3)
    return frame_count


def render_mid_cta(
    selection: dict,
    work_dir: Path,
    destination: Path,
    *,
    no_tts: bool,
    tts_provider: str,
    voice: str,
    rate: int,
    typecast_voice_id: str,
    typecast_voice_name: str,
    typecast_tempo: float,
    previous_text: str,
    next_text: str,
) -> tuple[dict, Path]:
    if selection.get("enabled") is not True:
        return selection, work_dir / "mid-cta-none.wav"
    narration = suppress_editorial_identifiers(str(selection.get("narration") or "").strip())
    voice_enabled = selection.get("voice_enabled") is not False
    voice_audio: Path | None = None
    rendered_voice_id: str | None = None
    rendered_voice_name: str | None = None
    audio_source = "original-synthetic-tone"
    measured_voice = 0.0
    if voice_enabled and narration and not no_tts and tts_provider == "typecast":
        voice_audio = work_dir / "mid-cta-typecast.wav"
        typecast_audio(
            voice_audio,
            narration,
            voice_id=typecast_voice_id,
            tempo=typecast_tempo,
            previous_text=previous_text,
            next_text=next_text,
            delivery=str(selection.get("voice_delivery") or "verdict"),
        )
        measured_voice = audio_duration(voice_audio)
        rendered_voice_id = typecast_voice_id
        rendered_voice_name = typecast_voice_name
        audio_source = "typecast+original-synthetic-tone"
    elif voice_enabled and narration and not no_tts and tts_provider == "local":
        say = shutil.which("say")
        if not say:
            raise News2ShortsError("중간 CTA 음성을 만들 로컬 TTS를 찾지 못했습니다.")
        voice_audio = work_dir / "mid-cta-local.aiff"
        run_command([say, "-v", voice, "-r", str(rate), "-o", str(voice_audio), narration])
        measured_voice = audio_duration(voice_audio)
        rendered_voice_name = voice
        audio_source = "local+original-synthetic-tone"
    min_duration = float(selection.get("min_duration") or MID_CTA_MIN_DURATION)
    max_duration = float(selection.get("max_duration") or MID_CTA_MAX_DURATION)
    duration = max(min_duration, measured_voice + MID_CTA_AUDIO_TAIL_SECONDS)
    if duration > max_duration + 0.01:
        raise News2ShortsError(
            f"중간 CTA 음성이 {max_duration:.1f}초 안에 들어오지 않습니다. 문구를 더 짧게 작성하세요."
        )
    duration = min(max_duration, duration)
    sfx_audio = work_dir / "mid-cta-sfx.wav"
    if selection.get("sfx_enabled") is False:
        create_silent_audio(sfx_audio, duration)
    else:
        create_mid_cta_sfx(sfx_audio, duration)
    audio = work_dir / "mid-cta.wav"
    mix_mid_cta_audio(voice_audio, sfx_audio, audio, duration)
    frames_dir = work_dir / "mid-cta-frames"
    frame_count = render_mid_cta_frames(selection, frames_dir, duration)
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            "30",
            "-i",
            str(frames_dir / "%04d.png"),
            "-i",
            str(audio),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ]
    )
    report = dict(selection)
    report.update(
        {
            "duration": round(duration, 3),
            "narration": narration,
            "audio": audio_source,
            "audio_duration": round(audio_duration(audio), 3),
            "voice_id": rendered_voice_id,
            "voice_name": rendered_voice_name,
            "frame_count": frame_count,
            "fps": 30,
            "srt_generated": False,
            "fake_button_rendered": False,
        }
    )
    return report, audio


def render_cta_tail(
    project: dict,
    selection: dict,
    work_dir: Path,
    destination: Path,
    *,
    no_tts: bool,
    tts_provider: str,
    voice: str,
    rate: int,
    typecast_voice_id: str,
    typecast_voice_name: str,
    typecast_tempo: float,
    previous_text: str,
) -> dict:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise News2ShortsError("CTA 테일 렌더에는 Pillow가 필요합니다.") from exc

    config = project.get("cta_tail")
    if (
        not isinstance(config, dict)
        or config.get("enabled") is not True
        or selection.get("enabled") is not True
    ):
        return {"enabled": False}
    configured_duration = min(
        MAX_CTA_TAIL_DURATION,
        max(
            MIN_CTA_TAIL_DURATION,
            float(selection.get("duration") or config.get("duration") or DEFAULT_CTA_TAIL_DURATION),
        ),
    )
    headline = suppress_editorial_identifiers(str(selection.get("headline") or "").strip())
    prompt = suppress_editorial_identifiers(str(selection.get("prompt") or "").strip())
    narration = suppress_editorial_identifiers(str(selection.get("narration") or "").strip())
    voice_enabled = selection.get("voice_enabled", config.get("voice_enabled")) is not False
    width, height = OUTPUT_VIDEO_SIZE
    canvas = Image.new("RGB", (width, height), "#090A0C")
    draw = ImageDraw.Draw(canvas)
    font_path = find_font()
    headline_font = load_font_face(font_path, 54, bold=True)
    prompt_font = load_font_face(font_path, 76, bold=True)
    accent = "#FFF200"
    draw.rounded_rectangle((72, 360, width - 72, 920), radius=42, fill="#11151A", outline="#272D35", width=3)
    draw.rounded_rectangle((272, 430, width - 272, 446), radius=8, fill=accent)
    headline_lines = wrap_text(draw, headline, headline_font, width - 180)[:2]
    draw_centered_lines(
        draw,
        headline_lines,
        headline_font,
        520,
        "#FFFFFF",
        spacing=12,
        canvas_width=width,
    )
    prompt_lines = wrap_text(draw, prompt, prompt_font, width - 140)[:1]
    draw_centered_lines(
        draw,
        prompt_lines,
        prompt_font,
        700,
        accent,
        spacing=8,
        canvas_width=width,
    )
    draw.rounded_rectangle((210, 1000, width - 210, 1006), radius=3, fill="#343B45")
    frame = work_dir / "cta-tail.png"
    canvas.save(frame, format="PNG", optimize=True)

    duration = configured_duration
    audio_source = "original-synthetic-tone"
    rendered_voice_id: str | None = None
    rendered_voice_name: str | None = None
    if voice_enabled and narration and not no_tts and tts_provider == "typecast":
        audio = work_dir / "cta-tail-typecast.wav"
        typecast_audio(
            audio,
            narration,
            voice_id=typecast_voice_id,
            tempo=typecast_tempo,
            previous_text=previous_text,
            next_text="",
        )
        measured_audio = audio_duration(audio)
        audio_source = "typecast"
        rendered_voice_id = typecast_voice_id
        rendered_voice_name = typecast_voice_name
    elif voice_enabled and narration and not no_tts and tts_provider == "local":
        say = shutil.which("say")
        if not say:
            raise News2ShortsError("공통 CTA 음성을 만들 로컬 TTS를 찾지 못했습니다.")
        audio = work_dir / "cta-tail-local.aiff"
        run_command([say, "-v", voice, "-r", str(rate), "-o", str(audio), narration])
        measured_audio = audio_duration(audio)
        audio_source = "local"
        rendered_voice_name = voice
    else:
        audio = work_dir / "cta-tail-tone.wav"
        if str(selection.get("variant") or "") == "brand-close":
            create_brand_close_audio(audio, configured_duration)
        else:
            create_cta_audio(audio, configured_duration)
        measured_audio = audio_duration(audio)

    if audio_source in {"typecast", "local"}:
        required_duration = measured_audio + CTA_NARRATION_TAIL_SECONDS
        if required_duration > MAX_CTA_TAIL_DURATION:
            raise News2ShortsError(
                "공통 CTA 음성이 6초를 넘습니다. cta_tail.narration을 더 짧게 작성하세요."
            )
        duration = max(configured_duration, required_duration)
    render_static_scene(frame, audio, destination, duration, motion="none", zoom_scale=1.0)
    return {
        "enabled": True,
        "variant": str(selection.get("variant") or "subscribe"),
        "duration": round(duration, 3),
        "headline": headline,
        "prompt": prompt,
        "narration": narration,
        "discussion_prompt": str(selection.get("discussion_prompt") or ""),
        "selection_strategy": str(selection.get("selection_strategy") or ""),
        "selection_reason": str(selection.get("selection_reason") or ""),
        "distribution": selection.get("distribution"),
        "distribution_basis": selection.get("distribution_basis"),
        "distribution_bucket": selection.get("distribution_bucket"),
        "voice_enabled": voice_enabled,
        "style": str(selection.get("style") or config.get("style") or "common-dark-yellow"),
        "audio": audio_source,
        "audio_duration": round(measured_audio, 3),
        "voice_id": rendered_voice_id,
        "voice_name": rendered_voice_name,
    }


def tag_to_title_hashtag(value: object) -> str:
    normalized = re.sub(r"\s+", "", str(value or "").strip().lstrip("#"))
    normalized = re.sub(r"[^0-9A-Za-z가-힣_]", "", normalized)
    return f"#{normalized}" if normalized else ""


def title_with_hashtags(title: str, tags: object) -> str:
    base = str(title or "").strip()
    if not base:
        return ""
    existing = {
        match.lower()
        for match in re.findall(r"#([0-9A-Za-z가-힣_]+)", base)
    }
    additions: list[str] = []
    if isinstance(tags, list):
        for tag in tags:
            hashtag = tag_to_title_hashtag(tag)
            key = hashtag.lstrip("#").lower()
            if not hashtag or key in existing:
                continue
            candidate = " ".join([base, *additions, hashtag])
            if len(candidate) > YOUTUBE_TITLE_LIMIT:
                continue
            additions.append(hashtag)
            existing.add(key)
            if len(additions) >= TITLE_HASHTAG_COUNT:
                break
    return " ".join([base, *additions])


def thumbnail_presenter_asset(
    project_dir: Path,
    manifest: dict,
    settings: dict,
    *,
    required: bool = False,
) -> tuple[Path, dict] | None:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        assets = []
    requested = str(settings.get("thumbnail_presenter_file") or "").strip()
    candidates = [
        record
        for record in assets
        if isinstance(record, dict)
        and (
            str(record.get("path") or "").strip() == requested
            if requested
            else str(record.get("usage_role") or "").strip() == THUMBNAIL_PRESENTER_USAGE_ROLE
        )
    ]
    if not candidates:
        if required or requested:
            raise News2ShortsError(
                "presenter-led 썸네일에는 rights-manifest에서 승인된 thumbnail-presenter 자산이 필요합니다."
            )
        return None
    record = candidates[0]
    path_value = str(record.get("path") or "").strip()
    if record.get("approved") is not True:
        raise News2ShortsError("썸네일 진행자 자산의 권리 승인이 완료되지 않았습니다.")
    if str(record.get("usage_role") or "").strip() != THUMBNAIL_PRESENTER_USAGE_ROLE:
        raise News2ShortsError("썸네일 진행자 자산은 usage_role=thumbnail-presenter여야 합니다.")
    if record.get("presenter_context_reviewed") is not True or record.get("case_party") is not False:
        raise News2ShortsError(
            "썸네일 진행자 자산은 presenter_context_reviewed=true, case_party=false로 사건 당사자가 아님을 확인해야 합니다."
        )
    if record.get("synthetic") is True and record.get("visual_quality_reviewed") is not True:
        raise News2ShortsError("합성 썸네일 진행자 자산은 visual_quality_reviewed=true가 필요합니다.")
    path = resolve_project_file(project_dir, path_value)
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise News2ShortsError("썸네일 진행자 자산은 JPG, PNG 또는 WebP 정지 이미지여야 합니다.")
    return path, record


def thumbnail_source_paths(
    project_dir: Path,
    storyboard: dict,
    manifest: dict,
) -> list[Path]:
    scenes = [scene for scene in storyboard.get("scenes", []) if isinstance(scene, dict)]
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        assets = []
    approved_paths = {
        str(record.get("path") or "").strip()
        for record in assets
        if isinstance(record, dict) and record.get("approved") is True
    }
    preferred: list[dict] = []
    if scenes:
        preferred.append(scenes[0])
    preferred.extend(
        scene
        for scene in scenes
        if str(scene.get("beat") or "") in {"turn", "rehook", "evidence"}
    )
    if scenes:
        preferred.append(scenes[-1])
    preferred.extend(scenes)

    selected: list[Path] = []
    seen: set[str] = set()
    for scene in preferred:
        value = str(scene.get("image") or "").strip()
        if not value or value in seen or value not in approved_paths:
            continue
        path = resolve_project_file(project_dir, value)
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        selected.append(path)
        seen.add(value)
        if len(selected) == 3:
            break
    if len(selected) < 2:
        raise News2ShortsError(
            "합성 썸네일에는 서로 다른 권리 승인 이미지가 최소 2개 필요합니다. "
            "storyboard와 rights-manifest를 보완하세요."
        )
    return selected


def render_composite_thumbnail(
    project_dir: Path,
    project: dict,
    storyboard: dict,
    manifest: dict,
    publish: dict,
    *,
    output_name: str = DEFAULT_THUMBNAIL_PATH,
    overwrite: bool = False,
) -> dict:
    try:
        from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
    except ImportError as exc:
        raise News2ShortsError("합성 썸네일 생성에는 Pillow가 필요합니다.") from exc

    output = resolve_project_file(project_dir, output_name, must_exist=False)
    if output.suffix.lower() not in {".jpg", ".jpeg"}:
        raise News2ShortsError("합성 썸네일 출력은 .jpg 또는 .jpeg 파일이어야 합니다.")
    if output.exists() and not overwrite:
        raise News2ShortsError(f"썸네일 파일이 이미 있습니다: {output}. 덮어쓰려면 --overwrite를 사용하세요.")

    settings = publish.get("upload_settings")
    if not isinstance(settings, dict):
        settings = {}
        publish["upload_settings"] = settings
    scenes = [scene for scene in storyboard.get("scenes", []) if isinstance(scene, dict)]
    first_scene = scenes[0] if scenes else {}
    style = visual_style_config(project)
    profile = shorts_profile_config(project)
    hook = suppress_editorial_identifiers(
        str(
            settings.get("thumbnail_hook")
            or profile.get("tension_question")
            or profile.get("hook")
            or style.get("display_headline")
            or first_scene.get("headline")
            or "이 결정, 시민에게 맞는 걸까요?"
        ).strip()
    )
    subhook = suppress_editorial_identifiers(
        str(
            settings.get("thumbnail_subhook")
            or first_scene.get("caption")
            or profile.get("viewer_stake")
            or profile.get("payoff")
            or "결정 뒤의 시민 영향"
        ).strip()
    )
    badge = suppress_editorial_identifiers(
        str(settings.get("thumbnail_badge") or "잠깐, 이 조건?").strip()
    )
    requested_thumbnail_style = str(settings.get("thumbnail_style") or "auto").strip().lower()
    if requested_thumbnail_style not in THUMBNAIL_STYLES:
        raise News2ShortsError(
            "thumbnail_style은 auto, presenter-led, evidence-led 중 하나여야 합니다."
        )
    try:
        project_version = int(project.get("version") or 1)
    except (TypeError, ValueError):
        project_version = 1
    if project_version >= 9 and not ends_with_question(hook):
        raise News2ShortsError(
            "새 프로젝트의 별도 썸네일은 시민 관점의 질문형 thumbnail_hook이 필요합니다."
        )
    normalized_badge = re.sub(r"\s+", "", badge)
    if project_version >= 13 and (
        not 3 <= len(normalized_badge) <= 14
        or normalized_badge in GENERIC_THUMBNAIL_BADGES
    ):
        raise News2ShortsError(
            "thumbnail_badge는 일반 감탄어가 아닌 3-14자의 주제별 조건·비용·공백·반전이어야 합니다."
        )
    thumbnail_status = str(settings.get("thumbnail_status") or "").strip()
    thumbnail_file = str(settings.get("thumbnail_file") or "").strip()
    if thumbnail_status == "blocked_rights" and not thumbnail_file:
        return {
            "status": "blocked_rights",
            "path": "",
            "hook": hook,
            "subhook": subhook,
            "badge": badge,
            "source_assets": [],
            "reason": str(settings.get("thumbnail_note") or "권리 승인 이미지가 필요합니다."),
            "thumbnail_style": requested_thumbnail_style,
            "presenter_used": False,
            "presenter_context_reviewed": False,
            "attention_first": True,
            "purpose": "dedicated-curiosity-thumbnail",
            "separate_asset": True,
            "question_led": True,
        }
    sources = thumbnail_source_paths(project_dir, storyboard, manifest)
    if project.get("sensitive_topic") is True and requested_thumbnail_style == "presenter-led":
        raise News2ShortsError("민감 뉴스는 진행자형 썸네일 대신 직접 근거 중심 썸네일을 사용하세요.")
    presenter_asset = None
    if project.get("sensitive_topic") is not True and requested_thumbnail_style != "evidence-led":
        presenter_asset = thumbnail_presenter_asset(
            project_dir,
            manifest,
            settings,
            required=requested_thumbnail_style == "presenter-led",
        )
    resolved_thumbnail_style = "presenter-led" if presenter_asset else "evidence-led"
    width, height = OUTPUT_VIDEO_SIZE
    canvas = Image.new("RGB", (width, height), "#090A0C")

    def cover(path: Path, size: tuple[int, int], centering: tuple[float, float]):
        with Image.open(path) as opened:
            source = ImageOps.exif_transpose(opened).convert("RGB")
        source = ImageEnhance.Contrast(source).enhance(1.08)
        return ImageOps.fit(source, size, method=Image.Resampling.LANCZOS, centering=centering)

    if presenter_asset:
        presenter_path, _presenter_record = presenter_asset
        background = cover(sources[0], (width, height), (0.5, 0.48))
        background = background.filter(ImageFilter.GaussianBlur(radius=18))
        background = ImageEnhance.Brightness(background).enhance(0.42)
        canvas.paste(background, (0, 0))
        split_x = 314
        canvas.paste(cover(sources[0], (split_x, height - 510), (0.5, 0.48)), (0, 510))
        canvas.paste(
            cover(presenter_path, (width - split_x, height - 510), (0.5, 0.28)),
            (split_x, 510),
        )
    elif len(sources) >= 3:
        canvas.paste(cover(sources[0], (width, 610), (0.5, 0.48)), (0, 0))
        canvas.paste(cover(sources[1], (width // 2, height - 610), (0.5, 0.5)), (0, 610))
        canvas.paste(cover(sources[2], (width - width // 2, height - 610), (0.5, 0.5)), (width // 2, 610))
    else:
        canvas.paste(cover(sources[0], (width, 640), (0.5, 0.48)), (0, 0))
        canvas.paste(cover(sources[1], (width, height - 640), (0.5, 0.5)), (0, 640))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    accent = "#FFF200"
    danger = "#E9262D"
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0, 62))
    divider_y = 502 if presenter_asset else 602
    draw.rectangle((0, divider_y, width, divider_y + 14), fill=accent)
    if presenter_asset:
        draw.rectangle((308, 510, 320, height), fill=accent)
    elif len(sources) >= 3:
        draw.rectangle((width // 2 - 6, 610, width // 2 + 6, height), fill=accent)
    draw.rounded_rectangle((34, 46, width - 34, 480), radius=34, fill=(3, 4, 6, 232), outline=accent, width=4)
    font_path = find_font()
    badge_font = load_font_face(font_path, 30, bold=True)
    badge_box = draw.textbbox((0, 0), badge, font=badge_font)
    badge_width = min(width - 116, max(190, badge_box[2] - badge_box[0] + 42))
    draw.rounded_rectangle((58, 72, 58 + badge_width, 126), radius=18, fill=danger)
    draw.text((79, 81), badge, font=badge_font, fill="#FFFFFF")

    headline_font, headline_lines = fitted_balanced_lines(
        draw,
        hook,
        font_path,
        width - 116,
        3,
        88,
        bold=True,
    )
    headline_y = 162
    for index, line in enumerate(headline_lines):
        box = draw.textbbox((0, 0), line, font=headline_font, stroke_width=4)
        line_width = box[2] - box[0]
        line_height = box[3] - box[1]
        draw.text(
            ((width - line_width) / 2, headline_y),
            line,
            font=headline_font,
            fill=accent if index == len(headline_lines) - 1 else "#FFFFFF",
            stroke_width=4,
            stroke_fill="#030303",
        )
        headline_y += line_height + 12

    draw.rounded_rectangle((34, 928, width - 34, 1198), radius=34, fill=(3, 4, 6, 238), outline="#FFFFFF", width=3)
    subhook_font, subhook_lines = fitted_balanced_lines(
        draw,
        subhook,
        font_path,
        width - 116,
        2,
        64,
        bold=True,
    )
    subhook_heights = [draw.textbbox((0, 0), line, font=subhook_font)[3] for line in subhook_lines]
    subhook_y = 1063 - (sum(subhook_heights) + max(0, len(subhook_lines) - 1) * 10) // 2
    draw_centered_lines(
        draw,
        subhook_lines,
        subhook_font,
        subhook_y,
        accent,
        spacing=10,
        canvas_width=width,
    )

    if presenter_asset:
        _presenter_path, presenter_record = presenter_asset
        presenter_label = (
            "가상 진행자 · 사건 당사자 아님"
            if presenter_record.get("synthetic") is True
            else "진행자 자료 이미지 · 사건 당사자 아님"
        )
        label_font = load_font_face(font_path, 18, bold=True)
        label_box = draw.textbbox((0, 0), presenter_label, font=label_font)
        label_width = label_box[2] - label_box[0] + 24
        label_x = width - label_width - 16
        draw.rounded_rectangle((label_x, 526, width - 16, 558), radius=10, fill=(0, 0, 0, 188))
        draw.text((label_x + 12, 532), presenter_label, font=label_font, fill="#FFFFFF")

    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="JPEG", quality=91, optimize=True, progressive=True)

    relative_output = output.relative_to(project_dir).as_posix()
    settings["thumbnail_method"] = "file_upload"
    settings["thumbnail_file"] = relative_output
    settings["thumbnail_status"] = "ready"
    settings["thumbnail_hook"] = hook
    settings["thumbnail_subhook"] = subhook
    settings["thumbnail_badge"] = badge
    settings["thumbnail_style"] = requested_thumbnail_style
    settings["thumbnail_note"] = f"별도 호기심 유도 썸네일 파일: {relative_output}"
    write_json(project_dir / "publish.json", publish)
    return {
        "path": relative_output,
        "width": width,
        "height": height,
        "hook": hook,
        "subhook": subhook,
        "badge": badge,
        "source_assets": [path.relative_to(project_dir).as_posix() for path in sources],
        "composition": (
            "presenter-led"
            if presenter_asset
            else "three-panel" if len(sources) >= 3 else "two-panel"
        ),
        "thumbnail_style": resolved_thumbnail_style,
        "presenter_used": presenter_asset is not None,
        "presenter_asset": (
            presenter_asset[0].relative_to(project_dir).as_posix() if presenter_asset else ""
        ),
        "presenter_context_reviewed": (
            presenter_asset[1].get("presenter_context_reviewed") is True if presenter_asset else False
        ),
        "attention_first": True,
        "purpose": "dedicated-curiosity-thumbnail",
        "separate_asset": True,
        "question_led": ends_with_question(hook),
    }


def cmd_thumbnail(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"프로젝트 디렉터리를 찾을 수 없습니다: {project_dir}")
    project = load_json(project_dir / "project.json")
    storyboard = load_json(project_dir / "storyboard.json")
    manifest = load_json(project_dir / "rights-manifest.json")
    publish = load_json(project_dir / "publish.json")
    if not all(isinstance(value, dict) for value in (project, storyboard, manifest, publish)):
        fail("썸네일 생성에 필요한 프로젝트 JSON 객체를 확인하세요.")
    report = render_composite_thumbnail(
        project_dir,
        project,
        storyboard,
        manifest,
        publish,
        output_name=args.output or DEFAULT_THUMBNAIL_PATH,
        overwrite=args.overwrite,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def validate_public_https_url(value: str, label: str) -> str:
    parsed = parse.urlsplit(value)
    hostname = (parsed.hostname or "").strip().lower()
    if parsed.scheme != "https" or not hostname or parsed.username or parsed.password:
        raise News2ShortsError(f"{label}은 공개 HTTPS URL이어야 합니다.")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        }
    except OSError as exc:
        raise News2ShortsError(f"{label} 호스트를 확인할 수 없습니다: {hostname}") from exc
    if not addresses:
        raise News2ShortsError(f"{label} 호스트 주소가 없습니다: {hostname}")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise News2ShortsError(f"{label}은 공개 인터넷 호스트여야 합니다: {hostname}")
    return value


class PublicImageRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        validate_public_https_url(newurl, "redirect URL")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_public_image(url: str) -> tuple[bytes, str, str]:
    validate_public_https_url(url, "image URL")
    opener = request.build_opener(
        request.ProxyHandler({}),
        PublicImageRedirectHandler(),
        request.HTTPSHandler(context=verified_ssl_context()),
    )
    req = request.Request(
        url,
        headers={
            "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*;q=0.8",
            "User-Agent": "news2shorts/0.36 public-image-review",
        },
        method="GET",
    )
    try:
        with opener.open(req, timeout=30) as response:
            final_url = response.geturl()
            validate_public_https_url(final_url, "final image URL")
            content_type = response.headers.get_content_type().lower()
            if not content_type.startswith("image/"):
                raise News2ShortsError(
                    f"인터넷 응답이 이미지가 아닙니다: {content_type or 'unknown'}"
                )
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_INTERNET_IMAGE_BYTES:
                raise News2ShortsError("인터넷 이미지가 25 MiB 제한을 초과합니다.")
            data = response.read(MAX_INTERNET_IMAGE_BYTES + 1)
    except error.HTTPError as exc:
        raise News2ShortsError(f"인터넷 이미지 요청 실패: HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise News2ShortsError(f"인터넷 이미지 연결 실패: {exc.reason}") from exc
    if len(data) > MAX_INTERNET_IMAGE_BYTES:
        raise News2ShortsError("인터넷 이미지가 25 MiB 제한을 초과합니다.")
    if not data:
        raise News2ShortsError("인터넷 이미지 응답이 비어 있습니다.")
    return data, final_url, content_type


def cmd_collect_internet_visual(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"프로젝트 디렉터리를 찾을 수 없습니다: {project_dir}")
    validate_public_https_url(args.source_page, "source page")
    project = load_json(project_dir / "project.json")
    storyboard = load_json(project_dir / "storyboard.json")
    manifest = load_json(project_dir / "rights-manifest.json")
    if not all(isinstance(value, dict) for value in (project, storyboard, manifest)):
        fail("인터넷 이미지 등록에 필요한 프로젝트 JSON 객체를 확인하세요.")
    visual_sourcing = project.get("visual_sourcing")
    if not isinstance(visual_sourcing, dict):
        fail("project.json의 visual_sourcing을 확인하세요.")
    korean_visuals_required = visual_sourcing.get("korean_visuals_required") is True
    international_visuals = visual_sourcing.get("international_source_visuals")
    international_visuals_enabled = (
        isinstance(international_visuals, dict)
        and international_visuals.get("enabled") is True
    )
    if korean_visuals_required:
        if args.visual_locale != DEFAULT_VISUAL_LOCALE:
            fail("한국 이미지 전용 프로젝트에는 --visual-locale ko-KR이 필요합니다.")
        if not args.confirm_korean_context:
            fail("실제 이미지를 확인한 뒤 --confirm-korean-context가 필요합니다.")
        if len(args.korean_context_note.strip()) < 12:
            fail(
                "--korean-context-note에는 한국어 표지판·국내 도로·건축·차량 환경 등 "
                "한국 배경 근거를 구체적으로 작성하세요."
            )
    elif international_visuals_enabled:
        assert isinstance(international_visuals, dict)
        source_locale = str(international_visuals.get("source_locale") or "").strip()
        source_country = str(international_visuals.get("source_country") or "").strip().upper()
        if args.visual_locale == DEFAULT_VISUAL_LOCALE:
            if not args.confirm_korean_context or len(args.korean_context_note.strip()) < 12:
                fail("한국 대응 이미지는 한국 배경 확인과 구체적인 근거가 필요합니다.")
        else:
            if args.visual_locale not in {source_locale, "neutral"}:
                fail(f"국제 실제사건 이미지는 --visual-locale {source_locale} 또는 neutral이 필요합니다.")
            if str(args.source_country or "").strip().upper() != source_country:
                fail(f"국제 실제사건 이미지는 --source-country {source_country}가 필요합니다.")
            if not args.confirm_source_event_context:
                fail("실제 사건 이미지를 확인한 뒤 --confirm-source-event-context가 필요합니다.")
            if len(args.source_event_context_note.strip()) < 12:
                fail("--source-event-context-note에 실제 사건·장소·시점 근거를 작성하세요.")
    scenes = storyboard.get("scenes")
    assets = manifest.get("assets")
    searches = manifest.get("searches")
    if not isinstance(scenes, list) or not isinstance(assets, list) or not isinstance(searches, list):
        fail("storyboard 또는 rights-manifest 배열을 확인하세요.")
    scene = next(
        (
            item
            for item in scenes
            if isinstance(item, dict) and str(item.get("id") or "").strip() == args.scene_id
        ),
        None,
    )
    if scene is None:
        fail(f"storyboard 장면을 찾지 못했습니다: {args.scene_id}")
    existing_visual = str(scene.get("video") or scene.get("image") or "").strip()
    if existing_visual and not args.overwrite:
        fail(f"장면에 기존 시각 자산이 있습니다: {args.scene_id}: {existing_visual}")
    if not args.confirm_news_relevance:
        fail("실제 이미지를 확인한 뒤 --confirm-news-relevance가 필요합니다.")
    if len(args.relevance_note.strip()) < 12:
        fail("--relevance-note에는 장면의 인물·대상·행동·결과 연결을 구체적으로 작성하세요.")
    permission_status = args.permission_status
    approved = permission_status in {"owned", "licensed", "permission_confirmed"}
    if approved and not args.permission_reference.strip():
        fail("확인된 권리 상태에는 --permission-reference가 필요합니다.")
    data, final_url, content_type = download_public_image(args.image_url)
    try:
        from PIL import Image, ImageOps

        with Image.open(io.BytesIO(data)) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > MAX_INTERNET_IMAGE_PIXELS:
                raise News2ShortsError("인터넷 이미지의 픽셀 크기가 허용 범위를 벗어납니다.")
            image.thumbnail((2160, 3840), Image.Resampling.LANCZOS)
            output_value = args.output or f"assets/collected/internet-{slugify(args.scene_id)}.png"
            output = resolve_project_file(project_dir, output_value, must_exist=False)
            if output.exists() and not args.overwrite:
                fail(f"인터넷 이미지 출력이 이미 있습니다: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            image.save(output, format="PNG", optimize=True)
    except News2ShortsError:
        raise
    except Exception as exc:
        raise News2ShortsError(f"인터넷 이미지 파일을 확인할 수 없습니다: {exc}") from exc
    relative = output.relative_to(project_dir).as_posix()
    kind = "licensed" if permission_status == "licensed" else "owned" if permission_status == "owned" else "official" if permission_status == "permission_confirmed" else "unreviewed"
    record = {
        "id": f"internet-{slugify(args.scene_id)}",
        "path": relative,
        "kind": kind,
        "media_type": "photo",
        "source_method": "web_search",
        "source_url": args.source_page,
        "download_url": final_url,
        "content_type": content_type,
        "creator": args.creator.strip(),
        "publisher": args.publisher.strip(),
        "license": args.permission_reference.strip() or "rights pending user review",
        "permission_status": permission_status,
        "attribution": args.attribution.strip() or args.publisher.strip() or args.creator.strip(),
        "retrieved_at": iso_now(),
        "sha256": file_sha256(output),
        "synthetic": False,
        "approved": approved,
        "local_review_only": not approved,
        "news_relevance_reviewed": True,
        "whiteboard_text_free_reviewed": bool(args.confirm_whiteboard_text_free),
        "relevance_level": args.relevance_level,
        "relevance_note": args.relevance_note.strip(),
        "visual_locale": args.visual_locale or "",
        "korean_context_reviewed": bool(args.confirm_korean_context),
        "korean_context_note": args.korean_context_note.strip(),
        "source_country": str(args.source_country or "").strip().upper(),
        "source_event_context_reviewed": bool(args.confirm_source_event_context),
        "source_event_context_note": args.source_event_context_note.strip(),
        "actual_event_media": bool(args.confirm_source_event_context),
        "user_will_confirm_rights_before_publish": True,
        "watermark_removed": False,
    }
    assets[:] = [
        item
        for item in assets
        if not (isinstance(item, dict) and str(item.get("path") or "") == relative)
    ]
    assets.append(record)
    searches.append(
        {
            "query": args.query.strip() or args.relevance_note.strip(),
            "scene_ids": [args.scene_id],
            "searched_at": iso_now(),
            "outcome": "collected",
            "selected_asset_path": relative,
            "note": "공개 HTTPS 이미지를 로컬 검토용으로 수집했으며 게시 전 사용 권리 확인이 필요합니다.",
        }
    )
    scene["image"] = relative
    scene["video"] = ""
    scene["image_fit"] = "auto"
    scene["synthetic"] = False
    scene["credit"] = record["attribution"]
    project["updated_at"] = iso_now()
    write_json(project_dir / "project.json", project)
    write_json(project_dir / "storyboard.json", storyboard)
    write_json(project_dir / "rights-manifest.json", manifest)
    print(
        json.dumps(
            {
                "project_dir": str(project_dir),
                "scene_id": args.scene_id,
                "asset": relative,
                "source_page": args.source_page,
                "permission_status": permission_status,
                "local_review_only": not approved,
                "visible_review_badge": False,
                "publish_blocked_until_rights_review": not approved,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def whiteboard_cli_path() -> Path:
    candidates = [PLUGIN_ROOT.parent / "whiteboard-shorts" / "scripts" / "whiteboard_shorts.py"]
    current = Path.cwd().resolve()
    candidates.extend(
        base / "plugins" / "whiteboard-shorts" / "scripts" / "whiteboard_shorts.py"
        for base in (current, *current.parents)
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise News2ShortsError(
            "whiteboard-shorts 실행기를 찾지 못했습니다. 같은 marketplace의 설치·소스 상태를 확인하세요."
        )
    return path


def srt_time(milliseconds: int) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def write_whiteboard_srt(path: Path, scenes: list[dict]) -> float:
    cursor = 0
    blocks: list[str] = []
    for index, scene in enumerate(scenes, start=1):
        duration_ms = max(1000, round(float(scene.get("duration") or 0.0) * 1000))
        end = cursor + duration_ms
        narration = str(scene.get("narration") or scene.get("caption") or "").strip()
        if not narration:
            raise News2ShortsError(f"whiteboard 장면 {index}의 narration이 비어 있습니다.")
        blocks.append(
            f"{index}\n{srt_time(cursor)} --> {srt_time(end)}\n{narration}"
        )
        cursor = end
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return cursor / 1000


def whiteboard_permission_status(record: dict) -> str:
    explicit = str(record.get("permission_status") or "").strip()
    if explicit in {
        "owned",
        "licensed",
        "permission_confirmed",
        "review_required",
        "unknown",
        "not_permitted",
    }:
        return explicit
    kind = str(record.get("kind") or "").strip()
    if record.get("approved") is True:
        if kind in {"owned", "generated"}:
            return "owned"
        if kind == "licensed":
            return "licensed"
        if kind == "official":
            return "permission_confirmed"
    return "unknown" if kind == "unreviewed" else "review_required"


def render_whiteboard_source_frame(scene: dict, project_dir: Path, destination: Path) -> None:
    image_value = str(scene.get("image") or "").strip()
    video_value = str(scene.get("video") or "").strip()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if image_value:
        render_retention_visual(scene, project_dir, destination)
        return
    if video_value:
        video_path = resolve_project_file(project_dir, video_value)
        start = max(0.0, float(scene.get("video_start") or 0.0))
        run_command(
            [
                shutil.which("ffmpeg") or "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{start:.3f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#F5EBD7",
                "-y",
                str(destination),
            ]
        )
        return
    raise News2ShortsError("whiteboard 변환에는 각 장면의 image 또는 video가 필요합니다.")


def render_whiteboard_ink(source: Path, destination: Path) -> None:
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    except ImportError as exc:
        raise News2ShortsError("whiteboard 이미지 변환에는 Pillow가 필요합니다.") from exc
    with Image.open(source) as opened:
        original = ImageOps.exif_transpose(opened).convert("RGB")
        original = ImageOps.fit(original, (1080, 1920), method=Image.Resampling.LANCZOS)
    paper = Image.new("RGB", original.size, "#F5EBD7")
    muted = ImageEnhance.Color(original).enhance(0.12)
    muted = ImageOps.posterize(muted, 4)
    base = Image.blend(paper, muted, 0.16)
    gray = ImageOps.grayscale(original).filter(ImageFilter.FIND_EDGES)
    edge_mask = ImageOps.autocontrast(gray).point(lambda value: 0 if value < 34 else min(225, value * 2))
    ink = Image.new("RGB", original.size, "#35383B")
    base.paste(ink, mask=edge_mask)
    destination.parent.mkdir(parents=True, exist_ok=True)
    base.save(destination, format="PNG", optimize=True)


def whiteboard_caption_beat(index: int, count: int) -> str:
    if index == 0:
        return "hook"
    if index == count - 1:
        return "payoff"
    if index == max(1, count // 2):
        return "rehook"
    return "setup" if index < count // 2 else "escalation"


def cmd_prepare_whiteboard(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"프로젝트 디렉터리를 찾을 수 없습니다: {project_dir}")
    errors, warnings = validate_project(project_dir, final=False)
    if errors:
        fail("whiteboard 준비 전 검증 실패:\n- " + "\n- ".join(errors))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    project = load_json(project_dir / "project.json")
    storyboard = load_json(project_dir / "storyboard.json")
    manifest = load_json(project_dir / "rights-manifest.json")
    if not all(isinstance(value, dict) for value in (project, storyboard, manifest)):
        fail("whiteboard 준비에 필요한 프로젝트 JSON 객체를 확인하세요.")
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        fail("whiteboard로 변환할 뉴스 장면이 없습니다.")
    target_value = args.output_dir or "whiteboard-project"
    whiteboard_dir = resolve_project_file(project_dir, target_value, must_exist=False)
    if whiteboard_dir == project_dir:
        fail("whiteboard 출력은 원 뉴스 프로젝트와 다른 하위 폴더여야 합니다.")
    if whiteboard_dir.exists():
        if not args.overwrite:
            fail(f"whiteboard 프로젝트가 이미 있습니다: {whiteboard_dir}")
        shutil.rmtree(whiteboard_dir)
    source_srt = project_dir / "assets" / "whiteboard" / "news-story.srt"
    if source_srt.exists() and not args.overwrite:
        fail(f"whiteboard SRT가 이미 있습니다: {source_srt}")
    total_seconds = write_whiteboard_srt(source_srt, scenes)
    run_command(
        [
            sys.executable,
            str(whiteboard_cli_path()),
            "init",
            "--project-dir",
            str(whiteboard_dir),
            "--srt",
            str(source_srt),
            "--title",
            str(project.get("title") or project_dir.name),
            "--rights-status",
            "owned",
            "--rights-reference",
            "news2shorts original Korean narration",
            "--target-sec",
            "0.1",
            "--min-sec",
            "0.1",
            "--max-sec",
            "90",
        ]
    )
    whiteboard_project = load_json(whiteboard_dir / "project.json")
    scene_plan = load_json(whiteboard_dir / "scene-plan.json")
    rights = load_json(whiteboard_dir / "rights-manifest.json")
    postproduction = load_json(whiteboard_dir / "post-production.json")
    if not all(isinstance(value, dict) for value in (whiteboard_project, scene_plan, rights, postproduction)):
        fail("whiteboard 프로젝트 초기화 결과가 올바르지 않습니다.")
    scene_files = scene_plan.get("scene_files")
    if not isinstance(scene_files, list) or len(scene_files) != len(scenes):
        fail("뉴스 장면과 whiteboard 장면 수가 일치하지 않습니다.")

    asset_records: list[dict] = []
    caption_items: list[dict] = []
    music_segments: list[dict] = []
    motion_items: list[dict] = []
    permission_statuses: list[str] = []
    source_frames = whiteboard_dir / "input" / "news-source-frames"
    source_frames.mkdir(parents=True, exist_ok=True)
    for index, (scene, scene_file) in enumerate(zip(scenes, scene_files), start=1):
        if not isinstance(scene, dict):
            fail(f"뉴스 장면 {index} 형식이 올바르지 않습니다.")
        visual = str(scene.get("video") or scene.get("image") or "").strip()
        if not visual:
            fail(f"whiteboard 장면 {index}에 실제 뉴스 image 또는 video가 필요합니다.")
        record = rights_record_for(manifest, visual)
        if not isinstance(record, dict):
            fail(f"whiteboard 장면의 권리·출처 기록이 없습니다: {visual}")
        permission_status = whiteboard_permission_status(record)
        if permission_status == "not_permitted":
            fail(f"not_permitted 자산은 whiteboard 검토본에도 사용할 수 없습니다: {visual}")
        if record.get("news_relevance_reviewed") is not True:
            fail(f"기사 연관성 육안 검토가 필요합니다: {visual}")
        if record.get("whiteboard_text_free_reviewed") is not True:
            fail(f"whiteboard 변환 전 원본 이미지의 문자·로고 영역 검토가 필요합니다: {visual}")
        permission_statuses.append(permission_status)
        scene_id = f"scene-{index:02d}"
        source_frame = source_frames / f"{scene_id}.png"
        scene_image = whiteboard_dir / "scenes" / f"{scene_id}.png"
        render_whiteboard_source_frame(scene, project_dir, source_frame)
        render_whiteboard_ink(source_frame, scene_image)
        whiteboard_scene_path = whiteboard_dir / str(scene_file)
        whiteboard_scene = load_json(whiteboard_scene_path)
        if not isinstance(whiteboard_scene, dict):
            fail(f"whiteboard 장면 파일이 올바르지 않습니다: {scene_file}")
        narration = str(scene.get("narration") or scene.get("caption") or "").strip()
        basis = str(record.get("relevance_note") or narration).strip()
        whiteboard_scene["visual_description"] = basis
        whiteboard_scene["news_source"] = {
            "project": str(project_dir),
            "scene_id": str(scene.get("id") or scene_id),
            "asset_path": visual,
            "source_ids": scene.get("source_ids") or [],
            "claim_ids": scene.get("claim_ids") or [],
        }
        write_json(whiteboard_scene_path, whiteboard_scene)
        duration_ms = int(whiteboard_scene.get("scene_duration_ms") or 0)
        reveal_duration = max(200, duration_ms - 600)
        annotation = {
            "sceneId": scene_id,
            "canvas": {"width": 1080, "height": 1920},
            "storyBasis": basis,
            "sceneDurationMs": duration_ms,
            "elements": [
                {
                    "id": "news-evidence",
                    "label": "뉴스 근거 이미지",
                    "sequence": 1,
                    "narrativeRole": str(scene.get("beat") or "evidence"),
                    "subtitle": narration,
                    "type": "evidence",
                    "region": {"x": 40, "y": 80, "width": 1000, "height": 1760},
                    "reveal": {
                        "direction": "top_to_bottom",
                        "startMs": 100,
                        "durationMs": reveal_duration,
                        "maskPaddingPx": 16,
                        "protectedRegions": [],
                    },
                    "handPath": {
                        "start": [540, 100],
                        "end": [540, 1800],
                        "easing": "easeInOut",
                    },
                }
            ],
        }
        write_json(whiteboard_dir / "scenes" / f"{scene_id}.annotation.json", annotation)
        asset_records.append(
            {
                "id": f"{scene_id}-image",
                "kind": "scene_image",
                "path": f"scenes/{scene_id}.png",
                "sha256": file_sha256(scene_image),
                "creator": str(record.get("creator") or record.get("publisher") or "unknown"),
                "original_url": str(record.get("source_url") or ""),
                "permission_status": permission_status,
                "permission_reference": str(record.get("license") or ""),
                "synthetic": True,
                "transform": "news2shorts-edge-derived-whiteboard",
                "source_asset_path": visual,
                "usage_scope": "local_whiteboard_review",
            }
        )
        caption = str(scene.get("caption") or scene.get("headline") or narration).strip()[:36]
        beat = whiteboard_caption_beat(index - 1, len(scenes))
        caption_items.append(
            {
                "scene_id": scene_id,
                "text": caption,
                "position": "top" if index % 2 else "bottom",
                "beat": beat,
            }
        )
        music_segments.append(
            {
                "scene_id": scene_id,
                "profile_id": "tension" if beat in {"rehook", "escalation"} else "gentle",
                "impact": beat in {"rehook", "payoff"},
            }
        )
        if beat in {"hook", "rehook", "payoff"}:
            motion_items.append(
                {
                    "scene_id": scene_id,
                    "type": "punch-in" if beat in {"rehook", "payoff"} else "zoom-in",
                    "start_scale": 1.0,
                    "end_scale": 1.1 if beat in {"rehook", "payoff"} else 1.05,
                    "focus_x": 0.5,
                    "focus_y": 0.48,
                }
            )

    rights["assets"] = asset_records + [
        {
            "id": "background-music",
            "kind": "background_music",
            "path": "assets/audio/background-music.wav",
            "creator": "Whiteboard Shorts synthetic tone generator",
            "permission_status": "owned",
            "permission_reference": "project-generated",
            "synthetic": True,
            "vocals": False,
            "usage_scope": "local_whiteboard_review",
        }
    ]
    rights["news2shorts_source"] = {
        "project": str(project_dir),
        "rights_inherited": True,
        "permission_statuses": permission_statuses,
        "publication_ready": False,
    }
    postproduction["captions"] = {
        "enabled": True,
        "style": "viral-punch",
        "items": caption_items,
    }
    postproduction["music"] = {
        "enabled": True,
        "mode": "synthetic_ambient",
        "vocals": False,
        "volume": 0.24,
        "fade_in_seconds": 0.25,
        "fade_out_seconds": 0.45,
        "asset_path": "assets/audio/background-music.wav",
        "segments": music_segments,
        "rights": {
            "permission_status": "owned",
            "note": "Whiteboard renderer project-generated no-vocal music",
        },
    }
    postproduction["motion"] = {"enabled": True, "items": motion_items}
    whiteboard_project["status"] = "annotated"
    whiteboard_project["updated_at"] = iso_now()
    whiteboard_project["render_profile"]["audio"] = "background_music"
    whiteboard_project["render_profile"]["audio_codec"] = "aac"
    whiteboard_project["news2shorts_source"] = {
        "project": str(project_dir),
        "visual_mode": "whiteboard",
        "prepared_at": iso_now(),
        "publish_blocked": True,
        "visible_review_badge": False,
        "rights_review_owner": "user_before_publish",
        "local_review_only": any(
            status not in {"owned", "licensed", "permission_confirmed"}
            for status in permission_statuses
        ),
    }
    write_json(whiteboard_dir / "project.json", whiteboard_project)
    write_json(whiteboard_dir / "rights-manifest.json", rights)
    write_json(whiteboard_dir / "post-production.json", postproduction)
    visual_sourcing = project.get("visual_sourcing")
    visual_style = project.get("visual_style")
    assert isinstance(visual_sourcing, dict) and isinstance(visual_style, dict)
    visual_sourcing["mode"] = "whiteboard"
    whiteboard_config = visual_sourcing.get("whiteboard")
    if not isinstance(whiteboard_config, dict):
        whiteboard_config = {}
        visual_sourcing["whiteboard"] = whiteboard_config
    whiteboard_config.update(
        {
            "enabled": True,
            "renderer": "whiteboard-shorts",
            "project_dir": str(whiteboard_dir.relative_to(project_dir)),
            "source_rights_inherited": True,
            "prepared_at": iso_now(),
        }
    )
    visual_style["render_mode"] = "whiteboard"
    project["updated_at"] = iso_now()
    write_json(project_dir / "project.json", project)
    print(
        json.dumps(
            {
                "project_dir": str(project_dir),
                "whiteboard_project": str(whiteboard_dir),
                "scene_count": len(scenes),
                "source_duration_seconds": total_seconds,
                "rendered": False,
                "review_required": True,
                "publication_ready": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_render_whiteboard(args: argparse.Namespace, project: dict) -> int:
    if not args.draft:
        fail("news2shorts whiteboard 옵션은 권리·장면 검토 전 clean final을 만들지 않습니다. --draft를 사용하세요.")
    if not args.confirm_whiteboard_review:
        fail("whiteboard 장면 이미지와 annotation을 확인한 뒤 --confirm-whiteboard-review가 필요합니다.")
    project_dir = Path(args.project_dir).expanduser().resolve()
    visual_sourcing = project.get("visual_sourcing")
    if not isinstance(visual_sourcing, dict):
        fail("project.json의 visual_sourcing을 확인하세요.")
    whiteboard_config = visual_sourcing.get("whiteboard")
    if not isinstance(whiteboard_config, dict) or whiteboard_config.get("enabled") is not True:
        fail("먼저 prepare-whiteboard를 실행하세요.")
    whiteboard_relative = args.whiteboard_project or str(
        whiteboard_config.get("project_dir") or "whiteboard-project"
    )
    whiteboard_dir = resolve_project_file(project_dir, whiteboard_relative)
    whiteboard_project = load_json(whiteboard_dir / "project.json")
    if not isinstance(whiteboard_project, dict):
        fail("whiteboard project.json을 확인하세요.")
    approvals = whiteboard_project.get("approvals")
    if not isinstance(approvals, dict):
        fail("whiteboard 승인 구조가 없습니다.")
    approvals["scene_plan_reviewed"] = True
    approvals["images_reviewed"] = True
    approvals["annotations_reviewed"] = True
    whiteboard_project["updated_at"] = iso_now()
    write_json(whiteboard_dir / "project.json", whiteboard_project)
    validate_result = run_command(
        [
            sys.executable,
            str(whiteboard_cli_path()),
            "validate",
            "--project-dir",
            str(whiteboard_dir),
            "--render-ready",
        ]
    )
    render_command = [
        sys.executable,
        str(whiteboard_cli_path()),
        "render",
        "--project-dir",
        str(whiteboard_dir),
        "--all",
        "--draft",
        "--hide-review-label",
    ]
    if args.overwrite:
        render_command.append("--overwrite")
    render_result = run_command(render_command)
    print(
        json.dumps(
            {
                "visual_mode": "whiteboard",
                "news_project": str(project_dir),
                "whiteboard_project": str(whiteboard_dir),
                "video": str(whiteboard_dir / "outputs" / "preview.mp4"),
                "validate": json.loads(validate_result.stdout),
                "renderer_output": render_result.stdout.strip(),
                "draft": True,
                "publication_ready": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"프로젝트 디렉터리를 찾을 수 없습니다: {project_dir}")
    project_preview = load_json(project_dir / "project.json")
    if not isinstance(project_preview, dict):
        fail("project.json의 최상위 값은 객체여야 합니다.")
    configured_mode = str(
        (project_preview.get("visual_sourcing") or {}).get("mode") or "standard"
    ).strip()
    requested_mode = args.visual_mode or configured_mode
    if requested_mode not in VISUAL_MODES:
        fail(f"지원하지 않는 visual mode입니다: {requested_mode}")
    if args.visual_mode and requested_mode != configured_mode:
        fail(
            "렌더 visual mode는 project.json과 일치해야 합니다. "
            "whiteboard는 prepare-whiteboard로 준비하세요."
        )
    if requested_mode == "whiteboard":
        return cmd_render_whiteboard(args, project_preview)
    errors, warnings = validate_project(project_dir, final=not args.draft)
    if errors:
        fail("렌더 전 검증 실패:\n- " + "\n- ".join(errors))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    project = load_json(project_dir / "project.json")
    storyboard = load_json(project_dir / "storyboard.json")
    manifest = load_json(project_dir / "rights-manifest.json")
    publish = load_json(project_dir / "publish.json")
    assert all(isinstance(value, dict) for value in (project, storyboard, manifest, publish))
    if args.style:
        style = visual_style_config(project).copy()
        current_template = str(style.get("template") or "classic-card")
        try:
            project_version = int(project.get("version") or 1)
        except (TypeError, ValueError):
            project_version = 1
        if project_version >= 4 and args.style != current_template:
            fail(
                "version 4+ 프로젝트의 렌더 포맷은 format_selection 기록과 일치해야 합니다. "
                "project.json의 선택 기록과 visual_style을 함께 수정하세요."
            )
        if current_template in RETENTION_TEMPLATES and args.style not in RETENTION_TEMPLATES:
            fail("새 집중 유지형 프로젝트는 고정 헤드라인 템플릿으로만 렌더할 수 있습니다.")
        style["template"] = args.style
        project["visual_style"] = style
    scenes = storyboard["scenes"]
    delivery_mode = str(project.get("delivery_mode") or "scene-based").strip()
    continuous_flow = delivery_mode == CONTINUOUS_FLOW_MODE
    visual_first = delivery_mode == VISUAL_FIRST_MODE
    hybrid_source_audio = continuous_flow and any(
        isinstance(scene, dict) and scene_uses_source_video_audio(scene)
        for scene in scenes
    )
    effective_no_tts = args.no_tts or visual_first
    voice_selection: dict | None = None
    if not effective_no_tts and args.tts_provider == "typecast":
        try:
            voice_selection = select_typecast_voice(project, storyboard, args.typecast_voice)
        except News2ShortsError as exc:
            fail(str(exc))
        print(
            f"typecast_voice: {voice_selection['voice_name']} "
            f"({voice_selection['voice_id']}, {voice_selection['mode']}) - {voice_selection['reason']}",
            file=sys.stderr,
        )
    default_name = "preview.mp4" if args.draft else "short.mp4"
    output_name = args.output or default_name
    if args.tts_provider == "local" and not 80 <= args.rate <= 500:
        fail("--rate는 80에서 500 사이여야 합니다.")
    if args.tts_provider == "typecast" and not 0.5 <= args.typecast_tempo <= 2.0:
        fail("--typecast-tempo는 0.5에서 2.0 사이여야 합니다.")
    needs_generated_tts = any(
        str(scene.get("narration") or "").strip()
        and not str(scene.get("audio") or "").strip()
        and not scene_uses_source_video_audio(scene)
        for scene in scenes
    )
    cta_config = project.get("cta_tail")
    cta_selection = select_cta_tail_variant(project, storyboard)
    configured_mid_cta = mid_cta_config(project)
    try:
        project_version_for_mid_cta = int(project.get("version") or 1)
        project_target_duration = float(project.get("target_duration_seconds") or 0.0)
    except (TypeError, ValueError):
        project_version_for_mid_cta = 1
        project_target_duration = 0.0
    mid_cta_may_need_generated_tts = (
        project_version_for_mid_cta >= 17
        and str(configured_mid_cta.get("mode") or "disabled") != "disabled"
        and delivery_mode == CONTINUOUS_FLOW_MODE
        and project_target_duration >= MID_CTA_MIN_BODY_SECONDS
        and configured_mid_cta.get("voice_enabled") is True
    )
    cta_needs_generated_tts = (
        isinstance(cta_config, dict)
        and cta_config.get("enabled") is True
        and cta_config.get("voice_enabled") is not False
        and bool(str(cta_selection.get("narration") or "").strip())
    )
    if (
        not effective_no_tts
        and (needs_generated_tts or cta_needs_generated_tts or mid_cta_may_need_generated_tts)
        and args.tts_provider == "typecast"
    ):
        typecast_api_key()
    if Path(output_name).suffix.lower() != ".mp4":
        fail("렌더 출력은 .mp4 파일이어야 합니다.")
    output = resolve_project_file(project_dir, output_name, must_exist=False)
    if output.exists() and not args.overwrite:
        fail(f"출력 파일이 이미 있습니다: {output}. 덮어쓰려면 --overwrite를 사용하세요.")
    editor_target = editor_package_target(project_dir, output_name)
    if editor_target.exists() and not args.overwrite:
        fail(
            f"편집 호환 패키지가 이미 있습니다: {editor_target}. "
            "덮어쓰려면 --overwrite를 사용하세요."
        )
    output.parent.mkdir(parents=True, exist_ok=True)

    suppressed_identifier_fields = suppress_public_identifiers(project_dir, project, storyboard)
    if suppressed_identifier_fields:
        print(
            f"suppressed_editorial_identifiers: {len(suppressed_identifier_fields)} field(s)",
            file=sys.stderr,
        )

    scene_reports: list[dict] = []
    mid_cta_report: dict = {"enabled": False}
    planned_mid_cta_selection: dict = {"enabled": False}
    if continuous_flow and not hybrid_source_audio:
        planned_mid_cta_selection = select_mid_cta(
            project,
            scenes,
            estimated_continuous_flow_scene_reports(project, scenes),
        )
    cta_report: dict = {"enabled": False}
    brand_intro_report: dict = {"enabled": False}
    editor_package_report: dict = {"enabled": False}
    background_music_report: dict = {"enabled": False}
    background_music_path: Path | None = None
    with tempfile.TemporaryDirectory(prefix=".news2shorts-", dir=project_dir) as temp_name:
        work_dir = Path(temp_name)
        scene_paths: list[Path] = []
        editor_scenes: list[dict] = []
        editor_scenes_dir = work_dir / "editor-scenes"
        editor_scenes_dir.mkdir(parents=True, exist_ok=True)
        template = str(visual_style_config(project).get("template") or "classic-card")
        try:
            timed_motion = int(project.get("version") or 1) >= 4
        except (TypeError, ValueError):
            timed_motion = False
        continuous_audio_segments: list[dict] = []
        continuous_group_audio_paths: list[Path] = []
        continuous_audio_duration = 0.0
        continuous_audio_source = ""
        if continuous_flow and not hybrid_source_audio:
            group_ranges = continuous_flow_audio_group_ranges(
                len(scenes),
                planned_mid_cta_selection,
            )
            for group_number, (group_start, group_end) in enumerate(group_ranges, start=1):
                group_scenes = scenes[group_start:group_end]
                output_stem = (
                    "continuous-flow"
                    if len(group_ranges) == 1
                    else f"continuous-flow-mid-cta-part-{group_number}"
                )
                group_audio_path, group_audio_duration, group_audio_source = continuous_flow_audio(
                    group_scenes,
                    work_dir,
                    no_tts=effective_no_tts,
                    tts_provider=args.tts_provider,
                    voice=args.voice,
                    rate=args.rate,
                    typecast_voice_id=(
                        str(voice_selection["voice_id"])
                        if voice_selection
                        else TYPECAST_VOICE_ID
                    ),
                    typecast_tempo=args.typecast_tempo,
                    output_stem=output_stem,
                )
                continuous_group_audio_paths.append(group_audio_path)
                continuous_audio_duration += group_audio_duration
                if not continuous_audio_source:
                    continuous_audio_source = group_audio_source
                if effective_no_tts:
                    group_durations = [
                        max(
                            CONTINUOUS_FLOW_PAYOFF_MIN_SECONDS
                            if str(scene.get("beat") or "").strip() == "payoff"
                            else CONTINUOUS_FLOW_MIN_SCENE_SECONDS,
                            float(scene.get("duration") or 0.0),
                        )
                        for scene in group_scenes
                    ]
                else:
                    group_durations = continuous_flow_scene_durations(
                        group_scenes,
                        group_audio_duration,
                    )
                group_cursor = 0.0
                for duration in group_durations:
                    continuous_audio_segments.append(
                        {
                            "path": group_audio_path,
                            "start": group_cursor,
                            "duration": duration,
                            "source": group_audio_source,
                        }
                    )
                    group_cursor += duration
        continuous_cursor = 0.0
        scene_cursor = 0.0
        for index, scene in enumerate(scenes, start=1):
            frame = work_dir / f"scene-{index:02d}.png"
            video_value = str(scene.get("video") or "").strip()
            static_overlay: Path | None = None
            if video_value:
                if scene_text_overlay_enabled(scene):
                    render_retention_overlay(scene, project, frame, draft=args.draft)
                else:
                    render_source_video_overlay(scene, frame)
            elif template in RETENTION_TEMPLATES:
                render_retention_visual(scene, project_dir, frame)
                static_overlay = work_dir / f"scene-{index:02d}-overlay.png"
                render_retention_overlay(scene, project, static_overlay, draft=args.draft)
            else:
                render_frame(scene, project, project_dir, frame, draft=args.draft)
            previous_text = str(scenes[index - 2].get("narration") or "").strip() if index > 1 else ""
            next_text = str(scenes[index].get("narration") or "").strip() if index < len(scenes) else ""
            requested = max(1.0, float(scene.get("duration") or 0.0))
            if continuous_flow and not hybrid_source_audio:
                segment = continuous_audio_segments[index - 1]
                duration = float(segment["duration"])
                audio = work_dir / f"scene-{index:02d}-continuous.wav"
                extract_audio_segment(
                    Path(segment["path"]),
                    audio,
                    start=float(segment["start"]),
                    duration=duration,
                )
                measured_audio = duration
                audio_source = f"{segment['source']}-segment"
            elif scene_uses_source_video_audio(scene):
                if not video_value:
                    raise News2ShortsError(
                        f"source-video audio_mode에는 video 자산이 필요합니다: {scene.get('id', index)}"
                    )
                video_path = resolve_project_file(project_dir, video_value)
                start = max(0.0, float(scene.get("video_start") or 0.0))
                audio = work_dir / f"scene-{index:02d}-source-video.wav"
                extract_audio_segment(
                    video_path,
                    audio,
                    start=start,
                    duration=requested,
                )
                measured_audio = audio_duration(audio)
                duration = requested
                audio_source = SOURCE_VIDEO_AUDIO_MODE
            else:
                audio, measured_audio, audio_source = scene_audio(
                    scene,
                    project_dir,
                    work_dir,
                    index,
                    no_tts=effective_no_tts,
                    tts_provider=args.tts_provider,
                    voice=args.voice,
                    rate=args.rate,
                    typecast_voice_id=(
                        str(voice_selection["voice_id"])
                        if voice_selection
                        else TYPECAST_VOICE_ID
                    ),
                    typecast_tempo=args.typecast_tempo,
                    previous_text=previous_text,
                    next_text=next_text,
                )
                duration = (
                    requested
                    if visual_first
                    else max(requested, measured_audio + TYPECAST_SCENE_TAIL_SECONDS)
                )
            if duration > 90:
                raise News2ShortsError(f"장면이 너무 깁니다: {scene.get('id', index)}: {duration:.1f}초")
            scene_path = work_dir / f"scene-{index:02d}.mp4"
            clean_scene_path = editor_scenes_dir / f"scene-{index:02d}.mp4"
            editor_overlay: Path | None = None
            if video_value:
                video_path = resolve_project_file(project_dir, video_value)
                start = max(0.0, float(scene.get("video_start") or 0.0))
                render_video_scene(video_path, frame, audio, scene_path, duration, start=start)
                render_clean_video_scene(
                    video_path,
                    audio,
                    clean_scene_path,
                    duration,
                    start=start,
                )
                editor_overlay = frame
                visual_kind = "video"
                motion = "source-video"
            else:
                motion_default = "none" if timed_motion else "zoom-in"
                motion = str(scene.get("motion") or motion_default) if template in RETENTION_TEMPLATES else "none"
                focus_x = float(scene.get("focus_x", 0.5))
                focus_y = float(scene.get("focus_y", 0.5))
                zoom_scale = float(scene.get("zoom_scale", 1.0 if timed_motion else 1.055))
                motion_start = float(scene.get("motion_start") or 0.0)
                motion_duration = float(scene.get("motion_duration") or 0.0)
                render_static_scene(
                    frame,
                    audio,
                    scene_path,
                    duration,
                    motion=motion,
                    overlay=static_overlay,
                    focus_x=focus_x,
                    focus_y=focus_y,
                    zoom_scale=zoom_scale,
                    motion_start=motion_start,
                    motion_duration=motion_duration,
                )
                render_static_scene(
                    frame,
                    audio,
                    clean_scene_path,
                    duration,
                    motion=motion,
                    focus_x=focus_x,
                    focus_y=focus_y,
                    zoom_scale=zoom_scale,
                    motion_start=motion_start,
                    motion_duration=motion_duration,
                )
                editor_overlay = static_overlay
                visual_kind = "image"
            scene_paths.append(scene_path)
            editor_scenes.append(
                {
                    "scene": scene,
                    "clean_path": clean_scene_path,
                    "overlay_path": editor_overlay,
                    "audio_path": audio,
                    "audio_duration": measured_audio,
                    "duration": duration,
                }
            )
            scene_reports.append(
                {
                    "id": scene.get("id") or f"scene-{index:02d}",
                    "beat": str(scene.get("beat") or ""),
                    "requested_duration": requested,
                    "audio_duration": round(measured_audio, 3),
                    "audio_source": audio_source,
                    "audio_mode": scene_audio_mode(scene),
                    "render_text_overlay": scene_text_overlay_enabled(scene),
                    "external_caption": scene_external_caption_enabled(scene),
                    "rendered_duration": round(duration, 3),
                    "visual_kind": visual_kind,
                    "image_fit": (
                        None
                        if video_value
                        else str(scene.get("image_fit") or "auto")
                    ),
                    "motion": motion,
                    "motion_start": None if video_value else round(float(scene.get("motion_start") or 0.0), 3),
                    "motion_duration": None if video_value else round(float(scene.get("motion_duration") or 0.0), 3),
                    "motion_emphasis": str(scene.get("motion_emphasis") or ""),
                    "visual_role": str(scene.get("visual_role") or "evidence"),
                    "story_link": scene.get("story_link") if isinstance(scene.get("story_link"), dict) else {},
                    "fact_index": str(scene.get("fact_index") or ""),
                    "claim_ids": (
                        scene.get("claim_ids") if isinstance(scene.get("claim_ids"), list) else []
                    ),
                    "evidence_kind": str(scene.get("evidence_kind") or ""),
                    "evidence_label": str(scene.get("evidence_label") or ""),
                    "evidence_value": str(scene.get("evidence_value") or ""),
                    "payoff_callback": str(scene.get("payoff_callback") or ""),
                    "payoff_punch": str(scene.get("payoff_punch") or ""),
                    "voice_delivery": str(scene.get("voice_delivery") or "auto"),
                    "focus_x": None if video_value else round(float(scene.get("focus_x", 0.5)), 3),
                    "focus_y": None if video_value else round(float(scene.get("focus_y", 0.5)), 3),
                    "zoom_scale": None
                    if video_value
                    else round(float(scene.get("zoom_scale", 1.0 if timed_motion else 1.055)), 3),
                    "flow_cue_start": round(continuous_cursor, 3) if continuous_flow else None,
                    "flow_cue_end": (
                        round(continuous_cursor + duration, 3) if continuous_flow else None
                    ),
                    "timeline_start": round(scene_cursor, 3),
                    "timeline_end": round(scene_cursor + duration, 3),
                }
            )
            if continuous_flow:
                continuous_cursor += duration
            scene_cursor += duration

        timing_errors, timing_warnings = render_timing_issues(
            project,
            scene_reports,
            final=not args.draft,
        )
        warnings.extend(message for message in timing_warnings if message not in warnings)
        if timing_errors:
            fail("Typecast 렌더 길이 검증 실패:\n- " + "\n- ".join(timing_errors))

        if continuous_flow and not hybrid_source_audio:
            mid_cta_selection = dict(planned_mid_cta_selection)
            if mid_cta_selection.get("enabled") is True:
                insert_after_index = int(mid_cta_selection["insert_after_scene_index"])
                body_duration = float(scene_reports[-1].get("timeline_end") or 0.0)
                boundary = float(
                    scene_reports[insert_after_index - 1].get("timeline_end") or 0.0
                )
                mid_cta_selection.update(
                    {
                        "body_duration": round(body_duration, 3),
                        "boundary_ratio": round(
                            boundary / body_duration if body_duration else 0.0,
                            4,
                        ),
                        "body_audio_strategy": "two-continuous-requests",
                        "body_audio_group_count": 2,
                        "boundary_preserves_complete_utterances": True,
                    }
                )
        else:
            mid_cta_selection = select_mid_cta(project, scenes, scene_reports)
        mid_cta_path = work_dir / "mid-cta.mp4"
        mid_cta_audio_path: Path | None = None
        if mid_cta_selection.get("enabled") is True:
            insert_after_index = int(mid_cta_selection["insert_after_scene_index"])
            previous_mid_text = str(scenes[insert_after_index - 1].get("narration") or "").strip()
            next_mid_text = (
                str(scenes[insert_after_index].get("narration") or "").strip()
                if insert_after_index < len(scenes)
                else ""
            )
            mid_cta_report, mid_cta_audio_path = render_mid_cta(
                mid_cta_selection,
                work_dir,
                mid_cta_path,
                no_tts=effective_no_tts,
                tts_provider=args.tts_provider,
                voice=args.voice,
                rate=args.rate,
                typecast_voice_id=(
                    str(voice_selection["voice_id"]) if voice_selection else TYPECAST_VOICE_ID
                ),
                typecast_voice_name=(
                    str(voice_selection["voice_name"]) if voice_selection else TYPECAST_VOICE_NAME
                ),
                typecast_tempo=args.typecast_tempo,
                previous_text=previous_mid_text,
                next_text=next_mid_text,
            )
            mid_duration = float(mid_cta_report.get("duration") or 0.0)
            mid_start = float(scene_reports[insert_after_index - 1].get("timeline_end") or 0.0)
            mid_cta_report["timeline_start"] = round(mid_start, 3)
            mid_cta_report["timeline_end"] = round(mid_start + mid_duration, 3)
            scene_paths.insert(insert_after_index, mid_cta_path)
            for report_item in scene_reports[insert_after_index:]:
                report_item["timeline_start"] = round(
                    float(report_item.get("timeline_start") or 0.0) + mid_duration,
                    3,
                )
                report_item["timeline_end"] = round(
                    float(report_item.get("timeline_end") or 0.0) + mid_duration,
                    3,
                )
            cta_selection = select_tail_after_mid_cta(
                project,
                storyboard,
                mid_cta_report,
            )
        else:
            mid_cta_report = mid_cta_selection

        cta_path = work_dir / "cta-tail.mp4"
        cta_report = render_cta_tail(
            project,
            cta_selection,
            work_dir,
            cta_path,
            no_tts=effective_no_tts,
            tts_provider=args.tts_provider,
            voice=args.voice,
            rate=args.rate,
            typecast_voice_id=(
                str(voice_selection["voice_id"]) if voice_selection else TYPECAST_VOICE_ID
            ),
            typecast_voice_name=(
                str(voice_selection["voice_name"]) if voice_selection else TYPECAST_VOICE_NAME
            ),
            typecast_tempo=args.typecast_tempo,
            previous_text=(str(scenes[-1].get("narration") or "").strip() if scenes else ""),
        )
        try:
            project_version = int(project.get("version") or 1)
        except (TypeError, ValueError):
            project_version = 1
        if (
            project_version >= 16
            and cta_report.get("enabled") is True
            and float(cta_report.get("duration") or 0.0) > DEFAULT_CTA_TAIL_DURATION + 0.01
        ):
            message = (
                "version 16 CTA 실제 길이가 2초를 넘습니다: "
                f"{float(cta_report.get('duration') or 0.0):.2f}/{DEFAULT_CTA_TAIL_DURATION:.2f}초"
            )
            if args.draft:
                warnings.append(message)
            else:
                fail(message)
        cta_audio_path = next(
            (
                candidate
                for candidate in (
                    work_dir / "cta-tail-typecast.wav",
                    work_dir / "cta-tail-local.aiff",
                    work_dir / "cta-tail-tone.wav",
                )
                if candidate.is_file()
            ),
            None,
        )
        concat_file = work_dir / "news-scenes-concat.txt"
        concat_file.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in scene_paths),
            encoding="utf-8",
        )
        segmented_news_body = work_dir / "news-scenes-segmented.mp4"
        run_command(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                "-y",
                str(segmented_news_body),
            ]
        )
        news_scenes_body = segmented_news_body
        if continuous_flow and not hybrid_source_audio and not effective_no_tts:
            body_audio_parts = list(continuous_group_audio_paths)
            if mid_cta_report.get("enabled") is True:
                if len(body_audio_parts) != 2 or mid_cta_audio_path is None:
                    raise News2ShortsError(
                        "중간 CTA 렌더에는 앞 본문, CTA, 뒤 본문의 완전한 오디오가 필요합니다."
                    )
                body_audio_parts.insert(1, mid_cta_audio_path)
            continuous_body_audio = work_dir / "continuous-body-with-cta.wav"
            concatenate_audio_files(
                body_audio_parts,
                continuous_body_audio,
                work_dir / "continuous-body-audio-concat.txt",
            )
            news_scenes_body = work_dir / "news-scenes-continuous.mp4"
            mux_continuous_audio(
                segmented_news_body,
                continuous_body_audio,
                news_scenes_body,
            )
        news_body = news_scenes_body
        if cta_report.get("enabled") is True:
            news_body = work_dir / "news-body.mp4"
            concatenate_mp4_files(
                [news_scenes_body, cta_path],
                news_body,
                work_dir / "news-body-concat.txt",
            )
        if visual_first:
            body_info = probe_video(news_body)
            generated_music = work_dir / "background-music.wav"
            create_news_pulse_audio(generated_music, float(body_info["duration"]))
            music_body = work_dir / "news-body-with-music.mp4"
            mux_continuous_audio(news_body, generated_music, music_body)
            news_body = music_body
            background_music_path = resolve_project_file(
                project_dir,
                VISUAL_FIRST_AUDIO_PATH,
                must_exist=False,
            )
            background_music_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(generated_music, background_music_path)
            record_generated_background_music(manifest, float(body_info["duration"]))
            write_json(project_dir / "rights-manifest.json", manifest)
            background_music_report = {
                "enabled": True,
                "mode": "renderer-generated",
                "profile": VISUAL_FIRST_AUDIO_PROFILE,
                "vocals": False,
                "path": VISUAL_FIRST_AUDIO_PATH,
                "duration": round(float(body_info["duration"]), 3),
            }
        brand_intro_report = compose_brand_intro(project, news_body, output)
        editor_package_report = create_editor_package(
            project_dir,
            project,
            storyboard,
            output,
            output_name,
            work_dir,
            editor_scenes,
            mid_cta_path if mid_cta_report.get("enabled") is True else None,
            mid_cta_audio_path,
            mid_cta_report,
            cta_path if cta_report.get("enabled") is True else None,
            cta_audio_path,
            cta_report,
            background_music_path,
            overwrite=args.overwrite,
        )

    video = probe_video(output)
    thumbnail_report = render_composite_thumbnail(
        project_dir,
        project,
        storyboard,
        manifest,
        publish,
        overwrite=args.overwrite,
    )
    report = {
        "version": 5,
        "rendered_at": iso_now(),
        "draft": args.draft,
        "output": output.relative_to(project_dir).as_posix(),
        "voice": None
        if effective_no_tts
        else (
            voice_selection["voice_id"]
            if args.tts_provider == "typecast" and voice_selection
            else args.voice
        ),
        "voice_name": None
        if effective_no_tts
        else (
            voice_selection["voice_name"]
            if args.tts_provider == "typecast" and voice_selection
            else args.voice
        ),
        "voice_selection": None
        if not voice_selection
        else {
            "mode": voice_selection["mode"],
            "profile": voice_selection["profile"],
            "reason": voice_selection["reason"],
            "use_cases": voice_selection["use_cases"],
            "selection_strategy": voice_selection["selection_strategy"],
            "popularity_basis": voice_selection["popularity_basis"],
            "popularity_source": voice_selection["popularity_source"],
            "distribution": voice_selection.get("distribution"),
            "distribution_basis": voice_selection.get("distribution_basis"),
            "distribution_bucket": voice_selection.get("distribution_bucket"),
        },
        "tts_provider": None if effective_no_tts else args.tts_provider,
        "tts_model": TYPECAST_MODEL if not effective_no_tts and args.tts_provider == "typecast" else None,
        "tts_outer_silence_trim": None
        if effective_no_tts or args.tts_provider != "typecast"
        else {
            "enabled": True,
            "leading_keep_seconds": TYPECAST_LEADING_SILENCE_KEEP_SECONDS,
            "trailing_keep_seconds": TYPECAST_TRAILING_SILENCE_KEEP_SECONDS,
            "threshold_db": TYPECAST_SILENCE_THRESHOLD_DB,
            "internal_pauses_preserved": True,
        },
        "delivery_mode": delivery_mode,
        "narration_style": narration_style_config(project),
        "continuous_flow": {
            "enabled": (
                continuous_flow
                and not hybrid_source_audio
                and mid_cta_report.get("enabled") is not True
            ),
            "hybrid_source_audio": hybrid_source_audio,
            "mid_cta_segmented": bool(
                continuous_flow
                and not hybrid_source_audio
                and mid_cta_report.get("enabled") is True
            ),
            "mid_cta_two_part": bool(
                continuous_flow
                and not hybrid_source_audio
                and mid_cta_report.get("enabled") is True
            ),
            "boundary_preserves_complete_utterances": bool(
                mid_cta_report.get("boundary_preserves_complete_utterances") is True
            ),
            "body_tts_requests": (
                sum(
                    1
                    for scene in scenes
                    if isinstance(scene, dict)
                    and not scene_uses_source_video_audio(scene)
                    and str(scene.get("narration") or "").strip()
                    and not str(scene.get("audio") or "").strip()
                )
                if hybrid_source_audio and not effective_no_tts
                else 2
                if continuous_flow
                and mid_cta_report.get("enabled") is True
                and not effective_no_tts
                else 1 if continuous_flow and not effective_no_tts else 0
            ),
            "audio_source": (
                "scene-aligned-hybrid"
                if hybrid_source_audio
                else f"{continuous_audio_source}-two-part-safe-boundary"
                if continuous_flow and mid_cta_report.get("enabled") is True
                else continuous_audio_source if continuous_flow else None
            ),
            "timing_strategy": (
                "scene-aligned"
                if hybrid_source_audio
                else "mid-cta-two-part-continuous"
                if continuous_flow and mid_cta_report.get("enabled") is True
                else
                "storyboard-requested"
                if continuous_flow and effective_no_tts
                else "narration-weighted"
                if continuous_flow
                else None
            ),
            "audio_duration": (
                round(scene_cursor, 3)
                if hybrid_source_audio
                else round(continuous_audio_duration, 3) if continuous_flow else None
            ),
        },
        "visual_style": visual_style_config(project).get("template"),
        "attention_strategy": {
            field: shorts_profile_config(project).get(field)
            for field in (
                "issue_focus",
                "viewer_stake",
                "tension_question",
                "visual_attention_device",
                "visual_attention_scene_id",
                "visual_attention_reason",
            )
        },
        "synthetic_badge": "hidden",
        "suppressed_editorial_identifiers": {
            "count": len(suppressed_identifier_fields),
            "fields": suppressed_identifier_fields,
        },
        "scene_transition": "cut",
        "brand_intro": brand_intro_report,
        "audio_bed": background_music_report,
        "retention_timing": retention_timing_report(project, scene_reports),
        "mid_cta": mid_cta_report,
        "cta_tail": cta_report,
        "editor_package": editor_package_report,
        "scenes": scene_reports,
        "video": video,
        "thumbnail": thumbnail_report,
        "warnings": warnings,
    }
    write_json(project_dir / "render-report.json", report)
    project["updated_at"] = iso_now()
    project["status"] = "rendered_draft" if args.draft else "rendered"
    project["last_render"] = {
        "path": output.relative_to(project_dir).as_posix(),
        "draft": args.draft,
        "rendered_at": report["rendered_at"],
    }
    if voice_selection:
        project["narration_voice"] = {
            "mode": voice_selection["mode"],
            "voice": "" if voice_selection["mode"] == "auto" else voice_selection["key"],
            "selected_voice_id": voice_selection["voice_id"],
            "selected_voice_name": voice_selection["voice_name"],
            "profile": voice_selection["profile"],
            "reason": voice_selection["reason"],
            "selection_strategy": voice_selection["selection_strategy"],
            "popularity_basis": voice_selection["popularity_basis"],
            "popularity_source": voice_selection["popularity_source"],
            "distribution": voice_selection.get("distribution"),
            "distribution_basis": voice_selection.get("distribution_basis"),
            "distribution_bucket": voice_selection.get("distribution_bucket"),
            "selected_at": report["rendered_at"],
        }
    write_json(project_dir / "project.json", project)
    print(output)
    return 0


def validate_editor_package(
    project_dir: Path,
    package_report: dict,
    expected_scene_count: int,
) -> list[str]:
    errors: list[str] = []
    package_value = str(package_report.get("path") or "").strip()
    if not package_value:
        return ["렌더 보고서에 편집 호환 패키지 경로가 없습니다."]
    try:
        package_dir = resolve_project_file(project_dir, package_value, must_exist=False)
    except News2ShortsError as exc:
        return [str(exc)]
    if not package_dir.is_dir():
        return [f"편집 호환 패키지 폴더가 없습니다: {package_value}"]

    required_files = (
        "reference.mp4",
        "editable.mp4",
        "captions.srt",
        "timeline.csv",
        "edit-manifest.json",
        "사용방법.txt",
    )
    for name in required_files:
        if not (package_dir / name).is_file():
            errors.append(f"편집 호환 패키지 파일이 없습니다: {package_value}/{name}")

    manifest_path = package_dir / "edit-manifest.json"
    if manifest_path.is_file():
        try:
            manifest = load_json(manifest_path)
        except News2ShortsError as exc:
            errors.append(str(exc))
        else:
            if not isinstance(manifest, dict) or manifest.get("version") != EDITOR_PACKAGE_VERSION:
                errors.append("편집 호환 패키지 manifest version이 지원 값과 다릅니다.")
            elif int(manifest.get("scene_count") or 0) != expected_scene_count:
                errors.append("편집 호환 패키지 장면 수가 storyboard와 다릅니다.")

    scene_files = sorted((package_dir / "scenes").glob("scene-*.mp4"))
    if len(scene_files) != expected_scene_count:
        errors.append(
            "편집 호환 패키지의 장면 MP4 수가 storyboard와 다릅니다: "
            f"{len(scene_files)}/{expected_scene_count}"
        )

    for name in ("reference.mp4", "editable.mp4"):
        video_path = package_dir / name
        if not video_path.is_file():
            continue
        try:
            info = probe_video(video_path)
        except News2ShortsError as exc:
            errors.append(str(exc))
            continue
        if info["width"] != OUTPUT_VIDEO_SIZE[0] or info["height"] != OUTPUT_VIDEO_SIZE[1]:
            errors.append(f"편집 호환 영상 해상도가 720x1280이 아닙니다: {name}")
        if not info["has_video"] or not info["has_audio"]:
            errors.append(f"편집 호환 영상의 영상 또는 오디오 스트림이 없습니다: {name}")

    captions_path = package_dir / "captions.srt"
    if captions_path.is_file():
        try:
            captions_path.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append("captions.srt가 UTF-8 형식이 아닙니다.")
    mid_cta_value = str(package_report.get("mid_cta") or "").strip()
    if mid_cta_value:
        if not (package_dir / "scenes" / "mid-cta.mp4").is_file():
            errors.append("편집 호환 패키지에 mid-cta.mp4가 없습니다.")
        if not (package_dir / "audio" / "mid-cta.wav").is_file():
            errors.append("편집 호환 패키지에 mid-cta.wav가 없습니다.")
        timeline_path = package_dir / "timeline.csv"
        if timeline_path.is_file():
            with timeline_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            if not any(row.get("kind") == "mid-cta" for row in rows):
                errors.append("편집 호환 패키지 timeline.csv에 mid-cta 행이 없습니다.")
    return errors


def validate_mid_cta_audio_boundary(render_report: dict) -> list[str]:
    mid_report = render_report.get("mid_cta")
    if not isinstance(mid_report, dict) or mid_report.get("enabled") is not True:
        return []
    if str(render_report.get("delivery_mode") or "") != CONTINUOUS_FLOW_MODE:
        return []
    if not str(render_report.get("tts_provider") or "").strip():
        return []

    errors: list[str] = []
    continuous_report = render_report.get("continuous_flow")
    if not isinstance(continuous_report, dict):
        return ["중간 CTA 렌더 보고서에 continuous_flow 오디오 기록이 없습니다."]
    try:
        body_tts_requests = int(continuous_report.get("body_tts_requests") or 0)
    except (TypeError, ValueError):
        body_tts_requests = 0
    if body_tts_requests != 2:
        errors.append("중간 CTA 본문은 앞뒤 두 번의 완전한 TTS 요청으로 생성해야 합니다.")
    if continuous_report.get("mid_cta_two_part") is not True:
        errors.append("중간 CTA 본문에 two-part 오디오 기록이 없습니다.")
    if continuous_report.get("boundary_preserves_complete_utterances") is not True:
        errors.append("중간 CTA 경계가 완전한 발화를 보존하지 않았습니다.")
    if mid_report.get("boundary_preserves_complete_utterances") is not True:
        errors.append("중간 CTA 자체 보고서에 안전한 발화 경계 기록이 없습니다.")
    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"프로젝트 디렉터리를 찾을 수 없습니다: {project_dir}")
    errors, warnings = validate_project(project_dir, final=args.final)
    project = load_json(project_dir / "project.json")
    assert isinstance(project, dict)
    render_report_path = project_dir / "render-report.json"
    if render_report_path.is_file():
        render_report = load_json(render_report_path)
        if isinstance(render_report, dict) and isinstance(render_report.get("scenes"), list):
            try:
                render_report_version = int(render_report.get("version") or 1)
            except (TypeError, ValueError):
                render_report_version = 1
            if render_report_version >= 3:
                editor_report = render_report.get("editor_package")
                if not isinstance(editor_report, dict) or editor_report.get("enabled") is not True:
                    errors.append("렌더 보고서에 편집 호환 패키지 생성 기록이 없습니다.")
                else:
                    storyboard_for_count = load_json(project_dir / "storyboard.json")
                    storyboard_scenes = (
                        storyboard_for_count.get("scenes", [])
                        if isinstance(storyboard_for_count, dict)
                        else []
                    )
                    errors.extend(
                        validate_editor_package(
                            project_dir,
                            editor_report,
                            len([scene for scene in storyboard_scenes if isinstance(scene, dict)]),
                        )
                    )
            timing_errors, timing_warnings = render_timing_issues(
                project,
                [item for item in render_report["scenes"] if isinstance(item, dict)],
                final=args.final,
            )
            errors.extend(message for message in timing_errors if message not in errors)
            warnings.extend(message for message in timing_warnings if message not in warnings)
            try:
                project_version = int(project.get("version") or 1)
            except (TypeError, ValueError):
                project_version = 1
            if project_version >= 16:
                retention_report = render_report.get("retention_timing")
                if not isinstance(retention_report, dict) or retention_report.get("passed") is not True:
                    errors.append("version 16 렌더 보고서의 답변·조건 타이밍 검증이 통과하지 않았습니다.")
                if str(project.get("delivery_mode") or "") == VISUAL_FIRST_MODE:
                    audio_bed_report = render_report.get("audio_bed")
                    if not isinstance(audio_bed_report, dict) or audio_bed_report.get("enabled") is not True:
                        errors.append("visual-first 렌더 보고서에 생성 BGM 기록이 없습니다.")
                    else:
                        if str(audio_bed_report.get("profile") or "") != VISUAL_FIRST_AUDIO_PROFILE:
                            errors.append("visual-first 렌더 보고서의 BGM profile이 다릅니다.")
                        if audio_bed_report.get("vocals") is not False:
                            errors.append("visual-first 렌더 보고서의 BGM은 무보컬이어야 합니다.")
            mid_cta_rendered = False
            if project_version >= 17:
                configured_mid_cta = mid_cta_config(project)
                mid_mode = str(configured_mid_cta.get("mode") or "disabled")
                mid_report = render_report.get("mid_cta")
                if not isinstance(mid_report, dict):
                    (errors if args.final else warnings).append(
                        "version 17 렌더 보고서에 mid_cta 기록이 없습니다. 다시 렌더하세요."
                    )
                else:
                    mid_cta_rendered = mid_report.get("enabled") is True
                    if mid_mode == "disabled" and mid_cta_rendered:
                        errors.append("사용자가 제외한 중간 CTA가 렌더됐습니다.")
                    if mid_mode == "enabled" and args.final and not mid_cta_rendered:
                        errors.append("사용자가 포함한 중간 CTA가 최종 렌더에 없습니다.")
                    if mid_cta_rendered:
                        errors.extend(validate_mid_cta_audio_boundary(render_report))
                        try:
                            mid_duration = float(mid_report.get("duration") or 0.0)
                        except (TypeError, ValueError):
                            mid_duration = 0.0
                        if not MID_CTA_MIN_DURATION <= mid_duration <= MID_CTA_MAX_DURATION:
                            errors.append("중간 CTA 실제 길이는 1.5-2.0초여야 합니다.")
                        if str(mid_report.get("ui_target_profile") or "") != MID_CTA_UI_TARGET_PROFILE:
                            errors.append("중간 CTA의 YouTube Shorts UI 목표 프로필이 없습니다.")
                        if mid_report.get("fake_button_rendered") is not False:
                            errors.append("중간 CTA는 클릭되지 않는 가짜 버튼을 그릴 수 없습니다.")
                        if mid_report.get("srt_generated") is not False:
                            errors.append("중간 CTA는 별도 SRT 자막을 만들 수 없습니다.")
                        if not str(mid_report.get("insert_after_scene_id") or "").strip():
                            errors.append("중간 CTA 삽입 장면 기록이 없습니다.")
            if args.final and project_version >= 4:
                cta_report = render_report.get("cta_tail")
                if not isinstance(cta_report, dict) or cta_report.get("enabled") is not True:
                    errors.append("최종 렌더 보고서에 공통 CTA 테일 적용 기록이 없습니다.")
                else:
                    try:
                        cta_duration = float(cta_report.get("duration") or 0.0)
                    except (TypeError, ValueError):
                        cta_duration = 0.0
                    if not MIN_CTA_TAIL_DURATION <= cta_duration <= MAX_CTA_TAIL_DURATION:
                        errors.append(
                            "최종 렌더의 CTA 테일 길이가 "
                            f"{MIN_CTA_TAIL_DURATION:.1f}-{MAX_CTA_TAIL_DURATION:.1f}초가 아닙니다."
                        )
                    if project_version >= 16 and cta_duration > DEFAULT_CTA_TAIL_DURATION + 0.01:
                        errors.append("version 16 최종 CTA 테일은 2초 이하여야 합니다.")
                    if (
                        project_version >= 16
                        and str(project.get("delivery_mode") or "") == VISUAL_FIRST_MODE
                        and cta_report.get("voice_enabled") is not False
                    ):
                        errors.append("visual-first 최종 CTA는 무음이어야 합니다.")
                    if project_version >= 8:
                        cta_variant = str(cta_report.get("variant") or "")
                        cta_config = project.get("cta_tail")
                        keep_tail_after_mid = (
                            isinstance(cta_config, dict)
                            and cta_config.get("keep_after_mid_cta") is True
                        )
                        if project_version >= 17 and mid_cta_rendered and not keep_tail_after_mid:
                            if cta_variant != "brand-close":
                                errors.append("중간 CTA가 있으면 최종 CTA는 brand-close여야 합니다.")
                            if cta_duration > BRAND_CLOSE_DURATION + 0.01:
                                errors.append("중간 CTA 이후 브랜드 마감은 0.8초 이하여야 합니다.")
                            if cta_report.get("voice_enabled") is not False:
                                errors.append("중간 CTA 이후 브랜드 마감은 무음이어야 합니다.")
                        else:
                            if cta_variant not in CTA_TAIL_VARIANTS:
                                errors.append("최종 렌더의 CTA variant가 subscribe 또는 comment가 아닙니다.")
                            expected_cta_strategy = (
                                CTA_TAIL_AFTER_MID_SELECTION_STRATEGY
                                if mid_cta_rendered and keep_tail_after_mid
                                else CTA_TAIL_SELECTION_STRATEGY
                            )
                            if str(cta_report.get("selection_strategy") or "") != expected_cta_strategy:
                                errors.append("최종 렌더의 CTA 자동 선택 전략 기록이 없습니다.")
                            if project.get("sensitive_topic") is True and cta_variant != "subscribe":
                                errors.append("민감 뉴스의 최종 CTA는 subscribe여야 합니다.")
                        if cta_variant == "comment":
                            if "댓글" not in str(cta_report.get("prompt") or ""):
                                errors.append("댓글형 CTA 화면에 댓글 행동이 표시되지 않았습니다.")
                            if "여러분의 생각을 댓글로 남겨주세요" not in str(
                                cta_report.get("narration") or ""
                            ):
                                errors.append("댓글형 CTA 음성에 요청한 댓글 유도 문구가 없습니다.")
                    if project_version >= 9:
                        thumbnail_report = render_report.get("thumbnail")
                        if not isinstance(thumbnail_report, dict):
                            errors.append("최종 렌더 보고서에 별도 호기심 유도 썸네일 기록이 없습니다.")
                        else:
                            if thumbnail_report.get("separate_asset") is not True:
                                errors.append("최종 썸네일은 영상 프레임이 아닌 별도 이미지여야 합니다.")
                            if thumbnail_report.get("question_led") is not True:
                                errors.append("최종 썸네일은 시민 관점의 질문형 훅을 사용해야 합니다.")
                            if str(thumbnail_report.get("purpose") or "") != "dedicated-curiosity-thumbnail":
                                errors.append("최종 썸네일의 호기심 유도 제작 목적 기록이 없습니다.")
                            if project_version >= 13:
                                if thumbnail_report.get("attention_first") is not True:
                                    errors.append("최종 썸네일에 attention-first 제작 기록이 없습니다.")
                                if not str(thumbnail_report.get("badge") or "").strip():
                                    errors.append("최종 썸네일에 주제별 긴장 배지 기록이 없습니다.")
                                if str(thumbnail_report.get("thumbnail_style") or "") not in {
                                    "presenter-led",
                                    "evidence-led",
                                }:
                                    errors.append("최종 썸네일의 적용 스타일 기록이 없습니다.")
                                if thumbnail_report.get("presenter_used") is True and thumbnail_report.get(
                                    "presenter_context_reviewed"
                                ) is not True:
                                    errors.append("진행자형 썸네일의 비당사자 맥락 검토 기록이 없습니다.")
            if args.final and project_version >= 7:
                brand_report = render_report.get("brand_intro")
                if not isinstance(brand_report, dict) or brand_report.get("enabled") is not True:
                    errors.append("최종 렌더 보고서에 공통 인트로 적용 기록이 없습니다.")
                else:
                    expected_brand_mode = str(
                        brand_intro_config(project).get("mode") or BRAND_MODE_LEGACY_FULL
                    ).strip()
                    if str(brand_report.get("mode") or BRAND_MODE_LEGACY_FULL) != expected_brand_mode:
                        errors.append("최종 렌더 보고서의 브랜드 모드가 프로젝트 설정과 다릅니다.")
                    expected_brand_asset = str(
                        brand_intro_config(project).get("asset") or BRAND_INTRO_ASSET_ID
                    ).strip()
                    if str(brand_report.get("asset") or "") != expected_brand_asset:
                        errors.append("최종 렌더 보고서의 공통 인트로 자산이 프로젝트 설정과 다릅니다.")
                    if expected_brand_mode == BRAND_MODE_CORNER_LOGO:
                        if float(brand_report.get("lead_in_seconds") or 0.0) != 0.0:
                            errors.append("corner-logo 최종 렌더는 브랜드 선행 시간이 없어야 합니다.")
                        if str(brand_report.get("position") or "") != "top-left":
                            errors.append("corner-logo 최종 렌더 위치는 top-left여야 합니다.")
                    else:
                        if str(brand_report.get("transition") or "") not in ALLOWED_BRAND_INTRO_TRANSITIONS:
                            errors.append("최종 렌더 보고서의 인트로 전환 효과가 지원 목록과 다릅니다.")
                        try:
                            transition_duration = float(brand_report.get("transition_duration") or 0.0)
                        except (TypeError, ValueError):
                            transition_duration = 0.0
                        if not MIN_BRAND_INTRO_TRANSITION_DURATION <= transition_duration <= MAX_BRAND_INTRO_TRANSITION_DURATION:
                            errors.append("최종 렌더 보고서의 인트로 전환 길이가 허용 범위와 다릅니다.")
    videos: list[dict] = []
    for name in ("preview.mp4", "short.mp4"):
        path = project_dir / name
        if path.is_file():
            try:
                info = probe_video(path)
                videos.append(info)
                expected_width, expected_height = OUTPUT_VIDEO_SIZE
                if info["width"] != expected_width or info["height"] != expected_height:
                    errors.append(f"영상 해상도가 {expected_width}x{expected_height}이 아닙니다: {name}")
                if not info["has_audio"] or not info["has_video"]:
                    errors.append(f"영상 또는 오디오 스트림이 없습니다: {name}")
                if info["duration"] > 180:
                    errors.append(f"Shorts 최대 길이를 넘습니다: {name}: {info['duration']:.1f}초")
                elif info["duration"] > 60:
                    warnings.append(f"1분을 넘는 Shorts입니다. Content ID와 음악 권리를 확인하세요: {name}")
            except News2ShortsError as exc:
                errors.append(str(exc))
    report = {
        "ok": not errors,
        "checked_at": iso_now(),
        "final_rules": args.final,
        "errors": errors,
        "warnings": warnings,
        "videos": videos,
    }
    if args.report:
        report_path = resolve_project_file(project_dir, args.report, must_exist=False)
        write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def upload_package_markdown(publish: dict) -> str:
    settings = publish.get("upload_settings")
    errors: list[str] = []
    if not isinstance(settings, dict):
        raise News2ShortsError("YouTube 업로드 정보를 만들 수 없습니다: upload_settings가 없습니다.")

    tags = publish.get("tags")
    raw_title = str(publish.get("title") or "").strip()
    raw_description = str(publish.get("description") or "").strip()
    pinned_comment = str(publish.get("pinned_comment") or "").strip()
    source_lines = publish.get("source_lines")
    if not raw_title:
        errors.append("제목")
    if not raw_description:
        errors.append("설명")
    if not pinned_comment:
        errors.append("고정 댓글")
    if not isinstance(tags, list) or not any(
        isinstance(tag, str) and tag.strip() for tag in tags
    ):
        errors.append("태그")
    if not isinstance(source_lines, list) or not any(
        isinstance(line, str) and line.strip() for line in source_lines
    ):
        errors.append("출처 문구")

    required_text_settings = {
        "thumbnail_hook": "썸네일 훅",
        "thumbnail_subhook": "썸네일 보조 문구",
        "thumbnail_badge": "썸네일 긴장 배지",
        "thumbnail_style": "썸네일 구성",
        "thumbnail_note": "썸네일 안내",
        "playlist": "재생목록",
        "category": "카테고리",
        "video_language": "영상 언어",
    }
    for field, label in required_text_settings.items():
        if not str(settings.get(field) or "").strip():
            errors.append(label)

    thumbnail_method = str(settings.get("thumbnail_method") or "").strip()
    thumbnail_file = str(settings.get("thumbnail_file") or "").strip()
    thumbnail_status = str(settings.get("thumbnail_status") or "").strip()
    if thumbnail_method not in {"video_frame", "file_upload"}:
        errors.append("썸네일 방식")
    if thumbnail_method == "file_upload" and not thumbnail_file:
        if thumbnail_status != "blocked_rights":
            errors.append("썸네일 파일 또는 blocked_rights 상태")

    audience = str(settings.get("audience") or "").strip()
    altered_content = str(settings.get("altered_content") or "").strip()
    age_restriction = str(settings.get("age_restriction") or "").strip()
    visibility = str(settings.get("visibility") or "").strip()
    schedule_at = str(settings.get("schedule_at") or "").strip()
    if audience not in {"made_for_kids", "not_made_for_kids"}:
        errors.append("시청자층")
    if altered_content not in {"yes", "no"}:
        errors.append("변경·합성 콘텐츠 공개 결정")
    if age_restriction not in {"none", "18_plus"}:
        errors.append("연령 제한 결정")
    if visibility not in {"private", "unlisted", "public", "scheduled"}:
        errors.append("공개 상태")
    if visibility == "scheduled" and not schedule_at:
        errors.append("예약 공개 시각")
    if not isinstance(settings.get("paid_promotion"), bool):
        errors.append("유료 프로모션 결정")
    if not isinstance(settings.get("allow_comments"), bool):
        errors.append("댓글 허용 결정")

    if errors:
        raise News2ShortsError(
            "YouTube 업로드 정보를 만들 수 없습니다. 임의의 '미작성' 대신 먼저 채우세요: "
            + ", ".join(dict.fromkeys(errors))
        )

    audience_labels = {
        "made_for_kids": "예, 아동용입니다",
        "not_made_for_kids": "아니요, 아동용이 아닙니다",
    }
    thumbnail_labels = {
        "video_frame": "동영상에서 선택",
        "file_upload": "파일 업로드",
    }
    altered_labels = {"yes": "예", "no": "아니요"}
    age_labels = {"none": "없음", "18_plus": "만 18세 이상"}
    visibility_labels = {
        "private": "비공개",
        "unlisted": "일부 공개",
        "public": "공개",
        "scheduled": "예약 공개",
    }

    title = title_with_hashtags(raw_title, tags)
    description = deduplicated_upload_description(raw_title, raw_description)
    if not title or not description:
        raise News2ShortsError(
            "YouTube 업로드 정보를 만들 수 없습니다. 제목·설명 중복 제거 후 공개 문구가 비었습니다."
        )
    tag_text = ", ".join(
        hashtag
        for hashtag in (tag_to_title_hashtag(tag) for tag in tags)
        if hashtag
    )
    thumbnail_file_display = (
        thumbnail_file
        if thumbnail_file
        else "생성 차단: 권리 승인 이미지 필요"
    )
    thumbnail_note = str(settings["thumbnail_note"]).strip()
    thumbnail_hook = str(settings["thumbnail_hook"]).strip()
    thumbnail_subhook = str(settings["thumbnail_subhook"]).strip()
    thumbnail_badge = str(settings["thumbnail_badge"]).strip()
    thumbnail_style = str(settings["thumbnail_style"]).strip()
    playlist = str(settings["playlist"]).strip()
    paid_promotion = settings["paid_promotion"]
    allow_comments = settings["allow_comments"]

    lines = [
        "## YouTube 업로드 정보",
        "",
        f"### 제목 ({len(title)}/{YOUTUBE_TITLE_LIMIT}자)",
        title,
        "",
        f"### 설명 ({len(description)}/{YOUTUBE_DESCRIPTION_LIMIT}자 · 링크 없음)",
        description,
        "",
        "### 태그",
        tag_text,
        "",
        "### 세부 설정",
        f"- 썸네일 방식: {thumbnail_labels[thumbnail_method]}",
        f"- 썸네일 파일: {thumbnail_file_display}",
        f"- 썸네일 훅: {thumbnail_hook}",
        f"- 썸네일 보조 문구: {thumbnail_subhook}",
        f"- 썸네일 긴장 배지: {thumbnail_badge}",
        f"- 썸네일 구성: {thumbnail_style}",
        f"- 썸네일 안내: {thumbnail_note}",
        f"- 재생목록: {playlist}",
        f"- 시청자층: {audience_labels[audience]}",
        f"- 카테고리: {str(settings['category']).strip()}",
        f"- 영상 언어: {str(settings['video_language']).strip()}",
        f"- 변경·합성 콘텐츠 공개: {altered_labels[altered_content]}",
        f"- 유료 프로모션: {'예' if paid_promotion else '아니요'}",
        f"- 연령 제한: {age_labels[age_restriction]}",
        f"- 댓글 허용: {'예' if allow_comments else '아니요'}",
        f"- 공개 상태: {visibility_labels[visibility]}",
    ]
    if visibility == "scheduled":
        lines.append(f"- 예약 공개 시각: {schedule_at}")
    lines.extend(["", "### 고정 댓글", pinned_comment])
    return "\n".join(lines)


def cmd_upload_package(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        fail(f"프로젝트 디렉터리를 찾을 수 없습니다: {project_dir}")
    publish = load_json(project_dir / "publish.json")
    if not isinstance(publish, dict):
        raise News2ShortsError("publish.json의 최상위 값은 객체여야 합니다.")
    print(upload_package_markdown(publish))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="news2shorts local MVP tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="로컬 렌더 환경과 선택 기능을 점검합니다.")
    doctor.add_argument("--json", action="store_true", help="JSON으로 출력합니다.")
    doctor.set_defaults(handler=cmd_doctor)

    configure_typecast = subparsers.add_parser(
        "configure-typecast",
        help="Typecast API 키를 macOS 키체인에 안전하게 저장합니다.",
    )
    configure_typecast.set_defaults(handler=cmd_configure_typecast)

    discover = subparsers.add_parser("discover", help="NAVER API HUB에서 최근 뉴스 후보를 찾습니다.")
    discover.add_argument("--query", action="append", help="검색어입니다. 여러 번 지정할 수 있습니다.")
    discover.add_argument("--hours", type=int, default=30, help="현재부터 조회할 시간 범위입니다.")
    discover.add_argument("--limit", type=int, default=30, help="검색어별 기사 수입니다.")
    discover.add_argument(
        "--candidates",
        type=int,
        choices=[DISCOVERY_CANDIDATE_COUNT],
        default=DISCOVERY_CANDIDATE_COUNT,
        help="출력할 후보 수입니다. 검증된 10개로 고정됩니다.",
    )
    discover.add_argument("--skip-trends", action="store_true", help="검색어 트렌드 재검증을 생략합니다.")
    discover.add_argument(
        "--hot-real-news",
        action="store_true",
        help="최근 24시간, 최근 6시간 내 서로 다른 출처 2곳 이상인 시민 영향 뉴스를 우선합니다.",
    )
    discover.add_argument(
        "--community-signals",
        help="공개 커뮤니티에서 읽기 전용으로 확인한 최소 메타데이터 JSON 경로입니다.",
    )
    discover.add_argument(
        "--project-history-root",
        default=DEFAULT_PROJECT_HISTORY_ROOT,
        help="이미 다룬 뉴스 주제를 제외할 기존 projects 루트입니다. 기본값은 ./projects입니다.",
    )
    discover.add_argument("--output", help="결과 JSON 경로입니다.")
    discover.set_defaults(handler=cmd_discover)

    init = subparsers.add_parser("init", help="새 제작 프로젝트를 초기화합니다.")
    init.add_argument("--title", required=True, help="뉴스 주제 또는 영상 제목입니다.")
    init.add_argument("--source-url", default="", help="입력 뉴스 URL입니다.")
    init.add_argument("--project-dir", help="프로젝트 디렉터리입니다.")
    init.add_argument(
        "--duration",
        type=int,
        help="목표 영상 길이입니다. 기본값은 continuous-flow 20초, visual-first 12초입니다.",
    )
    init.add_argument("--sensitive", action="store_true", help="민감 뉴스 검증 규칙을 적용합니다.")
    init.add_argument(
        "--delivery-mode",
        choices=tuple(sorted(DELIVERY_MODES)),
        default=CONTINUOUS_FLOW_MODE,
        help="continuous-flow 내레이션형 또는 visual-first 화면·BGM형 제작 모드입니다.",
    )
    init.add_argument(
        "--narration-style",
        choices=tuple(sorted(NARRATION_STYLES)),
        default=NARRATION_STYLE_STANDARD,
        help="기존 standard 또는 친구 설명형 cc-helper-conversational 내레이션 말투를 기록합니다.",
    )
    init.add_argument(
        "--visual-mode",
        choices=tuple(sorted(VISUAL_MODES)),
        default="standard",
        help="standard, hot-real-news 또는 whiteboard 시각 제작 모드를 기록합니다.",
    )
    init.add_argument(
        "--international-source-country",
        default="",
        help="한국 시민 영향이 있는 국제 실제사건의 ISO 2자리 현장 국가 코드입니다.",
    )
    init.add_argument(
        "--international-source-locale",
        default="",
        help="국제 실제사건 원본 시각의 로케일입니다. 예: ne-NP",
    )
    init.add_argument(
        "--international-citizen-stake",
        default="",
        help="국제 실제사건이 한국 시민의 안전·권리에 미치는 직접 영향입니다.",
    )
    init.add_argument(
        "--style",
        "--format",
        dest="style",
        choices=tuple(sorted(NEW_PROJECT_TEMPLATES)),
        default="quick-reveal",
        help="새 프로젝트는 quick-reveal만 지원합니다.",
    )
    init.add_argument(
        "--format-mode",
        choices=("auto", "manual"),
        default="auto",
        help="뉴스 구조에 따른 자동 선택인지 사용자 지정인지 기록합니다.",
    )
    init.add_argument(
        "--format-reason",
        default="",
        help="선택한 포맷이 뉴스 구조에 맞는 이유입니다.",
    )
    init.add_argument(
        "--format-confidence",
        choices=("low", "medium", "high"),
        default="medium",
        help="포맷 선택 신뢰도입니다.",
    )
    init.add_argument(
        "--hook-type",
        choices=tuple(sorted(HOOK_TYPES)),
        default="issue-tension",
        help="시민 관점의 질문으로 시작해 사실을 왜곡하지 않고 호기심을 여는 후크 유형입니다.",
    )
    init.add_argument(
        "--mid-cta-mode",
        choices=tuple(sorted(MID_CTA_MODES)),
        default="auto",
        help="중간 구독 CTA를 자동 선택, 강제 포함 또는 제외합니다.",
    )
    init.set_defaults(handler=cmd_init)

    optimize_images = subparsers.add_parser(
        "optimize-images",
        help="생성 이미지를 프로젝트 기본 크기로 축소하고 권리 기록에 크기를 남깁니다.",
    )
    optimize_images.add_argument("--project-dir", required=True, help="프로젝트 디렉터리입니다.")
    optimize_images.add_argument("--max-width", type=int, help="최대 이미지 너비입니다.")
    optimize_images.add_argument("--max-height", type=int, help="최대 이미지 높이입니다.")
    optimize_images.set_defaults(handler=cmd_optimize_images)

    collect_internet = subparsers.add_parser(
        "collect-internet-visual",
        help="공개 HTTPS 이미지를 출처·권리 상태와 함께 뉴스 장면의 로컬 검토 자산으로 등록합니다.",
    )
    collect_internet.add_argument("--project-dir", required=True)
    collect_internet.add_argument("--scene-id", required=True)
    collect_internet.add_argument("--image-url", required=True, help="공개 HTTPS 직접 이미지 URL입니다.")
    collect_internet.add_argument("--source-page", required=True, help="이미지 원본·기사의 canonical HTTPS 페이지입니다.")
    collect_internet.add_argument("--query", default="", help="이미지 검색어 또는 수집 근거입니다.")
    collect_internet.add_argument("--creator", default="")
    collect_internet.add_argument("--publisher", default="")
    collect_internet.add_argument("--attribution", default="")
    collect_internet.add_argument(
        "--permission-status",
        choices=("unknown", "review_required", "owned", "licensed", "permission_confirmed"),
        default="review_required",
    )
    collect_internet.add_argument("--permission-reference", default="")
    collect_internet.add_argument(
        "--relevance-level",
        choices=tuple(sorted(ALLOWED_VISUAL_RELEVANCE_LEVELS)),
        default="direct",
    )
    collect_internet.add_argument("--relevance-note", required=True)
    collect_internet.add_argument("--confirm-news-relevance", action="store_true")
    collect_internet.add_argument(
        "--visual-locale",
        help="한국 대응 자료는 ko-KR, 국제 실제사건 자료는 프로젝트 source_locale 또는 neutral입니다.",
    )
    collect_internet.add_argument(
        "--confirm-korean-context",
        action="store_true",
        help="한국어 표지판·국내 도로·건축·차량 환경 등 한국 배경을 육안 확인했습니다.",
    )
    collect_internet.add_argument(
        "--korean-context-note",
        default="",
        help="이미지가 한국 배경임을 보여주는 구체적인 시각 근거입니다.",
    )
    collect_internet.add_argument("--source-country", default="")
    collect_internet.add_argument("--confirm-source-event-context", action="store_true")
    collect_internet.add_argument(
        "--source-event-context-note",
        default="",
        help="국제 실제사건의 장소·시점·행동이 장면과 맞는 구체적인 근거입니다.",
    )
    collect_internet.add_argument("--confirm-whiteboard-text-free", action="store_true")
    collect_internet.add_argument("--output", help="프로젝트 내부 PNG 경로입니다.")
    collect_internet.add_argument("--overwrite", action="store_true")
    collect_internet.set_defaults(handler=cmd_collect_internet_visual)

    prepare_whiteboard = subparsers.add_parser(
        "prepare-whiteboard",
        help="뉴스 장면의 실제 이미지·영상 프레임을 권리 상태를 상속한 whiteboard 프로젝트로 준비합니다.",
    )
    prepare_whiteboard.add_argument("--project-dir", required=True, help="news2shorts 프로젝트입니다.")
    prepare_whiteboard.add_argument(
        "--output-dir",
        default="whiteboard-project",
        help="뉴스 프로젝트 내부의 whiteboard 출력 폴더입니다.",
    )
    prepare_whiteboard.add_argument("--overwrite", action="store_true")
    prepare_whiteboard.set_defaults(handler=cmd_prepare_whiteboard)

    review_source_audio = subparsers.add_parser(
        "review-source-audio",
        help="source-video 장면의 음성을 전사해 예상 대사와 컷 경계를 검토합니다.",
    )
    review_source_audio.add_argument("--project-dir", required=True, help="프로젝트 디렉터리입니다.")
    review_source_audio.add_argument(
        "--scene-id",
        action="append",
        help="검토할 source-video 장면 ID입니다. 생략하면 모든 source-video 장면을 검사합니다.",
    )
    review_source_audio.add_argument(
        "--backend",
        choices=("auto", "openai-whisper-cli", "transcript-file"),
        default="auto",
        help="자동은 설치된 로컬 OpenAI Whisper CLI를 사용합니다.",
    )
    review_source_audio.add_argument(
        "--transcript-file",
        help="장면별 text와 선택적 segments를 담은 검토된 UTF-8 JSON 또는 단일 장면 텍스트입니다.",
    )
    review_source_audio.add_argument("--language", default="ko", help="Whisper 전사 언어입니다.")
    review_source_audio.add_argument("--model", default="small", help="로컬 Whisper 모델 이름입니다.")
    review_source_audio.add_argument(
        "--model-dir",
        default="~/.cache/whisper",
        help="로컬 Whisper 모델 디렉터리입니다.",
    )
    review_source_audio.add_argument(
        "--allow-model-download",
        action="store_true",
        help="지정한 로컬 Whisper 모델이 없을 때 다운로드를 허용합니다.",
    )
    review_source_audio.add_argument(
        "--confirm-timing-reviewed",
        action="store_true",
        help="시간 정보 없는 전사 파일을 실제 영상과 청취 대조해 컷 경계를 확인했습니다.",
    )
    review_source_audio.set_defaults(handler=cmd_review_source_audio)

    render = subparsers.add_parser(
        "render",
        help="스토리보드를 세로 MP4와 CapCut/Vrew 편집 호환 패키지로 렌더링합니다.",
    )
    render.add_argument("--project-dir", required=True, help="프로젝트 디렉터리입니다.")
    render.add_argument("--draft", action="store_true", help="승인 전 미리보기 영상을 만듭니다.")
    render.add_argument("--no-tts", action="store_true", help="내레이션 대신 무음을 사용합니다.")
    render.add_argument(
        "--tts-provider",
        choices=("typecast", "local"),
        default="typecast",
        help="TTS 제공자입니다. 기본값은 typecast입니다.",
    )
    render.add_argument("--voice", default="Yuna", help="local TTS의 macOS say 음성 이름입니다.")
    render.add_argument("--rate", type=int, default=220, help="local TTS의 macOS say 말하기 속도입니다.")
    render.add_argument(
        "--typecast-voice",
        help=(
            "Typecast 보이스입니다. 생략하거나 auto면 콘텐츠에 맞춰 자동 선택합니다. "
            "수동 후보: Daeun, Seohyeon, Piljae, Moonjung, Kangil."
        ),
    )
    render.add_argument(
        "--typecast-tempo",
        type=float,
        default=1.05,
        help="Typecast 말하기 속도 배율입니다. 기본값은 1.05입니다.",
    )
    render.add_argument("--output", help="프로젝트 내부의 출력 파일명입니다.")
    render.add_argument("--overwrite", action="store_true", help="기존 출력 파일을 덮어씁니다.")
    render.add_argument(
        "--visual-mode",
        choices=tuple(sorted(VISUAL_MODES)),
        help="project.json에 기록된 시각 모드와 일치하는 렌더 모드입니다.",
    )
    render.add_argument(
        "--whiteboard-project",
        help="뉴스 프로젝트 내부의 준비된 whiteboard 프로젝트 경로입니다.",
    )
    render.add_argument(
        "--confirm-whiteboard-review",
        action="store_true",
        help="whiteboard 장면 이미지와 annotation을 확인했음을 기록합니다.",
    )
    render.add_argument(
        "--style",
        "--format",
        dest="style",
        choices=tuple(sorted(SUPPORTED_TEMPLATES)),
        help="이번 렌더에 적용할 영상 스타일입니다.",
    )
    render.set_defaults(handler=cmd_render)

    thumbnail = subparsers.add_parser(
        "thumbnail",
        help="권리 승인된 서로 다른 장면 이미지를 합성해 고자극 세로 썸네일을 만듭니다.",
    )
    thumbnail.add_argument("--project-dir", required=True, help="프로젝트 디렉터리입니다.")
    thumbnail.add_argument("--output", default=DEFAULT_THUMBNAIL_PATH, help="프로젝트 내부 JPG 경로입니다.")
    thumbnail.add_argument("--overwrite", action="store_true", help="기존 썸네일 파일을 덮어씁니다.")
    thumbnail.set_defaults(handler=cmd_thumbnail)

    validate = subparsers.add_parser("validate", help="프로젝트와 생성 영상을 검사합니다.")
    validate.add_argument("--project-dir", required=True, help="프로젝트 디렉터리입니다.")
    validate.add_argument("--final", action="store_true", help="최종 렌더 기준을 적용합니다.")
    validate.add_argument("--report", help="프로젝트 내부에 저장할 보고서 파일명입니다.")
    validate.set_defaults(handler=cmd_validate)

    upload_package = subparsers.add_parser(
        "upload-package",
        help="publish.json을 YouTube 업로드용 한국어 안내로 출력합니다.",
    )
    upload_package.add_argument("--project-dir", required=True, help="프로젝트 디렉터리입니다.")
    upload_package.set_defaults(handler=cmd_upload_package)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except News2ShortsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
