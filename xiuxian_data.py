import os
import json
import random
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from astrbot.api import logger
from .config_loader import ConfigLoader
from .utils import XiuXianUtils

# 修仙游戏数据管理类
class XiuXianData:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.user_data_file = os.path.join(data_dir, "user_data.json")
        self.users = self._load_data()
        
        # 初始化配置加载器
        config_dir = os.path.join(data_dir, "configs")
        os.makedirs(config_dir, exist_ok=True)
        self.config = ConfigLoader(config_dir)
        
        # 从配置加载器获取配置
        self.realms_config = self.config.realms
        self.breakthrough_rates = self.config.breakthrough_rates
    
    def _load_data(self) -> Dict[str, Any]:
        """加载用户数据"""
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载用户数据失败: {e}")
                return {}
        return {}
    
    def _save_data(self) -> None:
        """保存用户数据"""
        try:
            os.makedirs(os.path.dirname(self.user_data_file), exist_ok=True)
            with open(self.user_data_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存用户数据失败: {e}")
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """获取用户数据，如果不存在则创建"""
        if user_id not in self.users:
            # 从配置加载器获取用户模板并创建新用户数据
            self.users[user_id] = self.config.user_template.copy()
            # 确保必要的嵌套字典和列表存在
            if "equipment" not in self.users[user_id]:
                self.users[user_id]["equipment"] = {"weapon": None, "armor": None, "accessory": None}
            if "stats" not in self.users[user_id]:
                self.users[user_id]["stats"] = {"attack": 10, "defense": 10, "hp": 100, "max_hp": 100}
            if "inventory" not in self.users[user_id]:
                self.users[user_id]["inventory"] = {"pills": {}}
            if "items" not in self.users[user_id]:
                self.users[user_id]["items"] = []
            if "techniques" not in self.users[user_id]:
                self.users[user_id]["techniques"] = []
            # 确保其他必要字段存在
            self.users[user_id].setdefault("username", "")
            self.users[user_id].setdefault("last_practice_time", 0)
            self.users[user_id].setdefault("last_adventure_time", 0)
            self.users[user_id].setdefault("last_mine_time", 0)
            self.users[user_id].setdefault("last_daily_time", 0)
            self.users[user_id].setdefault("status", None)
            self.users[user_id].setdefault("status_end_time", 0)
            self.users[user_id].setdefault("status_start_time", 0)
            self.users[user_id].setdefault("status_duration", 0)
            self.users[user_id].setdefault("status_reward_multiplier", 0)
            self.users[user_id].setdefault("last_steal_time", 0)
            self.users[user_id].setdefault("last_duel_time", 0)
            self.users[user_id].setdefault("last_breakthrough_time", 0)
            self.users[user_id].setdefault("breakthrough_bonus", 0)
            self.users[user_id].setdefault("has_started", False)
            self.users[user_id].setdefault("daily_streak", 0)
            self._save_data()
        return self.users[user_id]
    
    def update_user(self, user_id: str, data: Dict[str, Any]) -> None:
        """更新用户数据"""
        if user_id in self.users:
            self.users[user_id].update(data)
            self._save_data()
    
    def add_exp(self, user_id: str, exp: int) -> Dict[str, Any]:
        """增加用户修为，但不自动升级，只有通过突破才能升级境界"""
        user = self.get_user(user_id)
        user["exp"] += exp
        
        # 不再自动升级，只返回修为增加信息
        level_up_info = {"leveled_up": False, "old_level": user["level"], "old_realm": user["realm"]}
        
        self._save_data()
        return level_up_info
    
    def _load_realms_config(self) -> List[Dict[str, Any]]:
        """加载境界配置"""
        try:
            os.makedirs(os.path.dirname(self.realms_config_file), exist_ok=True)
            if os.path.exists(self.realms_config_file):
                with open(self.realms_config_file, "r", encoding="utf-8") as f:
                    return json.load(f)["realms"]
            else:
                # 默认境界配置
                default_realms = {
                    "realms": [
                        {"name": "江湖好手", "level": 56, "exp_required": 1000}
                    ]
                }
                with open(self.realms_config_file, "w", encoding="utf-8") as f:
                    json.dump(default_realms, f, ensure_ascii=False, indent=4)
                return default_realms["realms"]
        except Exception as e:
            print(f"加载境界配置失败: {e}")
            return []
    
    def _load_breakthrough_rates(self) -> Dict[str, float]:
        """加载突破概率配置"""
        try:
            os.makedirs(os.path.dirname(self.breakthrough_rates_file), exist_ok=True)
            if os.path.exists(self.breakthrough_rates_file):
                with open(self.breakthrough_rates_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # 默认突破概率配置
                default_rates = {"江湖好手": 0.95}
                with open(self.breakthrough_rates_file, "w", encoding="utf-8") as f:
                    json.dump(default_rates, f, ensure_ascii=False, indent=4)
                return default_rates
        except Exception as e:
            print(f"加载突破概率配置失败: {e}")
            return {}
    
    def _get_realm_by_level(self, level: int) -> str:
        """根据等级获取对应的境界"""
        return self.config.get_realm_by_level(level)
    
    def add_spirit_stones(self, user_id: str, amount: int) -> int:
        """增加或减少灵石"""
        user = self.get_user(user_id)
        user["spirit_stones"] += amount
        self._save_data()
        return user["spirit_stones"]
    
    def get_next_realm(self, user_id: str) -> Dict[str, Any]:
        """获取用户下一境界信息"""
        user = self.get_user(user_id)
        current_realm = user["realm"]
        
        # 查找当前境界在配置中的位置
        current_index = -1
        for i, realm in enumerate(self.realms_config):
            if realm["name"] == current_realm:
                current_index = i
                break
        
        # 如果找不到当前境界或已是最高境界，返回None
        if current_index == -1 or current_index == 55:  # 注意：最高境界的索引是55（因为按等级值从低到高排序）
            return {
                "has_next": False,
                "message": "你已达到最高境界，无法继续突破。"
            }
        
        # 获取当前境界和下一境界信息
        current_realm_info = self.realms_config[current_index]
        next_realm = self.realms_config[current_index + 1]
        
        # 计算所需修为（使用当前境界的修为要求）
        exp_required = current_realm_info["exp_required"]
        current_exp = user["exp"]
        
        # 检查修为是否足够
        can_breakthrough = current_exp >= exp_required
        
        # 检查CD时间
        current_time = int(time.time())
        cd_remaining = 0
        breakthrough_cooldown = self.config.game_values.get("breakthrough", {}).get("cooldown_seconds", 3600)  # 默认1小时CD
        if current_time - user.get("last_breakthrough_time", 0) < breakthrough_cooldown:
            cd_remaining = breakthrough_cooldown - (current_time - user.get("last_breakthrough_time", 0))
        
        return {
            "has_next": True,
            "next_realm": next_realm["name"],
            "exp_required": exp_required,
            "current_exp": current_exp,
            "can_breakthrough": can_breakthrough,
            "cd_remaining": cd_remaining,
            "breakthrough_rate": self.breakthrough_rates.get(current_realm, 0.5)  # 默认0.5
        }
    
    def breakthrough(self, user_id: str, use_pill: bool = False) -> Dict[str, Any]:
        """尝试突破到下一境界"""
        user = self.get_user(user_id)
        next_realm_info = self.get_next_realm(user_id)
        
        # 检查是否有下一境界
        if not next_realm_info["has_next"]:
            return {
                "success": False,
                "message": next_realm_info["message"]
            }
        
        # 检查CD时间
        if next_realm_info["cd_remaining"] > 0:
            minutes = next_realm_info["cd_remaining"] // 60
            seconds = next_realm_info["cd_remaining"] % 60
            return {
                "success": False,
                "message": f"突破冷却中，需等待 {minutes}分{seconds}秒"
            }
        
        # 检查修为是否足够
        if not next_realm_info["can_breakthrough"]:
            return {
                "success": False,
                "message": f"修为不足，无法突破。当前修为：{next_realm_info['current_exp']}，需要：{next_realm_info['exp_required']}"
            }
        
        # 从配置中获取突破相关参数
        breakthrough_config = self.config.game_values.get("breakthrough", {})
        max_success_rate = breakthrough_config.get("max_success_rate", 0.95)
        exp_loss_percent_range = breakthrough_config.get("exp_loss_percent_range", [0.01, 0.1])
        bonus_increase_percent = breakthrough_config.get("bonus_increase_percent", 0.3)
        
        # 计算突破概率
        base_rate = next_realm_info["breakthrough_rate"]
        # 加上突破加成（如果有）
        bonus_rate = user.get("breakthrough_bonus", 0)
        final_rate = min(max_success_rate, base_rate + bonus_rate)  # 最高成功率由配置决定
        
        # 决定是否突破成功
        is_success = random.random() < final_rate
        
        # 更新最后突破时间
        user["last_breakthrough_time"] = int(time.time())
        
        result = {
            "success": True,
            "is_breakthrough_success": is_success,
            "old_realm": user["realm"],
            "new_realm": next_realm_info["next_realm"] if is_success else user["realm"],
            "exp_loss": 0,
            "message": ""
        }
        
        if is_success:
            # 突破成功，更新境界
            old_realm = user["realm"]
            user["realm"] = next_realm_info["next_realm"]
            # 消耗修为（消耗当前境界所需的修为）
            user["exp"] -= next_realm_info["exp_required"]
            # 重置突破加成
            user["breakthrough_bonus"] = 0
            
            # 更新最大生命值
            self.update_max_hp(user_id)
            
            result["message"] = f"恭喜突破成功！你的境界提升为【{user['realm']}】"
        else:
            # 突破失败
            if not use_pill:  # 如果没有使用渡厄丹
                # 随机扣减修为，范围由配置决定
                exp_loss_percent = random.uniform(exp_loss_percent_range[0], exp_loss_percent_range[1])
                exp_loss = int(user["exp"] * exp_loss_percent)
                user["exp"] = max(0, user["exp"] - exp_loss)
                
                # 增加下次突破成功率，增加比例由配置决定
                bonus_increase = base_rate * bonus_increase_percent
                user["breakthrough_bonus"] += bonus_increase
                
                result["exp_loss"] = exp_loss
                result["message"] = f"突破失败！损失了 {exp_loss} 点修为，但下次突破成功率提高了 {bonus_increase*100:.1f}%"
            else:
                # 使用了渡厄丹，不损失修为
                # 增加下次突破成功率，增加比例由配置决定
                bonus_increase = base_rate * bonus_increase_percent
                user["breakthrough_bonus"] += bonus_increase
                
                result["message"] = f"虽然突破失败，但由于使用了渡厄丹，没有损失修为。下次突破成功率提高了 {bonus_increase*100:.1f}%"
        
        # 更新用户数据
        self.update_user(user_id, user)
        
        return result
    
    def get_all_users(self) -> Dict[str, Any]:
        """获取所有用户数据"""
        return self.users
    
    def update_max_hp(self, user_id: str) -> None:
        """根据用户境界更新最大生命值"""
        user = self.get_user(user_id)
        realm = user["realm"]
        
        # 从配置中获取该境界对应的最大生命值
        max_hp = self.config.health_limits.get(realm, 100)  # 默认100
        
        # 更新用户最大生命值
        old_max_hp = user["stats"]["max_hp"]
        user["stats"]["max_hp"] = max_hp
        
        # 如果最大生命值增加，当前生命值也相应增加
        if max_hp > old_max_hp:
            hp_increase = max_hp - old_max_hp
            user["stats"]["hp"] += hp_increase
        
        # 确保当前生命值不超过最大生命值
        user["stats"]["hp"] = min(user["stats"]["hp"], user["stats"]["max_hp"])
        
        # 更新用户数据
        self.update_user(user_id, user)
    
    def duel(self, user_id: str, target_id: str) -> Dict[str, Any]:
        """切磋功能"""
        user = self.get_user(user_id)
        target = self.get_user(target_id)
        
        # 从配置中获取战斗公式参数
        duel_config = self.config.combat_formulas.get("duel", {})
        power_calc = duel_config.get("power_calculation", {})
        win_chance_config = duel_config.get("win_chance", {})
        
        # 获取战力计算参数
        level_multiplier = power_calc.get("level_multiplier", 10)
        attack_weight = power_calc.get("attack_weight", 1)
        defense_weight = power_calc.get("defense_weight", 1)
        
        # 计算战力（基于等级、装备和功法）
        user_power = user["level"] * level_multiplier + user["stats"]["attack"] * attack_weight + user["stats"]["defense"] * defense_weight
        target_power = target["level"] * level_multiplier + target["stats"]["attack"] * attack_weight + target["stats"]["defense"] * defense_weight
        
        # 获取胜率计算参数
        base_chance = win_chance_config.get("base_chance", 0.5)
        power_diff_weight = win_chance_config.get("power_diff_weight", 0.3)
        min_chance = win_chance_config.get("min_chance", 0.1)
        max_chance = win_chance_config.get("max_chance", 0.9)
        
        # 计算胜率（战力差距影响）
        power_diff = abs(user_power - target_power)
        win_chance = base_chance + (user_power - target_power) / max(user_power, target_power) * power_diff_weight
        win_chance = max(min_chance, min(max_chance, win_chance))  # 限制在配置的范围内
        
        # 决定胜负
        is_winner = random.random() < win_chance
        
        # 从配置中获取修为奖励范围
        duel_exp_config = self.config.game_values.get("duel", {})
        exp_range = duel_exp_config.get("exp_range", [10, 30])
        loser_exp_divisor = duel_exp_config.get("loser_exp_divisor", 2)
        
        # 计算奖惩
        exp_change = random.randint(exp_range[0], exp_range[1]) * max(user["level"], target["level"])
        
        result = {
            "success": True,
            "user_power": user_power,
            "target_power": target_power,
            "message": ""
        }
        
        if is_winner:
            # 胜者获得修为，败者损失修为
            self.add_exp(user_id, exp_change)
            target["exp"] = max(0, target["exp"] - exp_change // 2)
            result["message"] = f"切磋胜利！获得修为 {exp_change} 点！"
        else:
            # 败者损失修为，胜者获得修为
            user["exp"] = max(0, user["exp"] - exp_change // 2)
            self.add_exp(target_id, exp_change)
            result["message"] = f"切磋失败！损失修为 {exp_change // 2} 点！"
        
        self._save_data()
        return result
    
    def steal_spirit_stones(self, user_id: str, target_id: str) -> Dict[str, Any]:
        """偷取灵石功能"""
        user = self.get_user(user_id)
        target = self.get_user(target_id)
        current_time = int(time.time())
        
        # 检查CD（600秒）
        if current_time - user.get("last_steal_time", 0) < 600:
            remaining = 600 - (current_time - user.get("last_steal_time", 0))
            return {
                "success": False,
                "message": f"你的偷窃技能还在冷却中，需要等待 {remaining} 秒"
            }
        
        # 计算成功率（与修为等级相关）
        success_rate = 0.3 + user["level"] / 100 * 0.4  # 30%-70%之间
        success_rate = min(0.7, success_rate)  # 限制最高70%
        
        # 决定是否成功
        is_success = random.random() < success_rate
        
        result = {
            "success": True,
            "message": ""
        }
        
        if is_success:
            # 计算可偷取的灵石数量（1%-20%，且不超过目标拥有量）
            steal_percent = random.uniform(0.01, 0.2)
            steal_amount = int(target["spirit_stones"] * steal_percent)
            steal_amount = min(steal_amount, target["spirit_stones"])
            
            # 转移灵石
            user["spirit_stones"] += steal_amount
            target["spirit_stones"] -= steal_amount
            
            result["message"] = f"偷取成功！获得灵石 {steal_amount} 枚！"
        else:
            # 失败惩罚（损失100万灵石或全部灵石）
            penalty = min(1000000, user["spirit_stones"])
            user["spirit_stones"] -= penalty
            
            result["message"] = f"偷取失败！被发现并受到惩罚，损失灵石 {penalty} 枚！"
        
        # 更新最后偷窃时间
        user["last_steal_time"] = current_time
        
        self._save_data()
        return result
    
    # ===== 秘境探索相关 =====
    def adventure(self, user_id: str) -> Dict[str, Any]:
        """进行秘境探索，获取奖励"""
        user = self.get_user(user_id)
        current_time = int(time.time())
        
        # 从配置中获取秘境探索相关参数
        adventure_config = self.config.game_values.get("adventure", {})
        cooldown_hours = adventure_config.get("cooldown_hours", [1, 2])  # 默认1-2小时冷却
        
        # 随机冷却时间
        cooldown = 60 * 60 * random.randint(cooldown_hours[0], cooldown_hours[1])
        
        # 检查冷却时间
        if current_time - user["last_adventure_time"] < cooldown:
            remaining = cooldown - (current_time - user['last_adventure_time'])
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return {
                "success": False,
                "message": f"秘境入口尚未开启，需等待 {hours}小时{minutes}分钟"
            }
        
        # 根据用户等级确定探索难度和奖励
        level = user["level"]
        
        # 从配置中获取事件配置
        adventure_events = self.config.adventure_events
        
        # 获取事件类型列表
        event_types = adventure_events.get("event_types", ["treasure", "herb", "monster", "opportunity"])
        event_type = random.choice(event_types)
        
        result = {
            "success": True,
            "event_type": event_type,
            "rewards": [],
            "exp_gain": 0,
            "spirit_stones_gain": 0,
            "message": ""
        }
        
        # 获取惩罚事件配置
        punishment_config = adventure_events.get("punishment", {})
        punishment_chance = punishment_config.get("chance", 0.1)  # 默认10%概率触发惩罚
        punishment_events = punishment_config.get("events", ["遭遇强敌袭击", "踩入陷阱", "中了毒雾"])
        
        # 获取惩罚损失范围
        spirit_stones_loss_range = punishment_config.get("spirit_stones_loss", {})
        min_stones_multiplier = spirit_stones_loss_range.get("min_multiplier", 5)
        max_stones_multiplier = spirit_stones_loss_range.get("max_multiplier", 15)
        
        exp_loss_range = punishment_config.get("exp_loss", {})
        min_exp_multiplier = exp_loss_range.get("min_multiplier", 2)
        max_exp_multiplier = exp_loss_range.get("max_multiplier", 5)
        
        # 随机决定是否触发惩罚事件
        is_punishment = random.random() < punishment_chance
        
        # 如果触发惩罚事件
        if is_punishment:
            punishment = random.choice(punishment_events)
            
            # 损失灵石
            lost_stones = min(user["spirit_stones"], random.randint(level * min_stones_multiplier, level * max_stones_multiplier))
            user["spirit_stones"] -= lost_stones
            
            # 可能损失一些修为
            exp_loss = random.randint(level * min_exp_multiplier, level * max_exp_multiplier)
            user["exp"] = max(0, user["exp"] - exp_loss)
            
            result["message"] = f"你在秘境中{punishment}，损失了 {lost_stones} 灵石和 {exp_loss} 点修为！"
            result["success"] = True
            result["is_punishment"] = True
            
            # 更新最后探险时间
            user["last_adventure_time"] = current_time
            self.update_user(user_id, user)
            
            return result
            
        # 根据事件类型生成结果
        if event_type == "treasure":
            # 获取宝物配置
            treasure_config = adventure_events.get("treasure", {})
            spirit_stones_gain = treasure_config.get("spirit_stones_gain", {})
            min_multiplier = spirit_stones_gain.get("min_multiplier", 10)
            max_multiplier = spirit_stones_gain.get("max_multiplier", 30)
            treasure_messages = treasure_config.get("messages", ["你在秘境中发现了一处宝藏，获得了 {spirit_stones} 灵石！"])
            
            # 发现宝物
            spirit_stones = random.randint(level * min_multiplier, level * max_multiplier)
            result["spirit_stones_gain"] = spirit_stones
            user["spirit_stones"] += spirit_stones
            result["message"] = random.choice(treasure_messages).format(spirit_stones=spirit_stones)
            
        elif event_type == "herb":
            # 获取草药配置
            herb_config = adventure_events.get("herb", {})
            herbs = herb_config.get("items", ["灵草", "灵芝", "仙参", "龙血草", "九转还魂草"])
            herb_messages = herb_config.get("messages", ["你在秘境中发现了珍贵的 {herb}！"])
            
            # 发现灵草
            herb = random.choice(herbs)
            user["items"].append(herb)
            result["rewards"].append(herb)
            result["message"] = random.choice(herb_messages).format(herb=herb)
            
        elif event_type == "monster":
            # 获取怪物配置
            monster_config = adventure_events.get("monster", {})
            monster_names = monster_config.get("names", ["山猪", "赤焰狐", "黑风狼", "幽冥蛇", "雷霆鹰"])
            win_messages = monster_config.get("win_messages", ["你在秘境中遇到了 {monster}，经过一番激战，你成功击败了它！\n获得了 {exp_gain} 点修为和 {spirit_stones} 灵石！"])
            lose_messages = monster_config.get("lose_messages", ["你在秘境中遇到了 {monster}，不敌其强大的实力，被迫撤退...\n下次再来挑战吧！"])
            
            # 简单战斗逻辑
            monster_level = random.randint(max(1, level - 5), level + 5)
            win_chance = 0.5 + (level - monster_level) * 0.1  # 等级差影响胜率
            win_chance = max(0.1, min(0.9, win_chance))  # 胜率限制在10%~90%
            
            if random.random() < win_chance:
                # 战斗胜利
                exp_gain = monster_level * random.randint(5, 10)
                spirit_stones = monster_level * random.randint(5, 15)
                
                result["exp_gain"] = exp_gain
                result["spirit_stones_gain"] = spirit_stones
                
                self.add_exp(user_id, exp_gain)
                user = self.get_user(user_id)  # 重新获取用户数据，因为可能升级
                user["spirit_stones"] += spirit_stones
                
                result["message"] = random.choice(win_messages).format(monster=monster, exp_gain=exp_gain, spirit_stones=spirit_stones)
            else:
                # 战斗失败
                result["message"] = random.choice(lose_messages).format(monster=monster)
        
        elif event_type == "opportunity":
            # 获取机缘配置
            opportunity_config = adventure_events.get("opportunity", {})
            opportunities = opportunity_config.get("events", [
                "发现了一处修炼宝地",
                "偶遇前辈指点",
                "得到一篇功法残卷",
                "悟道树下顿悟",
                "天降灵雨洗礼"
            ])
            
            # 获取修为增益配置
            exp_gain_config = opportunity_config.get("exp_gain", {})
            min_multiplier = exp_gain_config.get("min_multiplier", 10)
            max_multiplier = exp_gain_config.get("max_multiplier", 20)
            
            # 获取功法概率和消息配置
            technique_chance = opportunity_config.get("technique_chance", 0.2)
            messages = opportunity_config.get("messages", ["你在秘境中{opportunity}，顿时感悟颇深！\n获得了 {exp_gain} 点修为！"])
            technique_messages = opportunity_config.get("technique_messages", ["你在秘境中{opportunity}，顿时感悟颇深！\n获得了 {exp_gain} 点修为，并习得了 {technique}！"])
            
            opportunity = random.choice(opportunities)
            
            exp_gain = level * random.randint(min_multiplier, max_multiplier)
            result["exp_gain"] = exp_gain
            self.add_exp(user_id, exp_gain)
            
            # 有小概率获得功法
            if random.random() < technique_chance:
                techniques = ["吐纳术", "御风术", "小周天功", "金刚不坏", "五行遁法", "太极剑法"]
                available_techniques = [t for t in techniques if t not in user["techniques"]]
                
                if available_techniques:
                    new_technique = random.choice(available_techniques)
                    user["techniques"].append(new_technique)
                    result["rewards"].append(new_technique)
                    result["message"] = random.choice(technique_messages).format(opportunity=opportunity, exp_gain=exp_gain, technique=new_technique)
                else:
                    result["message"] = random.choice(messages).format(opportunity=opportunity, exp_gain=exp_gain)
            else:
                result["message"] = random.choice(messages).format(opportunity=opportunity, exp_gain=exp_gain)
        
        # 更新最后探险时间
        user["last_adventure_time"] = current_time
        self.update_user(user_id, user)
        
        return result
    
    # ===== 功法相关 =====
    def learn_technique(self, user_id: str, technique_name: str) -> Dict[str, Any]:
        """学习功法"""
        user = self.get_user(user_id)
        
        # 检查是否已学习该功法
        if technique_name in user["techniques"]:
            return {
                "success": False,
                "message": f"你已经学会了 {technique_name}，不需要重复学习。"
            }
        
        # 从配置中获取功法列表
        techniques = self.config.shop_items.get("techniques", {})
        
        # 检查功法是否存在
        if technique_name not in techniques:
            return {
                "success": False,
                "message": f"没有找到名为 {technique_name} 的功法。"
            }
        
        technique = techniques[technique_name]
        
        # 检查等级要求
        if user["level"] < technique["level"]:
            return {
                "success": False,
                "message": f"你的修为不足，需要达到 {technique['level']} 级才能学习 {technique_name}。"
            }
        
        # 检查灵石是否足够
        if user["spirit_stones"] < technique["cost"]:
            return {
                "success": False,
                "message": f"灵石不足，学习 {technique_name} 需要 {technique['cost']} 灵石。"
            }
        
        # 扣除灵石并学习功法
        user["spirit_stones"] -= technique["cost"]
        user["techniques"].append(technique_name)
        self.update_user(user_id, user)
        
        return {
            "success": True,
            "message": f"恭喜你成功学习了 {technique_name}！"
        }
    
    def get_available_techniques(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户可学习的功法列表"""
        user = self.get_user(user_id)
        
        # 从配置中获取功法列表
        all_techniques = self.config.shop_items.get("techniques", {})
        
        result = []
        for name, info in all_techniques.items():
            # 检查是否已学习
            learned = name in user["techniques"]
            # 检查等级是否满足
            level_met = user["level"] >= info["level"]
            # 检查灵石是否足够
            stones_enough = user["spirit_stones"] >= info["cost"]
            
            technique_info = {
                "name": name,
                "level_required": info["level"],
                "cost": info["cost"],
                "description": info["description"],
                "learned": learned,
                "can_learn": level_met and stones_enough and not learned
            }
            
            result.append(technique_info)
        
        return result
    
    # ===== 丹药系统 =====
    def get_available_pills(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户可购买的丹药列表"""
        user = self.get_user(user_id)
        
        # 从配置中获取丹药列表
        all_pills = self.config.shop_items.get("pills", {})
        
        result = []
        for name, info in all_pills.items():
            # 检查等级是否满足
            level_met = user["level"] >= info["level"]
            # 检查灵石是否足够
            stones_enough = user["spirit_stones"] >= info["cost"]
            # 检查已拥有数量
            owned = user["inventory"]["pills"].get(name, 0)
            
            pill_info = {
                "name": name,
                "level_required": info["level"],
                "cost": info["cost"],
                "description": info["description"],
                "owned": owned,
                "can_buy": level_met and stones_enough
            }
            
            result.append(pill_info)
        
        return result
    
    def buy_pill(self, user_id: str, pill_name: str) -> Dict[str, Any]:
        """购买丹药"""
        user = self.get_user(user_id)
        
        # 从配置中获取丹药列表
        all_pills = self.config.shop_items.get("pills", {})
        
        # 检查丹药是否存在
        if pill_name not in all_pills:
            return {
                "success": False,
                "message": f"没有找到名为 {pill_name} 的丹药。"
            }
        
        pill = all_pills[pill_name]
        
        # 检查等级要求
        if user["level"] < pill["level"]:
            return {
                "success": False,
                "message": f"你的修为不足，需要达到 {pill['level']} 级才能购买 {pill_name}。"
            }
        
        # 检查灵石是否足够
        if user["spirit_stones"] < pill["cost"]:
            return {
                "success": False,
                "message": f"灵石不足，购买 {pill_name} 需要 {pill['cost']} 灵石。"
            }
        
        # 扣除灵石并添加丹药到物品栏
        user["spirit_stones"] -= pill["cost"]
        
        # 确保物品栏中有丹药分类
        if "pills" not in user["inventory"]:
            user["inventory"]["pills"] = {}
        
        # 添加丹药到物品栏
        if pill_name not in user["inventory"]["pills"]:
            user["inventory"]["pills"][pill_name] = 0
        user["inventory"]["pills"][pill_name] += 1
        
        self.update_user(user_id, user)
        
        return {
            "success": True,
            "message": f"成功购买了 {pill_name}！"
        }
    
    def use_pill(self, user_id: str, pill_name: str) -> Dict[str, Any]:
        """使用丹药"""
        user = self.get_user(user_id)
        
        # 从配置中获取丹药列表
        all_pills = self.config.shop_items.get("pills", {})
        
        # 检查丹药是否存在
        if pill_name not in all_pills:
            return {
                "success": False,
                "message": f"没有找到名为 {pill_name} 的丹药。"
            }
        
        # 检查用户是否拥有该丹药
        if "pills" not in user["inventory"] or pill_name not in user["inventory"]["pills"] or user["inventory"]["pills"][pill_name] <= 0:
            return {
                "success": False,
                "message": f"你没有 {pill_name}，请先购买。"
            }
        
        # 获取丹药信息
        pill = all_pills[pill_name]
        
        # 从库存中移除丹药
        user["inventory"]["pills"][pill_name] -= 1
        
        # 应用丹药效果
        exp_gain = pill["effect"]["exp"]
        message = f"你服用了 {pill_name}，获得了 {exp_gain} 点修为。"
        
        # 如果丹药有突破加成，应用到用户身上
        if "breakthrough_bonus" in pill:
            user["breakthrough_bonus"] = pill["breakthrough_bonus"]
            message += f"\n丹药效果：下次突破成功率提升 {int(pill['breakthrough_bonus'] * 100)}%。"
        
        # 增加修为并检查是否升级
        level_up_info = self.add_exp(user_id, exp_gain)
        
        # 更新用户数据
        self.update_user(user_id, user)
        
        # 如果升级了，添加升级信息
        if level_up_info["leveled_up"]:
            message += f"\n恭喜！你的修为提升到了 {user['level']} 级，境界晋升为 {user['realm']}！"
        
        return {
            "success": True,
            "message": message
        }
    
    # ===== 挖矿相关 =====
    def mine_spirit_stones(self, user_id: str) -> Dict[str, Any]:
        """挖矿获取灵石"""
        user = self.get_user(user_id)
        current_time = int(time.time())
        
        # 从配置中获取挖矿相关参数
        mining_config = self.config.game_values.get("mining", {})
        cooldown_hours = mining_config.get("cooldown_hours", [1, 2])  # 默认1-2小时冷却
        
        # 从配置中获取挖矿事件配置
        mining_events = self.config.mining_events
        
        # 获取惩罚事件配置
        punishment_config = mining_events.get("punishment", {})
        punishment_chance = punishment_config.get("chance", 0.1)  # 默认10%惩罚概率
        punishment_events = punishment_config.get("events", ["矿洞坍塌", "遭遇矿妖袭击"])
        punishment_loss_range = punishment_config.get("spirit_stones_loss", {})
        min_loss_multiplier = punishment_loss_range.get("min_multiplier", 3)
        max_loss_multiplier = punishment_loss_range.get("max_multiplier", 10)
        
        # 获取成功事件配置
        success_config = mining_events.get("success", {})
        base_stones = success_config.get("base_stones", 10)  # 默认基础灵石
        level_multiplier = success_config.get("level_bonus_multiplier", 2)  # 默认等级倍率
        random_range = success_config.get("random_range", [-5, 10])  # 默认随机范围
        min_stones = success_config.get("min_stones", 5)  # 默认最小灵石
        
        # 获取暴击配置
        critical_config = success_config.get("critical", {})
        critical_chance = critical_config.get("chance", 0.1)  # 默认暴击率
        critical_multiplier = critical_config.get("multiplier", 3)  # 默认暴击倍率
        
        # 获取消息配置
        success_messages = success_config.get("messages", ["你辛勤地挖掘矿石，获得了 {stones} 灵石。"])
        critical_messages = success_config.get("critical_messages", ["运气爆棚！你在矿洞中发现了一条灵石矿脉，获得了 {stones} 灵石！"])
        
        # 随机冷却时间
        cooldown = 60 * 60 * random.randint(cooldown_hours[0], cooldown_hours[1])
        
        # 检查冷却时间
        if current_time - user["last_mine_time"] < cooldown:
            remaining = cooldown - (current_time - user['last_mine_time'])
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return {
                "success": False,
                "message": f"矿洞尚未刷新，需等待 {hours}小时{minutes}分钟"
            }
        
        # 随机决定是否触发惩罚事件
        is_punishment = random.random() < punishment_chance
        
        if is_punishment:
            punishment = random.choice(punishment_events)
            
            # 损失灵石
            lost_stones = min(user["spirit_stones"], random.randint(user["level"] * min_loss_multiplier, user["level"] * max_loss_multiplier))
            user["spirit_stones"] -= lost_stones
            
            # 更新用户数据
            user["last_mine_time"] = current_time
            self.update_user(user_id, user)
            
            return {
                "success": True,
                "is_punishment": True,
                "spirit_stones_loss": lost_stones,
                "message": f"不幸遭遇{punishment}，损失了 {lost_stones} 灵石！"
            }
        
        # 根据等级确定基础挖矿收益
        level_bonus = user["level"] * level_multiplier
        
        # 随机波动
        stones = base_stones + level_bonus + random.randint(random_range[0], random_range[1])
        stones = max(min_stones, stones)  # 至少获得最小灵石数
        
        # 小概率暴击
        critical = random.random() < critical_chance
        if critical:
            stones = stones * critical_multiplier
            message = random.choice(critical_messages).format(stones=stones)
        else:
            message = random.choice(success_messages).format(stones=stones)
        
        # 更新用户数据
        user["spirit_stones"] += stones
        user["last_mine_time"] = current_time
        self.update_user(user_id, user)
        
        return {
            "success": True,
            "spirit_stones_gain": stones,
            "message": message
        }
    
    # ===== 每日签到 =====
    def daily_sign(self, user_id: str) -> Dict[str, Any]:
        """每日签到获取奖励"""
        user = self.get_user(user_id)
        current_time = int(time.time())
        
        # 获取今天的日期（0点为界限）
        today = datetime.fromtimestamp(current_time).replace(hour=0, minute=0, second=0, microsecond=0)
        today_timestamp = int(today.timestamp())
        
        # 检查是否已经签到
        if user["last_daily_time"] >= today_timestamp:
            return {
                "success": False,
                "message": "你今天已经签到过了，请明天再来！"
            }
        
        # 计算连续签到天数
        yesterday = today - timedelta(days=1)
        yesterday_timestamp = int(yesterday.timestamp())
        
        if user["last_daily_time"] >= yesterday_timestamp:
            # 连续签到
            if "daily_streak" not in user:
                user["daily_streak"] = 1
            else:
                user["daily_streak"] += 1
        else:
            # 断签，重置连续签到
            user["daily_streak"] = 1
        
        # 从配置中获取每日签到奖励参数
        daily_sign_config = self.config.game_values.get("daily_sign", {})
        base_stones = daily_sign_config.get("base_stones", 50)
        streak_bonus_per_day = daily_sign_config.get("streak_bonus_per_day", 10)
        max_streak_bonus = daily_sign_config.get("max_streak_bonus", 100)
        exp_multiplier = daily_sign_config.get("exp_multiplier", 5)
        
        # 根据连续签到天数给予奖励
        streak = user["daily_streak"]
        streak_bonus = min(streak * streak_bonus_per_day, max_streak_bonus)  # 最多额外奖励由配置决定
        
        stones = base_stones + streak_bonus
        exp = user["level"] * exp_multiplier  # 修为奖励与等级相关，倍率由配置决定
        
        # 更新用户数据
        user["spirit_stones"] += stones
        user["last_daily_time"] = current_time
        self.update_user(user_id, user)
        self.add_exp(user_id, exp)
        
        return {
            "success": True,
            "streak": streak,
            "spirit_stones_gain": stones,
            "exp_gain": exp,
            "message": f"签到成功！这是你连续签到的第 {streak} 天。\n获得 {stones} 灵石和 {exp} 点修为！"
        }
    
    # ===== 装备系统 =====
    def get_equipment_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有可用装备列表"""
        # 从配置中获取装备列表
        return self.config.shop_items.get("equipment", {})
    
    def get_user_equipment(self, user_id: str) -> Dict[str, Any]:
        """获取用户当前装备信息"""
        user = self.get_user(user_id)
        return user["equipment"]
    
    def buy_equipment(self, user_id: str, equipment_type: str, equipment_id: str) -> Dict[str, Any]:
        """购买装备"""
        user = self.get_user(user_id)
        all_equipment = self.get_equipment_list()
        
        # 检查装备类型是否有效
        if equipment_type not in all_equipment:
            return {
                "success": False,
                "message": f"无效的装备类型：{equipment_type}"
            }
        
        # 查找指定ID的装备
        equipment = None
        for item in all_equipment[equipment_type]:
            if item["id"] == equipment_id:
                equipment = item
                break
        
        if not equipment:
            return {
                "success": False,
                "message": f"找不到ID为 {equipment_id} 的装备"
            }
        
        # 检查等级要求
        if user["level"] < equipment["level"]:
            return {
                "success": False,
                "message": f"你的修为不足，需要达到 {equipment['level']} 级才能使用 {equipment['name']}"
            }
        
        # 检查灵石是否足够
        if user["spirit_stones"] < equipment["cost"]:
            return {
                "success": False,
                "message": f"灵石不足，购买 {equipment['name']} 需要 {equipment['cost']} 灵石"
            }
        
        # 扣除灵石并装备
        user["spirit_stones"] -= equipment["cost"]
        
        # 更新装备和属性
        old_equipment = user["equipment"][equipment_type]
        user["equipment"][equipment_type] = equipment["id"]
        
        # 更新用户属性
        if equipment_type == "weapon":
            # 移除旧武器属性
            if old_equipment:
                for old_item in all_equipment["weapon"]:
                    if old_item["id"] == old_equipment:
                        user["stats"]["attack"] -= old_item["attack"]
                        break
            # 添加新武器属性
            user["stats"]["attack"] += equipment["attack"]
        
        elif equipment_type == "armor":
            # 移除旧护甲属性
            if old_equipment:
                for old_item in all_equipment["armor"]:
                    if old_item["id"] == old_equipment:
                        user["stats"]["defense"] -= old_item["defense"]
                        break
            # 添加新护甲属性
            user["stats"]["defense"] += equipment["defense"]
        
        elif equipment_type == "accessory":
            # 移除旧饰品属性
            if old_equipment:
                for old_item in all_equipment["accessory"]:
                    if old_item["id"] == old_equipment:
                        user["stats"]["max_hp"] -= old_item["hp"]
                        user["stats"]["hp"] = min(user["stats"]["hp"], user["stats"]["max_hp"])
                        break
            # 添加新饰品属性
            user["stats"]["max_hp"] += equipment["hp"]
            user["stats"]["hp"] += equipment["hp"]  # 装备新饰品时恢复对应的生命值
        
        self.update_user(user_id, user)
        
        return {
            "success": True,
            "message": f"成功购买并装备了 {equipment['name']}！"
        }
    
    def get_available_equipment(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """获取用户可购买的装备列表"""
        user = self.get_user(user_id)
        all_equipment = self.get_equipment_list()
        result = {}
        
        for equip_type, items in all_equipment.items():
            result[equip_type] = []
            for item in items:
                # 检查等级是否满足
                level_met = user["level"] >= item["level"]
                # 检查灵石是否足够
                stones_enough = user["spirit_stones"] >= item["cost"]
                # 检查是否已装备
                equipped = user["equipment"][equip_type] == item["id"]
                
                item_info = item.copy()
                item_info["level_met"] = level_met
                item_info["stones_enough"] = stones_enough
                item_info["equipped"] = equipped
                item_info["can_buy"] = level_met and stones_enough
                
                result[equip_type].append(item_info)
        
        return result
    
    # ===== 状态系统相关 =====
    def set_status(self, user_id: str, status_type: str, duration_hours: float = 0) -> Dict[str, Any]:
        """设置用户状态
        
        Args:
            user_id: 用户ID
            status_type: 状态类型，可选值：'修炼中'、'探索中'、'收集灵石中'
            duration_hours: 持续时间（小时），可以是小数表示小时和分钟。
                           对于修炼状态，如果为0则表示无限时长，由用户自行决定结束时间
            
        Returns:
            包含状态信息的字典
        """
        user = self.get_user(user_id)
        current_time = int(time.time())
        
        # 检查是否已有状态
        if user["status"] is not None and current_time < user["status_end_time"]:
            remaining = user["status_end_time"] - current_time
            # 使用工具类格式化剩余时间
            time_str = XiuXianUtils.format_time_remaining(remaining)
            return {
                "success": False,
                "message": f"你当前正处于{user['status']}状态，还需 {time_str} 结束"
            }
        
        # 根据状态类型获取对应的活动类型配置
        activity_type = "practice" if status_type == "修炼中" else "adventure" if status_type == "探索中" else "mining" if status_type == "收集灵石中" else "status"
        
        # 从配置中获取最小和最大持续时间限制
        # 优先使用活动类型自己的min_duration_hours配置
        if activity_type in self.config.game_values and "min_duration_hours" in self.config.game_values[activity_type]:
            min_duration = self.config.game_values[activity_type]["min_duration_hours"]
        else:
            min_duration = self.config.get_min_duration_hours()
        
        max_duration = self.config.get_max_duration_hours(activity_type)
        
        # 对于修炼状态，如果duration_hours为0，则设置为最大时长，表示无限时长
        if status_type == "修炼中" and duration_hours == 0:
            duration_hours = max_duration
            duration_seconds = int(duration_hours * 3600)
            end_time_message = "无限时长，请使用 /结束修炼 命令手动结束"
        else:
            # 限制持续时间在配置的范围内
            duration_hours = max(min_duration, min(max_duration, duration_hours))
            duration_seconds = int(duration_hours * 3600)
            end_time_message = f"将持续 {duration_hours} 小时"
        
        # 计算奖励倍数（时间越长，奖励越多）
        # 对于修炼状态，初始设置为0，在结束时根据实际时长计算
        reward_multiplier = 0 if status_type == "修炼中" else duration_hours
        
        # 设置状态
        user["status"] = status_type
        user["status_start_time"] = current_time
        user["status_end_time"] = current_time + duration_seconds
        user["status_duration"] = duration_hours
        user["status_reward_multiplier"] = reward_multiplier
        
        self.update_user(user_id, user)
        
        logger.info(f"用户 ({user_id}) 进入了 {status_type} 状态，开始时间：{current_time}，结束时间：{user['status_end_time']}")
        
        return {
            "success": True,
            "status": status_type,
            "duration": duration_hours,
            "end_time": user["status_end_time"],
            "message": f"你已进入{status_type}状态，{end_time_message}"
        }
    
    def check_status(self, user_id: str) -> Dict[str, Any]:
        """检查用户当前状态"""
        user = self.get_user(user_id)
        current_time = int(time.time())
        
        # 如果没有状态
        if user["status"] is None:
            return {
                "has_status": False,
                "message": "你当前没有进行中的状态"
            }
            
        # 如果状态已结束，自动完成状态并返回无状态
        if current_time >= user["status_end_time"]:
            # 记录日志但不处理奖励，让complete_status处理
            logger.info(f"用户 ({user_id}) 的{user['status']}状态已结束，等待领取奖励")
            return {
                "has_status": False,
                "status_completed": True,
                "message": f"你的{user['status']}已经结束，可以领取奖励了"
            }
        
        # 计算剩余时间
        remaining = user["status_end_time"] - current_time
        
        # 使用工具类格式化剩余时间
        time_str = XiuXianUtils.format_time_remaining(remaining)
        
        return {
            "has_status": True,
            "status": user["status"],
            "remaining": remaining,
            "message": f"你当前正处于{user['status']}状态，还需 {time_str} 结束" if user["status"]!="修炼中" else f"你当前正处于{user['status']}状态"
        }
    
    def complete_status(self, user_id: str) -> Dict[str, Any]:
        """完成状态并获取奖励"""
        user = self.get_user(user_id)
        current_time = int(time.time())
        
        # 如果没有状态
        if user["status"] is None:
            return {
                "success": False,
                "message": "你当前没有进行中的状态"
            }
        
        # 如果是修炼状态，允许随时结束并获得奖励
        if user["status"] == "修炼中":
            # 计算实际修炼时长（小时）
            actual_duration = (current_time - user["status_start_time"]) / 3600
            # 确保至少有一定的修炼时间（至少5分钟）
            if actual_duration < 5/60:
                # 更新修炼状态
                user["status"] = None
                user["status_start_time"] = None
                user["status_end_time"] = None
                user["status_duration"] = None
                user["status_reward_multiplier"] = None
                self.update_user(user_id, user)
                return {
                    "success": False,
                    "message": "修炼时间太短，无法获得有效修为，请至少修炼5分钟"
                }
            # 更新奖励倍数
            user["status_reward_multiplier"] = actual_duration
            # 更新实际修炼时长
            user["status_duration"] = actual_duration
            self.update_user(user_id, user)
        # 对于其他状态，如果未结束则不能完成
        elif current_time < user["status_end_time"]:
            logger.info(f"current_time: {current_time}, user['status_end_time']: {user['status_end_time']}")
            remaining = user["status_end_time"] - current_time
            # 使用工具类格式化剩余时间
            time_str = XiuXianUtils.format_time_remaining(remaining)
            return {
                "success": False,
                "message": f"你的{user['status']}尚未完成，还需 {time_str}"
            }
        
        status_type = user["status"]
        multiplier = user["status_reward_multiplier"]
        result = {
            "success": True,
            "status_type": status_type,
            "rewards": []
        }
        
        # 根据不同状态类型给予不同奖励
        if status_type == "修炼中":
            # 从配置中获取修炼相关参数
            practice_config = self.config.game_values.get("practice", {})
            base_exp_per_hour = practice_config.get("base_exp_per_hour", 10)
            # 根据修炼时长计算实际经验
            actual_exp = int(base_exp_per_hour * user["status_duration"])
            level_multiplier = practice_config.get("level_multiplier", 2)
            random_bonus_range = practice_config.get("random_bonus_range", [-5, 10])
            critical_chance = practice_config.get("critical_chance", 0.1)
            critical_multiplier = practice_config.get("critical_multiplier", 3)
            
            # 使用工具类计算奖励
            reward_result = XiuXianUtils.calculate_reward(
                base_value=actual_exp,
                level=user["level"],
                multiplier=multiplier,
                level_factor=level_multiplier,
                random_range=random_bonus_range,
                critical_chance=critical_chance,
                critical_multiplier=critical_multiplier,
                min_value=5
            )
            
            exp_gain = reward_result["value"]
            is_critical = reward_result["is_critical"]
            if is_critical:
                result["is_critical"] = True
            
            level_up_info = self.add_exp(user_id, exp_gain)
            user = self.get_user(user_id)  # 重新获取更新后的数据
            
            result["exp_gain"] = exp_gain
            result["leveled_up"] = level_up_info["leveled_up"]
            
            if level_up_info["leveled_up"]:
                result["message"] = f"闭关修炼结束，获得 {exp_gain} 点修为！\n境界提升：{level_up_info['old_realm']} → {user['realm']}\n等级提升：{level_up_info['old_level']} → {user['level']}"
            else:
                if is_critical:
                    result["message"] = f"闭关修炼结束，顿悟成功！获得 {exp_gain} 点修为！"
                else:
                    result["message"] = f"闭关修炼结束，获得 {exp_gain} 点修为！"
        
        elif status_type == "探索中":
            # 从配置中获取秘境探索相关参数
            adventure_config = self.config.game_values.get("adventure", {})
            adventure_events = self.config.adventure_events
            
            # 获取事件类型列表
            event_types = adventure_events.get("event_types", ["treasure", "herb", "monster", "opportunity"])
            
            # 获取惩罚事件配置
            punishment_config = adventure_events.get("punishment", {})
            punishment_chance = punishment_config.get("chance", 0.1)  # 默认10%概率触发惩罚
            punishment_events = punishment_config.get("events", ["遭遇强敌袭击", "踩入陷阱", "中了毒雾"])
            
            # 获取惩罚损失范围
            spirit_stones_loss_range = punishment_config.get("spirit_stones_loss", {})
            min_stones_multiplier = spirit_stones_loss_range.get("min_multiplier", 5)
            max_stones_multiplier = spirit_stones_loss_range.get("max_multiplier", 15)
            
            exp_loss_range = punishment_config.get("exp_loss", {})
            min_exp_multiplier = exp_loss_range.get("min_multiplier", 2)
            max_exp_multiplier = exp_loss_range.get("max_multiplier", 5)
            
            # 随机决定是否触发惩罚事件
            is_punishment = random.random() < punishment_chance
            
            if is_punishment:
                punishment = random.choice(punishment_events)
                
                # 损失灵石
                lost_stones = min(user["spirit_stones"], random.randint(user["level"] * min_stones_multiplier, user["level"] * max_stones_multiplier))
                user["spirit_stones"] -= lost_stones
                
                # 可能损失一些修为
                exp_loss = random.randint(user["level"] * min_exp_multiplier, user["level"] * max_exp_multiplier)
                user["exp"] = max(0, user["exp"] - exp_loss)
                
                result["is_punishment"] = True
                result["spirit_stones_loss"] = lost_stones
                result["exp_loss"] = exp_loss
                result["message"] = f"长时间的秘境探索中{punishment}，损失了 {lost_stones} 灵石和 {exp_loss} 点修为！"
            else:
                # 随机事件类型
                event_type = random.choice(event_types)
                
                if event_type == "treasure":
                    # 获取宝物配置
                    treasure_config = adventure_events.get("treasure", {})
                    spirit_stones_gain = treasure_config.get("spirit_stones_gain", {})
                    min_multiplier = spirit_stones_gain.get("min_multiplier", 10)
                    max_multiplier = spirit_stones_gain.get("max_multiplier", 30)
                    treasure_messages = treasure_config.get("messages", ["你在秘境中发现了一处宝藏，获得了 {spirit_stones} 灵石！"])
                    
                    # 发现宝物
                    spirit_stones = int(random.randint(user["level"] * min_multiplier, user["level"] * max_multiplier) * multiplier)
                    user["spirit_stones"] += spirit_stones
                    result["spirit_stones_gain"] = spirit_stones
                    result["message"] = random.choice(treasure_messages).format(spirit_stones=spirit_stones)
                
                elif event_type == "herb":
                    # 获取草药配置
                    herb_config = adventure_events.get("herb", {})
                    herbs = herb_config.get("items", ["灵草", "灵芝", "仙参", "龙血草", "九转还魂草"])
                    herb_messages = herb_config.get("messages", ["你在秘境中发现了珍贵的 {herb}！"])
                    
                    # 发现灵草
                    herb_count = min(5, multiplier + random.randint(0, 2))
                    found_herbs = random.sample(herbs, min(herb_count, len(herbs)))
                    
                    for herb in found_herbs:
                        user["items"].append(herb)
                    
                    result["rewards"] = found_herbs
                    result["message"] = f"长时间的秘境探索中发现了珍贵的草药：{', '.join(found_herbs)}！"
                
                elif event_type == "monster":
                    # 获取怪物配置
                    monster_config = adventure_events.get("monster", {})
                    monster_names = monster_config.get("names", ["山猪", "赤焰狐", "黑风狼", "幽冥蛇", "雷霆鹰"])
                    
                    # 获取战斗配置
                    combat_config = self.config.combat_formulas.get("adventure", {})
                    monster_level_config = combat_config.get("monster_level", {})
                    min_level_diff = monster_level_config.get("min_level_diff", -5)
                    max_level_diff = monster_level_config.get("max_level_diff", 5)
                    
                    win_chance_config = combat_config.get("win_chance", {})
                    base_chance = win_chance_config.get("base_chance", 0.5)
                    level_diff_multiplier = win_chance_config.get("level_diff_multiplier", 0.1)
                    min_chance = win_chance_config.get("min_chance", 0.1)
                    max_chance = win_chance_config.get("max_chance", 0.9)
                    
                    # 获取奖励配置
                    exp_gain_config = adventure_config.get("exp_gain", {})
                    exp_base = exp_gain_config.get("base", 5)
                    exp_random_range = exp_gain_config.get("random_range", [5, 10])
                    
                    spirit_stones_gain_config = adventure_config.get("spirit_stones_gain", {})
                    stones_base = spirit_stones_gain_config.get("base", 5)
                    stones_level_multiplier = spirit_stones_gain_config.get("level_multiplier", 2)
                    stones_random_range = spirit_stones_gain_config.get("random_range", [5, 15])
                    
                    # 遇到妖兽
                    monster = random.choice(monster_names)
                    
                    # 简单战斗逻辑
                    monster_level = random.randint(max(1, user["level"] + min_level_diff), user["level"] + max_level_diff)
                    win_chance = base_chance + (user["level"] - monster_level) * level_diff_multiplier
                    win_chance = max(min_chance, min(max_chance, win_chance))  # 胜率限制
                    
                    if random.random() < win_chance:
                        # 战斗胜利
                        exp_gain = int(monster_level * random.randint(exp_random_range[0], exp_random_range[1]) * multiplier)
                        spirit_stones = int(monster_level * random.randint(stones_random_range[0], stones_random_range[1]) * multiplier)
                        
                        self.add_exp(user_id, exp_gain)
                        user = self.get_user(user_id)  # 重新获取用户数据，因为可能升级
                        user["spirit_stones"] += spirit_stones
                        
                        result["exp_gain"] = exp_gain
                        result["spirit_stones_gain"] = spirit_stones
                        result["message"] = f"长时间的秘境探索中遇到了 {monster}，经过一番激战，你成功击败了它！\n获得了 {exp_gain} 点修为和 {spirit_stones} 灵石！"
                    else:
                        # 战斗失败
                        result["message"] = f"长时间的秘境探索中遇到了 {monster}，不敌其强大的实力，被迫撤退..."
                
                elif event_type == "opportunity":
                    # 获取机缘配置
                    opportunity_config = adventure_events.get("opportunity", {})
                    opportunities = opportunity_config.get("events", [
                        "发现了一处修炼宝地",
                        "偶遇前辈指点",
                        "得到一篇功法残卷",
                        "悟道树下顿悟",
                        "天降灵雨洗礼"
                    ])
                    
                    # 获取技能获取概率
                    technique_chance = adventure_config.get("technique_chance", 0.2)
                    
                    # 机缘
                    opportunity = random.choice(opportunities)
                    
                    # 获取修为值
                    exp_gain = int(user["level"] * random.randint(10, 20) * multiplier)
                    self.add_exp(user_id, exp_gain)
                    
                    # 有小概率获得功法
                    # 确保概率值在0-1之间
                    if random.random() < min(1.0, technique_chance * multiplier):
                        # 从商店配置中获取可用功法
                        available_techniques = list(self.config.shop_items.get("techniques", {}).keys())
                        # 过滤掉已学习的功法
                        available_techniques = [t for t in available_techniques if t not in user["techniques"]]
                        
                        if available_techniques:
                            new_technique = random.choice(available_techniques)
                            user["techniques"].append(new_technique)
                            result["rewards"].append(new_technique)
                            result["message"] = f"长时间的秘境探索中{opportunity}，顿时感悟颇深！\n获得了 {exp_gain} 点修为，并习得了 {new_technique}！"
                        else:
                            result["message"] = f"长时间的秘境探索中{opportunity}，顿时感悟颇深！\n获得了 {exp_gain} 点修为！"
                    else:
                        result["message"] = f"长时间的秘境探索中{opportunity}，顿时感悟颇深！\n获得了 {exp_gain} 点修为！"
        
        elif status_type == "收集灵石中":
            # 从配置中获取挖矿相关参数
            mining_config = self.config.game_values.get("mining", {})
            base_stones = int(mining_config.get("base_stones", 10) * multiplier)
            level_multiplier = mining_config.get("level_multiplier", 2)
            level_bonus = int(user["level"] * level_multiplier * multiplier)
            random_range = mining_config.get("random_range", [-5, 10])
            min_stones = int(mining_config.get("min_stones", 5) * multiplier)
            critical_chance = mining_config.get("critical_chance", 0.1) * multiplier
            critical_multiplier = mining_config.get("critical_multiplier", 3)
            
            # 获取挖矿事件配置
            mining_events = self.config.mining_events
            success_messages = mining_events.get("success", {}).get("messages", ["你辛勤地挖掘矿石，获得了 {stones} 灵石。"])
            critical_messages = mining_events.get("success", {}).get("critical_messages", ["运气爆棚！你在矿洞中发现了一条灵石矿脉，获得了 {stones} 灵石！"])
            
            # 随机波动
            stones = base_stones + level_bonus + int(random.randint(random_range[0], random_range[1]) * multiplier)
            stones = max(min_stones, stones)  # 至少获得基础灵石
            
            # 小概率暴击
            critical = random.random() < critical_chance
            if critical:
                stones = int(stones * critical_multiplier)
                result["message"] = random.choice(critical_messages).format(stones=stones)
            else:
                result["message"] = random.choice(success_messages).format(stones=stones)
            
            user["spirit_stones"] += stones
            result["spirit_stones_gain"] = stones
        
        # 清除状态
        user["status"] = None
        user["status_end_time"] = 0
        user["status_start_time"] = 0
        user["status_duration"] = 0
        user["status_reward_multiplier"] = 0
        
        # 更新用户数据
        self.update_user(user_id, user)
        
        return result