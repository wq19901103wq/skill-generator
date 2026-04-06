#!/usr/bin/env python3
"""
个人信息提取器 - 从文本中提取人物画像
支持规则提取和 LLM 辅助提取
"""

import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class PersonaInfo:
    """人物画像数据结构"""
    name: str = ""
    title: str = ""  # 职位/头衔
    company: str = ""  # 所在公司
    basic_intro: str = ""  # 基本介绍
    work_experience: str = ""  # 工作经验
    education: str = ""  # 教育背景
    skills: str = ""  # 技能
    personality: str = ""  # 性格特点
    interests: str = ""  # 兴趣爱好
    contact: str = ""  # 联系方式
    tone_style: str = ""  # 说话风格（从聊天记录分析）
    common_phrases: List[str] = None  # 常用语
    
    def __post_init__(self):
        if self.common_phrases is None:
            self.common_phrases = []
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典（用于模板渲染）"""
        return {
            'name': self.name,
            'title': self.title,
            'company': self.company,
            'basic_intro': self.basic_intro or f"我是{self.name}，{self.title}" if self.name else "",
            'work_experience': self.work_experience,
            'education': self.education,
            'skills': self.skills,
            'personality': self.personality,
            'interests': self.interests,
            'contact': self.contact,
            'tone_style': self.tone_style,
            'common_phrases': self.common_phrases,
        }
    
    def to_persona_info_dict(self) -> Dict[str, str]:
        """转换为 PERSONA_INFO 格式的字典"""
        result = {}
        
        if self.basic_intro or (self.name and self.title):
            result['基本介绍'] = self.basic_intro or f"我是{self.name}，{self.title}"
        
        if self.work_experience:
            result['工作经验'] = self.work_experience
        
        if self.education:
            result['教育背景'] = self.education
        
        if self.skills:
            result['技能'] = self.skills
        
        if self.personality:
            result['性格'] = self.personality
        
        if self.interests:
            result['兴趣爱好'] = self.interests
        
        if self.company:
            result['所在公司'] = self.company
        
        if self.title:
            result['职位'] = self.title
        
        if self.contact:
            result['联系方式'] = self.contact
        
        return result


class PersonaExtractor:
    """个人信息提取器"""
    
    # 中文姓名正则（常见姓氏 + 1-2 字名）
    NAME_PATTERNS = [
        r'姓名[：:]\s*([\u4e00-\u9fa5]{2,4})',
        r'名字[：:]\s*([\u4e00-\u9fa5]{2,4})',
        r'^[\u4e00-\u9fa5]{2,4}的简历',
        r'([\u4e00-\u9fa5]{2,4})\s*[个人简历|个人简介|的简介]',
    ]
    
    # 联系方式正则
    CONTACT_PATTERNS = {
        'email': r'[\w.-]+@[\w.-]+\.\w+',
        'phone': r'1[3-9]\d{9}',
        'wechat': r'微信[：:]\s*([\w.-]+)',
    }
    
    # 教育背景关键词
    EDUCATION_KEYWORDS = ['大学', '学院', '本科', '硕士', '博士', '研究生', '学士', '学位', '专业']
    
    # 工作相关关键词
    WORK_KEYWORDS = ['工作', '经验', '经历', '任职', '就职', '担任', '负责', '主导', '参与']
    
    # 技能关键词
    SKILL_KEYWORDS = ['技能', '熟练', '掌握', '精通', '熟悉', '会', '能力', '技术栈']
    
    def __init__(self):
        self.persona = PersonaInfo()
        self.raw_text = ""
        self.source_type = ""  # 'resume', 'chat', 'mixed'
        
    def extract(self, text: str, source_type: str = 'auto') -> PersonaInfo:
        """
        从文本中提取个人信息
        
        Args:
            text: 原始文本
            source_type: 来源类型 ('resume', 'chat', 'auto')
        
        Returns:
            PersonaInfo 对象
        """
        self.raw_text = text
        self.source_type = source_type
        
        # 自动检测类型
        if source_type == 'auto':
            self.source_type = self._detect_source_type(text)
        
        # 提取姓名
        self.persona.name = self._extract_name(text)
        
        # 提取联系方式
        self.persona.contact = self._extract_contact(text)
        
        # 提取教育背景
        self.persona.education = self._extract_education(text)
        
        # 提取工作经验
        self.persona.work_experience = self._extract_work_experience(text)
        
        # 提取技能
        self.persona.skills = self._extract_skills(text)
        
        # 提取公司和职位
        self.persona.company, self.persona.title = self._extract_company_and_title(text)
        
        # 提取性格特点
        self.persona.personality = self._extract_personality(text)
        
        # 如果是聊天记录，提取说话风格
        if self.source_type == 'chat':
            self.persona.tone_style, self.persona.common_phrases = self._extract_tone_from_chat(text)
        
        return self.persona
    
    def extract_from_multiple(self, texts: Dict[str, str]) -> PersonaInfo:
        """
        从多个文本源中提取并合并信息
        
        Args:
            texts: {文件名: 文本内容}
        """
        combined_persona = PersonaInfo()
        
        for filename, text in texts.items():
            # 根据文件名判断类型
            if 'chat' in filename.lower() or '聊天' in filename or '对话' in filename:
                source_type = 'chat'
            else:
                source_type = 'resume'
            
            persona = self.extract(text, source_type)
            
            # 合并信息（非空字段覆盖）
            for field in ['name', 'title', 'company', 'education', 'skills', 
                         'work_experience', 'personality', 'interests', 'contact']:
                value = getattr(persona, field)
                if value:
                    setattr(combined_persona, field, value)
            
            # 合并常用语
            combined_persona.common_phrases.extend(persona.common_phrases)
        
        # 去重常用语
        combined_persona.common_phrases = list(set(combined_persona.common_phrases))[:10]
        
        self.persona = combined_persona
        return combined_persona
    
    def _detect_source_type(self, text: str) -> str:
        """检测文本来源类型"""
        # 聊天记录特征：时间戳、昵称、大量短句
        chat_indicators = [
            r'\d{2}:\d{2}',  # 时间戳
            r'\[.+?\]',  # [昵称]
            r'【.+?】',
            r'撤回了一条消息',
            r'已添加',
        ]
        
        chat_score = sum(1 for p in chat_indicators if re.search(p, text))
        
        if chat_score >= 2:
            return 'chat'
        
        # 简历特征
        resume_keywords = ['简历', '个人简介', '教育背景', '工作经历', '项目经验', '技能']
        resume_score = sum(1 for kw in resume_keywords if kw in text)
        
        if resume_score >= 2:
            return 'resume'
        
        return 'resume'  # 默认按简历处理
    
    def _extract_name(self, text: str) -> str:
        """提取姓名"""
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # 尝试从文件开头找
        lines = text.split('\n')[:10]  # 前10行
        for line in lines:
            line = line.strip()
            # 匹配独立的中文姓名（2-4字，常见姓氏开头）
            if re.match(r'^[\u4e00-\u9fa5]{2,4}$', line):
                return line
        
        return ""
    
    def _extract_contact(self, text: str) -> str:
        """提取联系方式"""
        contacts = []
        
        # 邮箱
        emails = re.findall(self.CONTACT_PATTERNS['email'], text)
        if emails:
            contacts.append(f"邮箱: {emails[0]}")
        
        # 手机
        phones = re.findall(self.CONTACT_PATTERNS['phone'], text)
        if phones:
            contacts.append(f"手机: {phones[0]}")
        
        # 微信
        wechat_match = re.search(self.CONTACT_PATTERNS['wechat'], text)
        if wechat_match:
            contacts.append(f"微信: {wechat_match.group(1)}")
        
        return '，'.join(contacts) if contacts else ""
    
    def _extract_education(self, text: str) -> str:
        """提取教育背景"""
        # 找包含教育关键词的句子
        sentences = re.split(r'[。\n]', text)
        education_sentences = []
        
        for sent in sentences:
            sent = sent.strip()
            if any(kw in sent for kw in self.EDUCATION_KEYWORDS):
                # 过滤掉太短的
                if len(sent) > 10:
                    education_sentences.append(sent)
        
        if education_sentences:
            # 返回最长的（通常信息最全）
            return max(education_sentences, key=len)
        
        return ""
    
    def _extract_work_experience(self, text: str) -> str:
        """提取工作经验"""
        # 找工作经历部分
        work_section = self._extract_section(text, 
            ['工作经历', '工作经验', '工作履历', '职业经历', '任职经历'],
            ['教育背景', '项目经验', '技能', '自我评价', '个人优势']
        )
        
        if work_section:
            # 取前 200 字作为摘要
            summary = work_section[:200].replace('\n', ' ')
            return summary + "..." if len(work_section) > 200 else summary
        
        # 如果没有明确分区，找包含工作关键词的句子
        sentences = re.split(r'[。\n]', text)
        work_sentences = [s for s in sentences if any(kw in s for kw in ['年经验', '工作', '负责', '担任'])]
        
        if work_sentences:
            return '。'.join(work_sentences[:2])
        
        return ""
    
    def _extract_skills(self, text: str) -> str:
        """提取技能"""
        # 找技能部分
        skill_section = self._extract_section(text,
            ['技能', '专业技能', '技术栈', '能力'],
            ['工作经历', '教育背景', '项目经验', '自我评价']
        )
        
        if skill_section:
            # 清理并返回
            skills = skill_section.replace('\n', ' ').strip()
            # 限制长度
            if len(skills) > 150:
                skills = skills[:150] + "..."
            return skills
        
        return ""
    
    def _extract_company_and_title(self, text: str) -> tuple:
        """提取公司和职位"""
        company = ""
        title = ""
        
        # 职位模式
        title_patterns = [
            r'(产品经理|工程师|总监|经理|设计师|运营|开发|测试|架构师|负责人|主管|副总裁|CEO|CTO|COO)',
            r'担任[\s\w]*?(.{2,10}?)(?:，|。|\n)',
            r'职位[：:]\s*(.+?)(?:\n|，|。)',
            r'现任(.{2,20}?)(?:的|，|。)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                break
        
        # 公司模式
        company_patterns = [
            r'(?:就职于|任职于|加入|在|来自)[\s]*(.{2,20}?)(?:担任|任|做|，|。)',
            r'(.{2,20}?)(?:公司|集团|科技|网络|信息)(?:担任|，|。)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip()
                if '公司' not in company and '集团' not in company:
                    company = company + "公司"
                break
        
        return company, title
    
    def _extract_personality(self, text: str) -> str:
        """提取性格特点"""
        # 找自我评价部分
        eval_section = self._extract_section(text,
            ['自我评价', '个人评价', '性格', '特点', '优势'],
            ['工作经历', '教育背景', '技能']
        )
        
        if eval_section:
            sentences = re.split(r'[。\n]', eval_section)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 10 and len(sent) < 100:
                    return sent
        
        return ""
    
    def _extract_tone_from_chat(self, text: str) -> tuple:
        """从聊天记录中提取说话风格"""
        # 提取说话者的消息
        messages = self._extract_messages(text)
        
        if not messages:
            return "", []
        
        # 分析常用语
        phrases = []
        
        # 找常见语气词
        particles = ['呢', '呀', '啦', '哦', '吧', '哈', '～', '哈哈', '嘿嘿']
        particle_counts = {p: text.count(p) for p in particles}
        common_particles = [p for p, c in particle_counts.items() if c > 5]
        
        # 找常用短语（2-4字）
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        from collections import Counter
        word_counts = Counter(words)
        common_words = [w for w, c in word_counts.most_common(5) if c > 2 and len(w) >= 2]
        
        phrases = common_particles + common_words
        
        # 描述说话风格
        style_parts = []
        if '～' in text or len([p for p in ['呢', '呀', '啦'] if p in text]) > 5:
            style_parts.append("语气比较柔和")
        if '哈哈' in text or '嘿嘿' in text:
            style_parts.append("喜欢用表情")
        if len(messages) > 0:
            avg_len = sum(len(m) for m in messages) / len(messages)
            if avg_len < 20:
                style_parts.append("回复简洁")
            elif avg_len > 50:
                style_parts.append("回复详细")
        
        tone_style = "，".join(style_parts) if style_parts else "说话比较自然"
        
        return tone_style, phrases[:5]
    
    def _extract_messages(self, text: str) -> List[str]:
        """从聊天记录中提取消息内容"""
        messages = []
        
        # 常见聊天记录格式
        # 格式1: [昵称] 内容
        # 格式2: 昵称: 内容
        # 格式3: 时间 昵称: 内容
        
        patterns = [
            r'\[.+?\]\s*(.+?)(?=\[|$)',
            r'^.+?[：:]\s*(.+?)$',
        ]
        
        for line in text.split('\n'):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    msg = match.group(1).strip()
                    if len(msg) > 5:  # 过滤太短的
                        messages.append(msg)
                    break
        
        return messages
    
    def _extract_section(self, text: str, start_keywords: List[str], end_keywords: List[str]) -> str:
        """提取文本中的特定章节"""
        # 构建开始和结束模式
        start_pattern = '|'.join(start_keywords)
        
        # 找开始位置
        start_match = re.search(rf'(?:{start_pattern})[：:\s\n]*', text)
        if not start_match:
            return ""
        
        start_pos = start_match.end()
        
        # 找结束位置（下一个章节或文本结束）
        end_pattern = '|'.join(end_keywords)
        end_match = re.search(rf'(?:{end_pattern})[：:\s\n]', text[start_pos:])
        
        if end_match:
            end_pos = start_pos + end_match.start()
            return text[start_pos:end_pos].strip()
        else:
            # 取到段落结束（下一个空行或一定长度）
            remaining = text[start_pos:]
            # 找下一个空行
            blank_match = re.search(r'\n\s*\n', remaining)
            if blank_match:
                return remaining[:blank_match.start()].strip()
            else:
                # 限制长度
                return remaining[:500].strip()


def extract_persona_from_text(text: str, source_type: str = 'auto') -> Dict[str, str]:
    """
    便捷函数：从文本中提取个人信息
    
    Returns:
        PERSONA_INFO 格式的字典
    """
    extractor = PersonaExtractor()
    persona = extractor.extract(text, source_type)
    return persona.to_persona_info_dict()


def extract_persona_from_files(file_contents: Dict[str, str]) -> Dict[str, str]:
    """
    便捷函数：从多个文件内容中提取并合并个人信息
    
    Args:
        file_contents: {文件名: 文件内容}
    
    Returns:
        PERSONA_INFO 格式的字典
    """
    extractor = PersonaExtractor()
    persona = extractor.extract_from_multiple(file_contents)
    return persona.to_persona_info_dict()
