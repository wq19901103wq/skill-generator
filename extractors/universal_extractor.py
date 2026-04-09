#!/usr/bin/env python3
"""
Universal Extractor - LLM 驱动的通用信息提取器

使用 LLM 智能分析任意类型的资料，自动识别资料类型并提取结构化信息。

支持的资料类型：
- 简历/个人介绍 → 数字分身
- 产品文档/手册 → FAQ 助手
- 技术文档/API 文档 → 技术助手
- 聊天记录 → 聊天风格分析
- 论文/报告 → 学术助手
- 任意文本 → 通用知识助手
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DocumentType(Enum):
    """文档类型枚举"""
    RESUME = "resume"                    # 简历/个人介绍
    PRODUCT_DOCS = "product_docs"        # 产品文档
    TECHNICAL_DOCS = "technical_docs"    # 技术文档/API 文档
    CHAT_LOGS = "chat_logs"              # 聊天记录
    ACADEMIC_PAPER = "academic_paper"    # 学术论文
    FAQ = "faq"                          # FAQ/问答
    GENERAL_KNOWLEDGE = "general"        # 通用知识
    UNKNOWN = "unknown"                  # 未知类型


@dataclass
class ExtractedInfo:
    """提取的信息结构"""
    document_type: DocumentType
    document_type_name: str
    name: str = ""                       # 主体名称（人名/产品名/项目名）
    title: str = ""                      # 标题/职位/产品类型
    description: str = ""                # 描述/简介
    key_points: List[str] = field(default_factory=list)      # 关键要点
    structured_data: Dict[str, Any] = field(default_factory=dict)  # 类型特定的结构化数据
    suggested_skill_type: str = ""       # 建议生成的 Skill 类型
    suggested_triggers: List[str] = field(default_factory=list)  # 建议的触发词
    persona_info: Dict[str, str] = field(default_factory=dict)  # 兼容旧的 PERSONA_INFO 格式


class LLMBackend:
    """LLM 后端接口"""
    
    def __init__(self, provider: str = "openai", api_key: str = None, base_url: str = None):
        self.provider = provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
    def complete(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
        """
        调用 LLM 完成文本生成
        
        支持多种后端：openai, anthropic, kimi, local 等
        """
        if self.provider == "openai":
            return self._openai_complete(prompt, system_prompt, max_tokens)
        elif self.provider == "anthropic":
            return self._anthropic_complete(prompt, system_prompt, max_tokens)
        else:
            # 默认使用简单的规则后备
            return self._fallback_complete(prompt, system_prompt)
    
    def _openai_complete(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        """OpenAI API 调用"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ LLM 调用失败: {e}")
            return self._fallback_complete(prompt, system_prompt)
    
    def _anthropic_complete(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        """Anthropic API 调用"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"⚠️ LLM 调用失败: {e}")
            return self._fallback_complete(prompt, system_prompt)
    
    def _fallback_complete(self, prompt: str, system_prompt: str) -> str:
        """后备方案：返回错误提示"""
        return json.dumps({
            "error": "LLM 未配置",
            "message": "请设置 OPENAI_API_KEY 或其他 LLM 提供商的 API 密钥"
        })


class UniversalExtractor:
    """通用信息提取器 - LLM 驱动"""
    
    def __init__(self, llm_backend: LLMBackend = None):
        self.llm = llm_backend or LLMBackend()
    
    def extract(self, content: str, hint: str = None) -> ExtractedInfo:
        """
        从文本中提取结构化信息
        
        Args:
            content: 文本内容
            hint: 用户提示，帮助 LLM 理解上下文
        
        Returns:
            ExtractedInfo 对象
        """
        # 步骤1：识别文档类型
        doc_type = self._identify_document_type(content, hint)
        
        # 步骤2：根据类型提取信息
        if doc_type == DocumentType.RESUME:
            return self._extract_resume(content, hint)
        elif doc_type == DocumentType.PRODUCT_DOCS:
            return self._extract_product_docs(content, hint)
        elif doc_type == DocumentType.TECHNICAL_DOCS:
            return self._extract_technical_docs(content, hint)
        elif doc_type == DocumentType.CHAT_LOGS:
            return self._extract_chat_logs(content, hint)
        elif doc_type == DocumentType.FAQ:
            return self._extract_faq(content, hint)
        else:
            return self._extract_general(content, hint)
    
    def _identify_document_type(self, content: str, hint: str = None) -> DocumentType:
        """使用 LLM 识别文档类型"""
        system_prompt = """你是一个文档分析专家。请分析输入的文本，判断它属于以下哪种类型：
- resume: 简历、个人介绍、求职信
- product_docs: 产品文档、产品手册、功能说明
- technical_docs: 技术文档、API文档、代码文档
- chat_logs: 聊天记录、对话记录
- academic_paper: 学术论文、研究报告
- faq: FAQ、问答文档、常见问题
- general: 其他通用知识文档

只返回一个单词（类型名），不要解释。"""
        
        content_sample = content[:3000]  # 取前3000字符
        prompt = f"分析以下文档的类型：\n\n{content_sample}\n\n文档类型："
        
        if hint:
            prompt = f"用户提示：{hint}\n\n{prompt}"
        
        result = self.llm.complete(prompt, system_prompt).strip().lower()
        
        # 映射到枚举
        type_mapping = {
            'resume': DocumentType.RESUME,
            'product_docs': DocumentType.PRODUCT_DOCS,
            'product': DocumentType.PRODUCT_DOCS,
            'technical_docs': DocumentType.TECHNICAL_DOCS,
            'technical': DocumentType.TECHNICAL_DOCS,
            'chat_logs': DocumentType.CHAT_LOGS,
            'chat': DocumentType.CHAT_LOGS,
            'academic_paper': DocumentType.ACADEMIC_PAPER,
            'academic': DocumentType.ACADEMIC_PAPER,
            'faq': DocumentType.FAQ,
            'general': DocumentType.GENERAL_KNOWLEDGE,
        }
        
        return type_mapping.get(result, DocumentType.UNKNOWN)
    
    def _extract_resume(self, content: str, hint: str = None) -> ExtractedInfo:
        """提取简历信息"""
        system_prompt = """你是一个简历分析专家。请从简历中提取以下信息，返回 JSON 格式：
{
    "name": "姓名",
    "title": "职位/头衔",
    "company": "当前公司",
    "description": "个人简介（2-3句话）",
    "key_points": ["关键经历1", "关键经历2"],
    "structured_data": {
        "教育背景": "...",
        "工作经历": "...",
        "技能": "...",
        "联系方式": "..."
    }
}"""
        
        prompt = f"分析以下简历：\n\n{content[:5000]}"
        result = self.llm.complete(prompt, system_prompt)
        
        try:
            data = json.loads(result)
        except:
            data = self._parse_json_fuzzy(result)
        
        return ExtractedInfo(
            document_type=DocumentType.RESUME,
            document_type_name="简历/个人介绍",
            name=data.get('name', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            key_points=data.get('key_points', []),
            structured_data=data.get('structured_data', {}),
            suggested_skill_type="personal_digital_twin",
            suggested_triggers=["@" + data.get('name', '用户'), data.get('name', ''), "简历"],
            persona_info=data.get('structured_data', {})
        )
    
    def _extract_product_docs(self, content: str, hint: str = None) -> ExtractedInfo:
        """提取产品文档信息"""
        system_prompt = """你是一个产品分析专家。请从产品文档中提取以下信息，返回 JSON 格式：
{
    "name": "产品名称",
    "title": "产品类型/定位",
    "description": "产品简介（2-3句话）",
    "key_points": ["核心功能1", "核心功能2", "核心功能3"],
    "structured_data": {
        "产品概述": "...",
        "核心功能": "...",
        "使用场景": "...",
        "常见问题": "..."
    }
}"""
        
        prompt = f"分析以下产品文档：\n\n{content[:5000]}"
        result = self.llm.complete(prompt, system_prompt)
        
        try:
            data = json.loads(result)
        except:
            data = self._parse_json_fuzzy(result)
        
        return ExtractedInfo(
            document_type=DocumentType.PRODUCT_DOCS,
            document_type_name="产品文档",
            name=data.get('name', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            key_points=data.get('key_points', []),
            structured_data=data.get('structured_data', {}),
            suggested_skill_type="product_assistant",
            suggested_triggers=[data.get('name', ''), "产品", "怎么用", "功能"],
            persona_info={
                "产品名称": data.get('name', ''),
                "产品简介": data.get('description', ''),
                "核心功能": "\n".join(data.get('key_points', [])),
                **data.get('structured_data', {})
            }
        )
    
    def _extract_technical_docs(self, content: str, hint: str = None) -> ExtractedInfo:
        """提取技术文档信息"""
        system_prompt = """你是一个技术分析专家。请从技术文档中提取以下信息，返回 JSON 格式：
{
    "name": "技术/项目名称",
    "title": "技术类型（如：API、框架、工具）",
    "description": "技术简介（2-3句话）",
    "key_points": ["关键特性1", "关键特性2", "关键特性3"],
    "structured_data": {
        "技术概述": "...",
        "核心概念": "...",
        "使用方法": "...",
        "常见问题": "..."
    }
}"""
        
        prompt = f"分析以下技术文档：\n\n{content[:5000]}"
        result = self.llm.complete(prompt, system_prompt)
        
        try:
            data = json.loads(result)
        except:
            data = self._parse_json_fuzzy(result)
        
        return ExtractedInfo(
            document_type=DocumentType.TECHNICAL_DOCS,
            document_type_name="技术文档",
            name=data.get('name', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            key_points=data.get('key_points', []),
            structured_data=data.get('structured_data', {}),
            suggested_skill_type="technical_assistant",
            suggested_triggers=[data.get('name', ''), "怎么", "用法", "问题"],
            persona_info={
                "技术名称": data.get('name', ''),
                "技术简介": data.get('description', ''),
                "关键特性": "\n".join(data.get('key_points', [])),
                **data.get('structured_data', {})
            }
        )
    
    def _extract_chat_logs(self, content: str, hint: str = None) -> ExtractedInfo:
        """提取聊天记录信息"""
        system_prompt = """你是一个对话分析专家。请从聊天记录中提取以下信息，返回 JSON 格式：
{
    "name": "说话人名称",
    "title": "关系/身份",
    "description": "说话风格描述（2-3句话）",
    "key_points": ["常用语1", "常用语2", "常用语3"],
    "structured_data": {
        "说话风格": "...",
        "语气特点": "...",
        "常用表达": "...",
        "兴趣话题": "..."
    }
}"""
        
        prompt = f"分析以下聊天记录，提取说话人的风格：\n\n{content[:5000]}"
        result = self.llm.complete(prompt, system_prompt)
        
        try:
            data = json.loads(result)
        except:
            data = self._parse_json_fuzzy(result)
        
        return ExtractedInfo(
            document_type=DocumentType.CHAT_LOGS,
            document_type_name="聊天记录",
            name=data.get('name', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            key_points=data.get('key_points', []),
            structured_data=data.get('structured_data', {}),
            suggested_skill_type="chat_bot",
            suggested_triggers=["@" + data.get('name', ''), data.get('name', ''), "聊", "说"],
            persona_info={
                "说话人": data.get('name', ''),
                "说话风格": data.get('description', ''),
                "常用表达": "\n".join(data.get('key_points', [])),
                **data.get('structured_data', {})
            }
        )
    
    def _extract_faq(self, content: str, hint: str = None) -> ExtractedInfo:
        """提取 FAQ 信息"""
        system_prompt = """你是一个 FAQ 分析专家。请从 FAQ 文档中提取以下信息，返回 JSON 格式：
{
    "name": "主题/领域名称",
    "title": "文档类型",
    "description": "主题简介",
    "key_points": ["常见问题1", "常见问题2", "常见问题3"],
    "structured_data": {
        "概述": "...",
        "FAQ列表": [
            {"Q": "问题1", "A": "答案1"},
            {"Q": "问题2", "A": "答案2"}
        ]
    }
}"""
        
        prompt = f"分析以下 FAQ 文档：\n\n{content[:5000]}"
        result = self.llm.complete(prompt, system_prompt)
        
        try:
            data = json.loads(result)
        except:
            data = self._parse_json_fuzzy(result)
        
        return ExtractedInfo(
            document_type=DocumentType.FAQ,
            document_type_name="FAQ/问答",
            name=data.get('name', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            key_points=data.get('key_points', []),
            structured_data=data.get('structured_data', {}),
            suggested_skill_type="faq_assistant",
            suggested_triggers=["怎么", "如何", "问题", "帮助"],
            persona_info={
                "主题": data.get('name', ''),
                "简介": data.get('description', ''),
                "常见问题": "\n".join(data.get('key_points', [])),
                **data.get('structured_data', {})
            }
        )
    
    def _extract_general(self, content: str, hint: str = None) -> ExtractedInfo:
        """提取通用信息"""
        system_prompt = """你是一个信息提取专家。请从文档中提取以下信息，返回 JSON 格式：
{
    "name": "主题名称",
    "title": "类型/类别",
    "description": "内容简介（2-3句话）",
    "key_points": ["要点1", "要点2", "要点3"],
    "structured_data": {
        "概述": "...",
        "主要内容": "...",
        "关键信息": "..."
    }
}"""
        
        prompt = f"分析以下文档：\n\n{content[:5000]}"
        result = self.llm.complete(prompt, system_prompt)
        
        try:
            data = json.loads(result)
        except:
            data = self._parse_json_fuzzy(result)
        
        return ExtractedInfo(
            document_type=DocumentType.GENERAL_KNOWLEDGE,
            document_type_name="通用知识",
            name=data.get('name', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            key_points=data.get('key_points', []),
            structured_data=data.get('structured_data', {}),
            suggested_skill_type="knowledge_assistant",
            suggested_triggers=["什么是", "怎么", "为什么", data.get('name', '')],
            persona_info={
                "主题": data.get('name', ''),
                "简介": data.get('description', ''),
                "要点": "\n".join(data.get('key_points', [])),
                **data.get('structured_data', {})
            }
        )
    
    def _parse_json_fuzzy(self, text: str) -> dict:
        """模糊解析 JSON（处理 LLM 可能返回的 markdown code block）"""
        # 尝试提取 markdown code block
        if '```json' in text:
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
        elif '```' in text:
            match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
        
        try:
            return json.loads(text)
        except:
            # 返回空结构
            return {
                "name": "",
                "title": "",
                "description": "",
                "key_points": [],
                "structured_data": {}
            }


def extract_with_llm(content: str, hint: str = None, provider: str = "openai") -> ExtractedInfo:
    """
    便捷函数：使用 LLM 提取信息
    
    用法：
        info = extract_with_llm(文档内容, hint="这是产品手册")
        print(info.name)           # 提取的名称
        print(info.document_type)  # 文档类型
        print(info.persona_info)   # 结构化的 PERSONA_INFO
    """
    llm = LLMBackend(provider=provider)
    extractor = UniversalExtractor(llm_backend=llm)
    return extractor.extract(content, hint)
