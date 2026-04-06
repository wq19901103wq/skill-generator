#!/usr/bin/env python3
"""
聊天记录解析器 - 支持微信、飞书等格式
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class ChatParser:
    """聊天记录解析器"""
    
    # 不同平台的聊天记录格式
    FORMATS = {
        'wechat_txt': {
            'name': '微信文本导出',
            'patterns': [
                r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\S+)\s*$',  # 日期 昵称
                r'^(\d{2}:\d{2}:\d{2})\s+(\S+)\s*$',  # 时间 昵称
            ]
        },
        'wechat_csv': {
            'name': '微信CSV导出',
            'type': 'csv'
        },
        'lark': {
            'name': '飞书',
            'patterns': [
                r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s+(\S+)\s*',  # [日期时间] 昵称
            ]
        },
        'qq': {
            'name': 'QQ',
            'patterns': [
                r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\S+)\s*',  # 日期时间 昵称
            ]
        }
    }
    
    def __init__(self):
        self.messages = []  # [(timestamp, sender, content), ...]
        self.target_user = ""  # 目标用户（数字分身对应的人）
        
    def parse(self, text: str, format_type: str = 'auto') -> List[Tuple]:
        """
        解析聊天记录
        
        Args:
            text: 原始文本
            format_type: 格式类型 ('wechat_txt', 'wechat_csv', 'lark', 'qq', 'auto')
        
        Returns:
            [(timestamp, sender, content), ...]
        """
        if format_type == 'auto':
            format_type = self._detect_format(text)
        
        if format_type == 'wechat_csv':
            return self._parse_wechat_csv(text)
        else:
            return self._parse_text_format(text, format_type)
    
    def _detect_format(self, text: str) -> str:
        """自动检测格式"""
        # 检查 CSV 格式
        if text.startswith('"') and ',' in text.split('\n')[0]:
            return 'wechat_csv'
        
        # 检查飞书格式
        if '[20' in text and ']\n' in text[:1000]:
            return 'lark'
        
        # 默认微信文本格式
        return 'wechat_txt'
    
    def _parse_text_format(self, text: str, format_type: str) -> List[Tuple]:
        """解析文本格式"""
        messages = []
        lines = text.split('\n')
        
        current_time = ""
        current_sender = ""
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是新消息头
            is_header = False
            for pattern in self.FORMATS.get(format_type, {}).get('patterns', []):
                match = re.match(pattern, line)
                if match:
                    # 保存前一条消息
                    if current_sender and current_content:
                        messages.append((
                            current_time,
                            current_sender,
                            '\n'.join(current_content)
                        ))
                    
                    current_time = match.group(1)
                    current_sender = match.group(2)
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # 保存最后一条消息
        if current_sender and current_content:
            messages.append((
                current_time,
                current_sender,
                '\n'.join(current_content)
            ))
        
        self.messages = messages
        return messages
    
    def _parse_wechat_csv(self, text: str) -> List[Tuple]:
        """解析微信CSV格式"""
        import csv
        import io
        
        messages = []
        
        try:
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                # 微信CSV常见列名
                time_col = row.get('时间') or row.get('CreateTime') or row.get('StrTime')
                sender_col = row.get('昵称') or row.get('NickName') or row.get('StrNickName')
                content_col = row.get('内容') or row.get('StrContent') or row.get('Message')
                
                if sender_col and content_col:
                    messages.append((time_col, sender_col, content_col))
        except Exception as e:
            print(f"CSV解析错误: {e}")
        
        self.messages = messages
        return messages
    
    def identify_target_user(self, hint: str = None) -> str:
        """
        识别目标用户（数字分身的主人）
        
        Args:
            hint: 提示，如部分姓名
        
        Returns:
            目标用户昵称
        """
        if not self.messages:
            return ""
        
        # 统计发言频率
        sender_counts = defaultdict(int)
        sender_messages = defaultdict(list)
        
        for time, sender, content in self.messages:
            sender_counts[sender] += 1
            sender_messages[sender].append(content)
        
        # 如果有提示，优先匹配
        if hint:
            for sender in sender_counts:
                if hint in sender or sender in hint:
                    self.target_user = sender
                    return sender
        
        # 选择发言最多的作为目标（通常是自己导出的记录）
        if sender_counts:
            # 排除群助手、系统消息等
            filtered = {k: v for k, v in sender_counts.items() 
                       if not any(x in k for x in ['系统', '助手', '微信团队'])}
            
            if filtered:
                self.target_user = max(filtered, key=filtered.get)
            else:
                self.target_user = max(sender_counts, key=sender_counts.get)
        
        return self.target_user
    
    def extract_user_profile(self, target_user: str = None) -> Dict:
        """
        从聊天记录中提取用户画像
        
        Returns:
            {
                'common_phrases': [],  # 常用语
                'tone_particles': [],  # 语气词
                'avg_message_length': 0,  # 平均消息长度
                'active_hours': [],  # 活跃时间段
                'reply_style': '',  # 回复风格描述
            }
        """
        if target_user:
            self.target_user = target_user
        elif not self.target_user:
            self.identify_target_user()
        
        target = self.target_user
        user_messages = [content for time, sender, content in self.messages if sender == target]
        
        if not user_messages:
            return {}
        
        profile = {
            'target_user': target,
            'total_messages': len(user_messages),
        }
        
        # 合并所有消息文本
        all_text = '\n'.join(user_messages)
        
        # 分析语气词
        particles = ['呢', '呀', '啦', '哦', '吧', '哈', '哇', '啊', '嘛']
        particle_usage = {p: all_text.count(p) for p in particles}
        profile['tone_particles'] = [p for p, c in particle_usage.items() if c > len(user_messages) * 0.1]
        
        # 分析表情符号
        emojis = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', all_text)
        common_emojis = {}
        for e in emojis:
            common_emojis[e] = common_emojis.get(e, 0) + 1
        profile['common_emojis'] = sorted(common_emojis.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 分析常用短语（2-4字）
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', all_text)
        from collections import Counter
        word_counts = Counter(words)
        # 过滤常见词
        stop_words = {'好的', '可以', '收到', '了解', '知道', '明白', '谢谢', '没问题'}
        profile['common_phrases'] = [w for w, c in word_counts.most_common(10) 
                                      if w not in stop_words and c > 2][:5]
        
        # 平均消息长度
        avg_len = sum(len(m) for m in user_messages) / len(user_messages)
        profile['avg_message_length'] = round(avg_len, 1)
        
        # 活跃时间段
        hours = []
        for time, sender, content in self.messages:
            if sender == target and time:
                # 提取小时
                hour_match = re.search(r'(\d{2}):', str(time))
                if hour_match:
                    hours.append(int(hour_match.group(1)))
        
        if hours:
            from collections import Counter
            hour_counts = Counter(hours)
            profile['active_hours'] = [h for h, c in hour_counts.most_common(3)]
        
        # 回复风格描述
        style_parts = []
        if profile['tone_particles']:
            style_parts.append(f"常用语气词：{''.join(profile['tone_particles'])}")
        if avg_len < 15:
            style_parts.append("回复简洁")
        elif avg_len > 40:
            style_parts.append("回复详细")
        if '哈哈' in all_text or '😂' in all_text:
            style_parts.append("喜欢开玩笑")
        if '？' in all_text or '?' in all_text:
            q_rate = all_text.count('？') / len(user_messages)
            if q_rate > 0.2:
                style_parts.append("经常提问")
        
        profile['reply_style'] = '，'.join(style_parts) if style_parts else '说话自然'
        
        return profile
    
    def get_sample_replies(self, target_user: str = None, count: int = 10) -> List[str]:
        """
        获取用户的典型回复样本
        
        Returns:
            回复样本列表（用于学习说话风格）
        """
        if target_user:
            self.target_user = target_user
        elif not self.target_user:
            self.identify_target_user()
        
        target = self.target_user
        user_messages = [content for time, sender, content in self.messages if sender == target]
        
        # 过滤太短的，选择有代表性的
        filtered = [m for m in user_messages if 10 < len(m) < 100]
        
        # 去重并返回
        seen = set()
        samples = []
        for m in filtered:
            # 简化用于去重
            simplified = re.sub(r'[，。！？\s]', '', m)
            if simplified not in seen:
                seen.add(simplified)
                samples.append(m)
                if len(samples) >= count:
                    break
        
        return samples
    
    def generate_reply_templates(self, target_user: str = None) -> Dict[str, List[str]]:
        """
        生成回复模板
        
        Returns:
            {
                '打招呼': [...],
                '同意': [...],
                '拒绝': [...],
                '询问': [...],
            }
        """
        if target_user:
            self.target_user = target_user
        elif not self.target_user:
            self.identify_target_user()
        
        target = self.target_user
        user_messages = [content for time, sender, content in self.messages if sender == target]
        
        templates = {
            '打招呼': [],
            '同意': [],
            '拒绝': [],
            '询问': [],
            '其他': [],
        }
        
        for msg in user_messages:
            msg = msg.strip()
            if len(msg) < 5 or len(msg) > 50:
                continue
            
            # 分类
            if any(w in msg for w in ['你好', '在吗', '在？', 'hi', 'hello', '早', '晚上好']):
                templates['打招呼'].append(msg)
            elif any(w in msg for w in ['好的', '可以', '没问题', '行', '同意', '收到']):
                templates['同意'].append(msg)
            elif any(w in msg for w in ['不行', '不能', '抱歉', '不好意思', '不了']):
                templates['拒绝'].append(msg)
            elif '？' in msg or '?' in msg:
                templates['询问'].append(msg)
            else:
                templates['其他'].append(msg)
        
        # 每个类别取前 3 个
        for key in templates:
            templates[key] = templates[key][:3]
        
        return templates
