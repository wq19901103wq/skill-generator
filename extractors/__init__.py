"""
文件提取模块 - 从各种文件格式中提取个人信息

支持两种模式：
1. 规则提取（PersonaExtractor）- 基于正则，适合简历
2. LLM 提取（UniversalExtractor）- 智能识别任意资料类型
"""

from .file_parser import FileParser
from .persona_extractor import PersonaExtractor
from .chat_parser import ChatParser
from .universal_extractor import (
    UniversalExtractor,
    LLMBackend,
    ExtractedInfo,
    DocumentType,
    extract_with_llm
)

__all__ = [
    'FileParser', 
    'PersonaExtractor', 
    'ChatParser',
    'UniversalExtractor',
    'LLMBackend',
    'ExtractedInfo',
    'DocumentType',
    'extract_with_llm'
]
