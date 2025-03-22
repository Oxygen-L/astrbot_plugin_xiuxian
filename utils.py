import time
import random
from typing import Dict, Any, Tuple, Optional
from astrbot.api import logger

class XiuXianUtils:
    """
    修仙游戏工具类，提供各种通用功能
    """
    
    @staticmethod
    def parse_duration(duration: str) -> float:
        """
        解析持续时间字符串，支持多种格式：
        - "x小时y分钟"
        - "x小时"
        - "y分钟"
        - 纯数字（表示小时）
        
        Args:
            duration: 持续时间字符串
            
        Returns:
            持续时间（小时），可以是小数表示小时和分钟
        """
        # 默认1小时
        duration_hours = 1.0
        
        if duration:
            # 解析小时和分钟
            hours = 0
            minutes = 0
            
            # 检查是否包含小时
            if "小时" in duration:
                hour_parts = duration.split("小时")
                try:
                    hours = int(hour_parts[0].strip())
                except ValueError:
                    pass
                
                # 检查是否还有分钟部分
                if len(hour_parts) > 1 and "分钟" in hour_parts[1]:
                    try:
                        minutes = int(hour_parts[1].split("分钟")[0].strip())
                    except ValueError:
                        pass
            # 检查是否只有分钟
            elif "分钟" in duration:
                try:
                    minutes = int(duration.split("分钟")[0].strip())
                except ValueError:
                    pass
            # 尝试将整个字符串解析为小时数
            else:
                try:
                    hours = float(duration.strip())
                except ValueError:
                    pass
            
            # 计算总小时数（包括小数部分）
            duration_hours = hours + (minutes / 60.0)
        
        return duration_hours
    
    @staticmethod
    def format_time_remaining(seconds: int) -> str:
        """
        将剩余秒数格式化为可读的时间字符串
        
        Args:
            seconds: 剩余秒数
            
        Returns:
            格式化的时间字符串，如 "2小时30分钟15秒"
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟{secs}秒"
        elif minutes > 0:
            return f"{minutes}分钟{secs}秒"
        else:
            return f"{secs}秒"
    
    @staticmethod
    def calculate_reward(base_value: int, level: int, multiplier: float, 
                        level_factor: int = 2, random_range: Tuple[int, int] = (-5, 10),
                        critical_chance: float = 0.1, critical_multiplier: float = 3.0,
                        min_value: Optional[int] = None) -> Dict[str, Any]:
        """
        计算奖励值，适用于修为、灵石等各种奖励
        
        Args:
            base_value: 基础奖励值
            level: 用户等级
            multiplier: 奖励倍数（通常基于时间）
            level_factor: 等级影响因子
            random_range: 随机波动范围
            critical_chance: 暴击概率
            critical_multiplier: 暴击倍数
            min_value: 最小奖励值
            
        Returns:
            包含奖励信息的字典
        """
        # 计算基础值
        base = base_value * multiplier
        # 添加等级加成
        level_bonus = level * level_factor
        # 添加随机波动
        random_bonus = random.randint(random_range[0], random_range[1])
        
        # 计算总值
        total = int(base + level_bonus + random_bonus)
        
        # 小概率暴击
        is_critical = random.random() < critical_chance
        if is_critical:
            total = int(total * critical_multiplier)
        
        # 确保最低收益
        if min_value is not None:
            total = max(min_value, total)
        
        return {
            "value": total,
            "is_critical": is_critical
        }
    
    @staticmethod
    def generate_task_id(user_id: str, action_type: str = "") -> str:
        """
        生成唯一的任务ID
        
        Args:
            user_id: 用户ID
            action_type: 动作类型
            
        Returns:
            唯一的任务ID
        """
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        return f"{user_id}_{action_type}_{timestamp}_{random_suffix}"