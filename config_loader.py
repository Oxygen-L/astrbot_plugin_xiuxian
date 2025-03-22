import os
import json
from typing import Dict, Any, List, Optional
from astrbot.api import logger

class ConfigLoader:
    """配置加载器，负责加载和管理所有游戏配置"""
    
    def __init__(self, config_dir: str):
        """初始化配置加载器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = config_dir
        
        # 配置文件路径
        self.realms_config_file = os.path.join(config_dir, "realms.json")
        self.breakthrough_rates_file = os.path.join(config_dir, "breakthrough_rates.json")
        self.game_values_file = os.path.join(config_dir, "game_values.json")
        self.shop_items_file = os.path.join(config_dir, "shop_items.json")
        self.health_limits_file = os.path.join(config_dir, "health_limits.json")
        self.combat_formulas_file = os.path.join(config_dir, "combat_formulas.json")
        self.adventure_events_file = os.path.join(config_dir, "adventure_events.json")
        self.mining_events_file = os.path.join(config_dir, "mining_events.json")
        self.user_template_file = os.path.join(config_dir, "user_template.json")
        
        # 加载所有配置
        self.realms = self._load_realms_config()
        self.breakthrough_rates = self._load_breakthrough_rates()
        self.game_values = self._load_game_values()
        self.shop_items = self._load_shop_items()
        self.health_limits = self._load_health_limits()
        self.combat_formulas = self._load_combat_formulas()
        self.adventure_events = self._load_adventure_events()
        self.mining_events = self._load_mining_events()
        self.user_template = self._load_user_template()
    
    def _load_json_file(self, file_path: str, default_value: Any = None) -> Any:
        """通用JSON文件加载方法
        
        Args:
            file_path: 文件路径
            default_value: 默认值，如果文件不存在或加载失败时返回
            
        Returns:
            加载的JSON数据或默认值，会自动递归过滤掉所有包含_comment的键
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 递归过滤掉所有包含_comment的键
                    filtered_data = self._filter_comments(data)
                    return filtered_data
            else:
                if default_value is not None:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(default_value, f, ensure_ascii=False, indent=4)
                    return default_value
                return {}
        except Exception as e:
            logger.error(f"加载配置文件 {file_path} 失败: {e}")
            return default_value if default_value is not None else {}
            
    def _filter_comments(self, data: Any) -> Any:
        """递归过滤JSON数据中所有包含_comment的键
        
        Args:
            data: 要过滤的数据
            
        Returns:
            过滤后的数据
        """
        if isinstance(data, dict):
            # 过滤掉所有包含_comment的键
            filtered_dict = {k: self._filter_comments(v) for k, v in data.items() if not k.startswith("_comment")}
            return filtered_dict
        elif isinstance(data, list):
            # 递归处理列表中的每个元素
            return [self._filter_comments(item) for item in data]
        else:
            # 基本类型直接返回
            return data
    
    def _load_realms_config(self) -> List[Dict[str, Any]]:
        """加载境界配置"""
        default_realms = {
            "realms": [
                {"name": "江湖好手", "level": 1, "exp_required": 1000}
            ]
        }
        config = self._load_json_file(self.realms_config_file, default_realms)
        return config.get("realms", [])
    
    def _load_breakthrough_rates(self) -> Dict[str, float]:
        """加载突破概率配置"""
        default_rates = {"江湖好手": 0.95}
        return self._load_json_file(self.breakthrough_rates_file, default_rates)
    
    def _load_game_values(self) -> Dict[str, Any]:
        """加载游戏基础数值配置"""
        default_values = {
            "practice": {
                "base_exp_per_hour": 10,
                "level_multiplier": 2,
                "random_bonus_range": [-5, 10],
                "critical_chance": 0.1,
                "critical_multiplier": 3,
                "max_duration_hours": 6
            },
            "adventure": {
                "cooldown_hours": [1, 2],
                "punishment_chance": 0.1,
                "exp_gain": {
                    "base": 5,
                    "random_range": [5, 10]
                },
                "spirit_stones_gain": {
                    "base": 5,
                    "level_multiplier": 2,
                    "random_range": [5, 15]
                },
                "technique_chance": 0.2,
                "max_duration_hours": 6
            },
            "mining": {
                "cooldown_hours": [1, 2],
                "punishment_chance": 0.1,
                "base_stones": 10,
                "level_multiplier": 2,
                "random_range": [-5, 10],
                "critical_chance": 0.1,
                "critical_multiplier": 3,
                "min_stones": 5,
                "max_duration_hours": 6
            },
            "daily_sign": {
                "base_stones": 50,
                "streak_bonus_per_day": 10,
                "max_streak_bonus": 100,
                "exp_multiplier": 5
            },
            "duel": {
                "cooldown_seconds": 600,
                "exp_range": [10, 30],
                "loser_exp_divisor": 2
            },
            "steal": {
                "cooldown_seconds": 600,
                "base_success_rate": 0.3,
                "level_bonus_rate": 0.4,
                "max_success_rate": 0.7,
                "steal_percent_range": [0.01, 0.2]
            },
            "breakthrough": {
                "cooldown_seconds": 3600,
                "exp_loss_percent_range": [0.01, 0.1],
                "bonus_increase_percent": 0.3,
                "max_success_rate": 0.95
            },
            "status": {
                "min_duration_hours": 0.1,
                "max_duration_hours": 6
            }
        }
        return self._load_json_file(self.game_values_file, default_values)
    
    def _load_shop_items(self) -> Dict[str, Any]:
        """加载商店物品配置"""
        default_items = {
            "techniques": {
                "吐纳术": {"level": 1, "cost": 100, "description": "基础呼吸法，提升修炼速度"}
            },
            "pills": {
                "渡厄丹": {"level": 5, "cost": 200, "description": "服用后可恢复少量修为，突破瓶颈", "effect": {"exp": 50}, "breakthrough_bonus": 0.1}
            },
            "equipment": {
                "weapon": [
                    {"id": "w1", "name": "木剑", "level": 1, "cost": 200, "attack": 5, "description": "普通的木制剑，适合初学者使用"}
                ],
                "armor": [
                    {"id": "a1", "name": "布衣", "level": 1, "cost": 200, "defense": 5, "description": "普通的布制衣服，提供基础防护"}
                ],
                "accessory": [
                    {"id": "ac1", "name": "木质护符", "level": 1, "cost": 200, "hp": 20, "description": "简单的护身符，略微增加生命值"}
                ]
            }
        }
        return self._load_json_file(self.shop_items_file, default_items)
    
    def _load_health_limits(self) -> Dict[str, int]:
        """加载生命值上限配置"""
        default_limits = {"江湖好手": 100}
        return self._load_json_file(self.health_limits_file, default_limits)
    
    def _load_combat_formulas(self) -> Dict[str, Any]:
        """加载战斗公式配置"""
        default_formulas = {
            "duel": {
                "power_calculation": {
                    "level_multiplier": 10,
                    "attack_weight": 1,
                    "defense_weight": 1
                },
                "win_chance": {
                    "base_chance": 0.5,
                    "power_diff_weight": 0.3,
                    "min_chance": 0.1,
                    "max_chance": 0.9
                }
            }
        }
        return self._load_json_file(self.combat_formulas_file, default_formulas)
    
    def _load_adventure_events(self) -> Dict[str, Any]:
        """加载秘境探索事件配置"""
        default_events = {
            "event_types": ["treasure", "herb", "monster", "opportunity"],
            "punishment": {
                "chance": 0.1,
                "events": ["遭遇强敌袭击", "踩入陷阱", "中了毒雾"],
                "spirit_stones_loss": {
                    "min_multiplier": 5,
                    "max_multiplier": 15
                },
                "exp_loss": {
                    "min_multiplier": 2,
                    "max_multiplier": 5
                }
            }
        }
        return self._load_json_file(self.adventure_events_file, default_events)
    
    def _load_mining_events(self) -> Dict[str, Any]:
        """加载挖矿事件配置"""
        default_events = {
            "punishment": {
                "chance": 0.1,
                "events": ["矿洞坍塌", "遭遇矿妖袭击"],
                "spirit_stones_loss": {
                    "min_multiplier": 3,
                    "max_multiplier": 10
                }
            },
            "success": {
                "base_stones": 10,
                "level_bonus_multiplier": 2,
                "random_range": [-5, 10],
                "min_stones": 5,
                "critical": {
                    "chance": 0.1,
                    "multiplier": 3
                }
            }
        }
        return self._load_json_file(self.mining_events_file, default_events)
    
    def _load_user_template(self) -> Dict[str, Any]:
        """加载用户模板配置"""
        default_template = {
            "level": 1,
            "exp": 0,
            "max_exp": 1000,
            "realm": "江湖好手",
            "spirit_stones": 100,
            "stats": {
                "attack": 10,
                "defense": 10,
                "hp": 100,
                "max_hp": 100
            }
        }
        return self._load_json_file(self.user_template_file, default_template)
    
    def get_realm_by_level(self, level: int) -> str:
        """根据等级获取对应的境界
        
        Args:
            level: 用户等级
            
        Returns:
            对应的境界名称
        """
        if not self.realms:
            return "江湖好手"
        
        for realm in self.realms:
            if realm["level"] == level:
                return realm["name"]
        
        return "江湖好手"
    
    def get_max_duration_hours(self, activity_type: str) -> float:
        """获取活动的最大持续时间
        
        Args:
            activity_type: 活动类型，如'practice'、'adventure'、'mining'
            
        Returns:
            最大持续时间（小时）
        """
        if activity_type in self.game_values and "max_duration_hours" in self.game_values[activity_type]:
            return self.game_values[activity_type]["max_duration_hours"]
        return self.game_values.get("status", {}).get("max_duration_hours", 6.0)
    
    def get_min_duration_hours(self, activity_type: str = None) -> float:
        """获取活动的最小持续时间
        
        Args:
            activity_type: 活动类型，如'practice'、'adventure'、'mining'，默认为None使用通用配置
            
        Returns:
            最小持续时间（小时）
        """
        if activity_type and activity_type in self.game_values and "min_duration_hours" in self.game_values[activity_type]:
            return self.game_values[activity_type]["min_duration_hours"]
        return self.game_values.get("status", {}).get("min_duration_hours", 0.1)