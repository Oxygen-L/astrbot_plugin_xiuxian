import os
import json
import random
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from astrbot.api import logger

# 修仙游戏数据管理类
class XiuXianData:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.user_data_file = os.path.join(data_dir, "user_data.json")
        self.users = self._load_data()
        
        # 加载境界配置
        self.realms_config_file = os.path.join(data_dir, "configs", "realms.json")
        self.breakthrough_rates_file = os.path.join(data_dir, "configs", "breakthrough_rates.json")
        self.realms_config = self._load_realms_config()
        self.breakthrough_rates = self._load_breakthrough_rates()
    
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
            # 创建新用户数据
            self.users[user_id] = {
                "level": 1,  # 修为等级
                "exp": 0,    # 当前经验
                "max_exp": 100,  # 升级所需经验
                "realm": "江湖好手",  # 境界
                "last_practice_time": 0,  # 上次修炼时间
                "spirit_stones": 100,  # 灵石
                "items": [],  # 物品列表
                "techniques": [],  # 功法列表
                "username": "",  # 用户名称
                "equipment": {  # 装备栏
                    "weapon": None,
                    "armor": None,
                    "accessory": None
                },
                "stats": {  # 基础属性
                    "attack": 10,
                    "defense": 10,
                    "hp": 100,
                    "max_hp": 100
                },
                "last_adventure_time": 0,  # 上次探险时间
                "last_mine_time": 0,  # 上次挖矿时间
                "last_daily_time": 0,  # 上次每日签到时间
                "status": None,  # 当前状态：修炼中、探索中、收集灵石中等
                "status_end_time": 0,  # 状态结束时间
                "status_start_time": 0,  # 状态开始时间
                "status_duration": 0,  # 状态持续时间（小时）
                "status_reward_multiplier": 0,
                "last_steal_time": 0,  # 上次偷窃时间
                "last_duel_time": 0,  # 上次切磋时间
                "last_breakthrough_time": 0,  # 上次突破时间
                "breakthrough_bonus": 0,  # 突破加成
                "inventory": {  # 物品栏
                    "pills": {}  # 丹药
                }# 奖励倍数
            }
            self._save_data()
        return self.users[user_id]
    
    def update_user(self, user_id: str, data: Dict[str, Any]) -> None:
        """更新用户数据"""
        if user_id in self.users:
            self.users[user_id].update(data)
            self._save_data()
    
    def add_exp(self, user_id: str, exp: int) -> Dict[str, Any]:
        """增加用户经验，并检查是否升级"""
        user = self.get_user(user_id)
        user["exp"] += exp
        
        # 检查是否升级
        level_up_info = {"leveled_up": False, "old_level": user["level"], "old_realm": user["realm"]}
        
        while user["exp"] >= user["max_exp"]:
            user["exp"] -= user["max_exp"]
            user["level"] += 1
            user["max_exp"] = int(user["max_exp"] * 1.5)  # 每级所需经验增加
            level_up_info["leveled_up"] = True
            
            # 更新境界
            user["realm"] = self._get_realm_by_level(user["level"])
        
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
        if not self.realms_config:
            # 如果没有加载到配置，使用默认境界
            return "江湖好手"
        
        for realm in self.realms_config:
            if realm["level"] == level:
                return realm["name"]
        
        # 如果没有找到对应等级的境界，返回默认境界
        return "江湖好手"
    
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
        if current_index == -1 or current_index == 0:  # 注意：最高境界的索引是0（因为按等级值从高到低排序）
            return {
                "has_next": False,
                "message": "你已达到最高境界，无法继续突破。"
            }
        
        # 获取下一境界信息
        next_realm = self.realms_config[current_index - 1]
        
        # 计算所需修为
        exp_required = next_realm["exp_required"]
        current_exp = user["exp"]
        
        # 检查修为是否足够
        can_breakthrough = current_exp >= exp_required
        
        # 检查CD时间
        current_time = int(time.time())
        cd_remaining = 0
        if current_time - user.get("last_breakthrough_time", 0) < 3600:  # 1小时CD
            cd_remaining = 3600 - (current_time - user.get("last_breakthrough_time", 0))
        
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
        
        # 计算突破概率
        base_rate = next_realm_info["breakthrough_rate"]
        # 加上突破加成（如果有）
        bonus_rate = user.get("breakthrough_bonus", 0)
        final_rate = min(0.95, base_rate + bonus_rate)  # 最高95%成功率
        
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
            user["realm"] = next_realm_info["next_realm"]
            # 消耗修为
            user["exp"] -= next_realm_info["exp_required"]
            # 重置突破加成
            user["breakthrough_bonus"] = 0
            
            result["message"] = f"恭喜突破成功！你的境界提升为【{user['realm']}】"
        else:
            # 突破失败
            if not use_pill:  # 如果没有使用渡厄丹
                # 随机扣减1%-10%的修为
                exp_loss_percent = random.uniform(0.01, 0.1)
                exp_loss = int(user["exp"] * exp_loss_percent)
                user["exp"] = max(0, user["exp"] - exp_loss)
                
                # 增加下次突破成功率
                bonus_increase = base_rate * 0.3  # 当前境界基础突破概率的30%
                user["breakthrough_bonus"] += bonus_increase
                
                result["exp_loss"] = exp_loss
                result["message"] = f"突破失败！损失了 {exp_loss} 点修为，但下次突破成功率提高了 {bonus_increase*100:.1f}%"
            else:
                # 使用了渡厄丹，不损失修为
                # 增加下次突破成功率
                bonus_increase = base_rate * 0.3  # 当前境界基础突破概率的30%
                user["breakthrough_bonus"] += bonus_increase
                
                result["message"] = f"虽然突破失败，但由于使用了渡厄丹，没有损失修为。下次突破成功率提高了 {bonus_increase*100:.1f}%"
        
        # 更新用户数据
        self.update_user(user_id, user)
        
        return result
    
    def get_all_users(self) -> Dict[str, Any]:
        """获取所有用户数据"""
        return self.users
    
    def duel(self, user_id: str, target_id: str) -> Dict[str, Any]:
        """切磋功能"""
        user = self.get_user(user_id)
        target = self.get_user(target_id)
        
        # 计算战力（基于等级、装备和功法）
        user_power = user["level"] * 10 + user["stats"]["attack"] + user["stats"]["defense"]
        target_power = target["level"] * 10 + target["stats"]["attack"] + target["stats"]["defense"]
        
        # 计算胜率（战力差距影响）
        power_diff = abs(user_power - target_power)
        win_chance = 0.5 + (user_power - target_power) / max(user_power, target_power) * 0.3
        win_chance = max(0.1, min(0.9, win_chance))  # 限制在10%-90%之间
        
        # 决定胜负
        is_winner = random.random() < win_chance
        
        # 计算奖惩
        exp_change = random.randint(10, 30) * max(user["level"], target["level"])
        
        result = {
            "success": True,
            "user_power": user_power,
            "target_power": target_power,
            "message": ""
        }
        
        if is_winner:
            # 胜者获得经验，败者损失经验
            self.add_exp(user_id, exp_change)
            target["exp"] = max(0, target["exp"] - exp_change // 2)
            result["message"] = f"切磋胜利！获得修为 {exp_change} 点！"
        else:
            # 败者损失经验，胜者获得经验
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
        # 随机1-2小时的冷却时间
        cooldown = 60 * 60 * random.randint(1, 2)  # 1-2小时冷却时间
        
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
        # 随机事件类型：宝物、灵草、妖兽、机缘
        event_types = ["treasure", "herb", "monster", "opportunity"]
        event_type = random.choice(event_types)
        
        result = {
            "success": True,
            "event_type": event_type,
            "rewards": [],
            "exp_gain": 0,
            "spirit_stones_gain": 0,
            "message": ""
        }
        
        # 随机决定是否触发惩罚事件
        is_punishment = random.random() < 0.1  # 10%概率触发惩罚
        
        # 如果触发惩罚事件
        if is_punishment:
            punishments = [
                "遭遇强敌袭击",
                "踩入陷阱",
                "中了毒雾",
                "触发阵法反噬",
                "引来天劫"
            ]
            punishment = random.choice(punishments)
            
            # 损失灵石
            lost_stones = min(user["spirit_stones"], random.randint(level * 5, level * 15))
            user["spirit_stones"] -= lost_stones
            
            # 可能损失一些经验
            exp_loss = random.randint(level * 2, level * 5)
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
            # 发现宝物
            spirit_stones = random.randint(level * 10, level * 30)
            result["spirit_stones_gain"] = spirit_stones
            user["spirit_stones"] += spirit_stones
            result["message"] = f"你在秘境中发现了一处宝藏，获得了 {spirit_stones} 灵石！"
            
        elif event_type == "herb":
            # 发现灵草
            herbs = ["灵草", "灵芝", "仙参", "龙血草", "九转还魂草"]
            herb = random.choice(herbs)
            user["items"].append(herb)
            result["rewards"].append(herb)
            result["message"] = f"你在秘境中发现了珍贵的 {herb}！"
            
        elif event_type == "monster":
            # 遇到妖兽
            monster_names = ["山猪", "赤焰狐", "黑风狼", "幽冥蛇", "雷霆鹰"]
            monster = random.choice(monster_names)
            
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
                
                result["message"] = f"你在秘境中遇到了 {monster}，经过一番激战，你成功击败了它！\n获得了 {exp_gain} 点修为和 {spirit_stones} 灵石！"
            else:
                # 战斗失败
                result["message"] = f"你在秘境中遇到了 {monster}，不敌其强大的实力，被迫撤退...\n下次再来挑战吧！"
        
        elif event_type == "opportunity":
            # 机缘
            opportunities = [
                "发现了一处修炼宝地",
                "偶遇前辈指点",
                "得到一篇功法残卷",
                "悟道树下顿悟",
                "天降灵雨洗礼"
            ]
            opportunity = random.choice(opportunities)
            
            exp_gain = level * random.randint(10, 20)
            result["exp_gain"] = exp_gain
            self.add_exp(user_id, exp_gain)
            
            # 有小概率获得功法
            if random.random() < 0.2:
                techniques = ["吐纳术", "御风术", "小周天功", "金刚不坏", "五行遁法", "太极剑法"]
                available_techniques = [t for t in techniques if t not in user["techniques"]]
                
                if available_techniques:
                    new_technique = random.choice(available_techniques)
                    user["techniques"].append(new_technique)
                    result["rewards"].append(new_technique)
                    result["message"] = f"你在秘境中{opportunity}，顿时感悟颇深！\n获得了 {exp_gain} 点修为，并习得了 {new_technique}！"
                else:
                    result["message"] = f"你在秘境中{opportunity}，顿时感悟颇深！\n获得了 {exp_gain} 点修为！"
            else:
                result["message"] = f"你在秘境中{opportunity}，顿时感悟颇深！\n获得了 {exp_gain} 点修为！"
        
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
        
        # 功法列表及其所需灵石和等级
        techniques = {
            "吐纳术": {"level": 1, "cost": 100},
            "御风术": {"level": 5, "cost": 300},
            "小周天功": {"level": 10, "cost": 800},
            "金刚不坏": {"level": 15, "cost": 1500},
            "五行遁法": {"level": 20, "cost": 3000},
            "太极剑法": {"level": 25, "cost": 5000},
            "大周天功": {"level": 30, "cost": 8000},
            "九阳神功": {"level": 40, "cost": 15000},
            "乾坤大挪移": {"level": 50, "cost": 30000}
        }
        
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
        
        # 功法列表及其所需灵石和等级
        all_techniques = {
            "吐纳术": {"level": 1, "cost": 100, "description": "基础呼吸法，提升修炼速度"},
            "御风术": {"level": 5, "cost": 300, "description": "掌控风元素，提升移动速度"},
            "小周天功": {"level": 10, "cost": 800, "description": "打通周身经脉，增强修炼效率"},
            "金刚不坏": {"level": 15, "cost": 1500, "description": "强化体魄，提高防御力"},
            "五行遁法": {"level": 20, "cost": 3000, "description": "掌握五行之力，提高闪避能力"},
            "太极剑法": {"level": 25, "cost": 5000, "description": "刚柔并济的剑法，提高攻击力"},
            "大周天功": {"level": 30, "cost": 8000, "description": "贯通全身经脉，大幅提升修炼效率"},
            "九阳神功": {"level": 40, "cost": 15000, "description": "至阳至刚的功法，全面提升各项属性"},
            "乾坤大挪移": {"level": 50, "cost": 30000, "description": "移星换斗的神功，可借力打力"}
        }
        
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
        
        # 丹药列表及其所需灵石和等级
        all_pills = {
            "渡厄丹": {"level": 5, "cost": 200, "description": "服用后可恢复少量修为，突破瓶颈", "effect": {"exp": 50}},
            "聚气丹": {"level": 15, "cost": 500, "description": "服用后可恢复中量修为，提升修炼速度", "effect": {"exp": 150}},
            "回春丹": {"level": 25, "cost": 1000, "description": "服用后可恢复大量修为，延年益寿", "effect": {"exp": 300}},
            "洗髓丹": {"level": 35, "cost": 2000, "description": "服用后可洗髓伐毛，重塑根基", "effect": {"exp": 500}},
            "金元丹": {"level": 45, "cost": 5000, "description": "服用后可大幅提升修为，改善体质", "effect": {"exp": 1000}}
        }
        
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
        
        # 丹药列表及其所需灵石和等级
        all_pills = {
            "渡厄丹": {"level": 5, "cost": 200, "description": "服用后可恢复少量修为，突破瓶颈", "effect": {"exp": 50}},
            "聚气丹": {"level": 15, "cost": 500, "description": "服用后可恢复中量修为，提升修炼速度", "effect": {"exp": 150}},
            "回春丹": {"level": 25, "cost": 1000, "description": "服用后可恢复大量修为，延年益寿", "effect": {"exp": 300}},
            "洗髓丹": {"level": 35, "cost": 2000, "description": "服用后可洗髓伐毛，重塑根基", "effect": {"exp": 500}},
            "金元丹": {"level": 45, "cost": 5000, "description": "服用后可大幅提升修为，改善体质", "effect": {"exp": 1000}}
        }
        
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
        
        # 丹药列表及其效果
        all_pills = {
            "渡厄丹": {"level": 5, "cost": 200, "description": "服用后可恢复少量修为，突破瓶颈", "effect": {"exp": 50}, "breakthrough_bonus": 0.1},
            "聚气丹": {"level": 15, "cost": 500, "description": "服用后可恢复中量修为，提升修炼速度", "effect": {"exp": 150}},
            "回春丹": {"level": 25, "cost": 1000, "description": "服用后可恢复大量修为，延年益寿", "effect": {"exp": 300}},
            "洗髓丹": {"level": 35, "cost": 2000, "description": "服用后可洗髓伐毛，重塑根基", "effect": {"exp": 500}},
            "金元丹": {"level": 45, "cost": 5000, "description": "服用后可大幅提升修为，改善体质", "effect": {"exp": 1000}}
        }
        
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
        
        # 增加经验并检查是否升级
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
        # 随机1-2小时的冷却时间
        cooldown = 60 * 60 * random.randint(1, 2)  # 1-2小时冷却时间
        
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
        is_punishment = random.random() < 0.1  # 10%概率触发惩罚
        
        if is_punishment:
            punishments = [
                "矿洞坍塌",
                "遭遇矿妖袭击",
                "触发禁制陷阱",
                "灵石爆炸",
                "挖到诅咒石"
            ]
            punishment = random.choice(punishments)
            
            # 损失灵石
            lost_stones = min(user["spirit_stones"], random.randint(user["level"] * 3, user["level"] * 10))
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
        base_stones = 10
        level_bonus = user["level"] * 2
        
        # 随机波动
        stones = base_stones + level_bonus + random.randint(-5, 10)
        stones = max(5, stones)  # 至少获得5灵石
        
        # 小概率暴击
        critical = random.random() < 0.1
        if critical:
            stones = stones * 3
            message = f"运气爆棚！你在矿洞中发现了一条灵石矿脉，获得了 {stones} 灵石！"
        else:
            message = f"你辛勤地挖掘矿石，获得了 {stones} 灵石。"
        
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
        
        # 根据连续签到天数给予奖励
        streak = user["daily_streak"]
        base_stones = 50
        streak_bonus = min(streak * 10, 100)  # 最多额外奖励100灵石
        
        stones = base_stones + streak_bonus
        exp = user["level"] * 5  # 经验奖励与等级相关
        
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
    # 该函数为静态方法，不需要实例化即可调用
    @staticmethod
    def get_equipment_list() -> Dict[str, List[Dict[str, Any]]]:
        """获取所有可用装备列表"""
        equipment = {
            "weapon": [
                {"id": "w1", "name": "木剑", "level": 1, "cost": 200, "attack": 5, "description": "普通的木制剑，适合初学者使用"},
                {"id": "w2", "name": "铁剑", "level": 5, "cost": 500, "attack": 15, "description": "坚固的铁剑，具有不错的攻击力"},
                {"id": "w3", "name": "青锋剑", "level": 10, "cost": 1200, "attack": 30, "description": "锋利的精钢宝剑，削铁如泥"},
                {"id": "w4", "name": "赤焰剑", "level": 20, "cost": 3000, "attack": 60, "description": "蕴含火属性的法剑，可灼烧敌人"},
                {"id": "w5", "name": "紫电神剑", "level": 30, "cost": 8000, "attack": 100, "description": "雷属性神兵，攻击带有麻痹效果"},
                {"id": "w6", "name": "太虚剑", "level": 50, "cost": 20000, "attack": 200, "description": "传说中的仙家宝剑，锋利无比"}
            ],
            "armor": [
                {"id": "a1", "name": "布衣", "level": 1, "cost": 200, "defense": 5, "description": "普通的布制衣服，提供基础防护"},
                {"id": "a2", "name": "皮甲", "level": 5, "cost": 500, "defense": 15, "description": "用兽皮制成的护甲，提供较好的防护"},
                {"id": "a3", "name": "铁甲", "level": 10, "cost": 1200, "defense": 30, "description": "坚固的铁制护甲，大幅提升防御力"},
                {"id": "a4", "name": "玄冰甲", "level": 20, "cost": 3000, "defense": 60, "description": "蕴含冰属性的法甲，可抵御火属性攻击"},
                {"id": "a5", "name": "金刚甲", "level": 30, "cost": 8000, "defense": 100, "description": "坚不可摧的护甲，大幅提升生存能力"},
                {"id": "a6", "name": "仙云法衣", "level": 50, "cost": 20000, "defense": 200, "description": "仙家法衣，轻若无物却防御惊人"}
            ],
            "accessory": [
                {"id": "ac1", "name": "木质护符", "level": 1, "cost": 200, "hp": 20, "description": "简单的护身符，略微增加生命值"},
                {"id": "ac2", "name": "玉佩", "level": 5, "cost": 500, "hp": 50, "description": "蕴含灵气的玉佩，提升生命值"},
                {"id": "ac3", "name": "灵珠", "level": 10, "cost": 1200, "hp": 100, "description": "凝聚灵气的宝珠，大幅提升生命值"},
                {"id": "ac4", "name": "聚灵环", "level": 20, "cost": 3000, "hp": 200, "description": "聚集周围灵气的法器，显著提升生命值"},
                {"id": "ac5", "name": "龙血石", "level": 30, "cost": 8000, "hp": 400, "description": "蕴含龙族精血的宝石，极大提升生命力"},
                {"id": "ac6", "name": "仙灵珠", "level": 50, "cost": 20000, "hp": 800, "description": "仙界宝物，拥有强大的生命力"}
            ]
        }
        
        return equipment
    
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
    def set_status(self, user_id: str, status_type: str, duration_hours: float) -> Dict[str, Any]:
        """设置用户状态
        
        Args:
            user_id: 用户ID
            status_type: 状态类型，可选值：'修炼中'、'探索中'、'收集灵石中'
            duration_hours: 持续时间（小时），可以是小数表示小时和分钟，范围0.1-6小时
            
        Returns:
            包含状态信息的字典
        """
        user = self.get_user(user_id)
        current_time = int(time.time())
        
        # 检查是否已有状态
        if user["status"] is not None and current_time < user["status_end_time"]:
            remaining = user["status_end_time"] - current_time
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return {
                "success": False,
                "message": f"你当前正处于{user['status']}状态，还需 {hours}小时{minutes}分钟 结束"
            }
        
        # 限制持续时间在0.1-6小时之间
        # duration_hours = max(0.1, min(6, duration_hours))
        duration_seconds = int(duration_hours * 3600)
        
        # 计算奖励倍数（时间越长，奖励越多）
        reward_multiplier = duration_hours + 1
        
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
            "message": f"你已进入{status_type}状态，将持续 {duration_hours} 小时"
        }
    
    def check_status(self, user_id: str) -> Dict[str, Any]:
        """检查用户当前状态"""
        user = self.get_user(user_id)
        current_time = int(time.time())
        
        # 如果没有状态或状态已结束
        if user["status"] is None or current_time >= user["status_end_time"]:
            return {
                "has_status": False,
                "message": "你当前没有进行中的状态"
            }
        
        # 计算剩余时间
        remaining = user["status_end_time"] - current_time
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        
        return {
            "has_status": True,
            "status": user["status"],
            "remaining": remaining,
            "message": f"你当前正处于{user['status']}状态，还需 {hours}小时{minutes}分钟{seconds}秒 结束"
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
        
        # 如果状态未结束
        if current_time < user["status_end_time"]:
            logger.info(f"current_time: {current_time}, user['status_end_time']: {user['status_end_time']}")
            remaining = user["status_end_time"] - current_time
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return {
                "success": False,
                "message": f"你的{user['status']}尚未完成，还需 {hours}小时{minutes}分钟"
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
            # 修炼获得经验
            base_exp = 10 * multiplier
            exp_gain = int(base_exp * (1 + random.random() * 0.5))  # 随机波动
            
            level_up_info = self.add_exp(user_id, exp_gain)
            user = self.get_user(user_id)  # 重新获取更新后的数据
            
            result["exp_gain"] = exp_gain
            result["leveled_up"] = level_up_info["leveled_up"]
            
            if level_up_info["leveled_up"]:
                result["message"] = f"闭关修炼结束，获得 {exp_gain} 点修为！\n境界提升：{level_up_info['old_realm']} → {user['realm']}\n等级提升：{level_up_info['old_level']} → {user['level']}"
            else:
                result["message"] = f"闭关修炼结束，获得 {exp_gain} 点修为！"
        
        elif status_type == "探索中":
            # 秘境探索获得奖励，有几率获得灵石、经验或物品，也有几率受到惩罚
            is_punishment = random.random() < 0.1  # 10%概率触发惩罚
            
            if is_punishment:
                punishments = [
                    "遭遇强敌袭击",
                    "踩入陷阱",
                    "中了毒雾",
                    "触发阵法反噬",
                    "引来天劫"
                ]
                punishment = random.choice(punishments)
                
                # 损失灵石
                lost_stones = min(user["spirit_stones"], random.randint(user["level"] * 5, user["level"] * 15))
                user["spirit_stones"] -= lost_stones
                
                # 可能损失一些经验
                exp_loss = random.randint(user["level"] * 2, user["level"] * 5)
                user["exp"] = max(0, user["exp"] - exp_loss)
                
                result["is_punishment"] = True
                result["spirit_stones_loss"] = lost_stones
                result["exp_loss"] = exp_loss
                result["message"] = f"长时间的秘境探索中{punishment}，损失了 {lost_stones} 灵石和 {exp_loss} 点修为！"
            else:
                # 随机事件类型：宝物、灵草、妖兽、机缘
                event_types = ["treasure", "herb", "monster", "opportunity"]
                event_type = random.choice(event_types)
                
                if event_type == "treasure":
                    # 发现宝物
                    spirit_stones = random.randint(user["level"] * 10, user["level"] * 30) * multiplier
                    user["spirit_stones"] += spirit_stones
                    result["spirit_stones_gain"] = spirit_stones
                    result["message"] = f"长时间的秘境探索中发现了一处宝藏，获得了 {spirit_stones} 灵石！"
                
                elif event_type == "herb":
                    # 发现灵草
                    herbs = ["灵草", "灵芝", "仙参", "龙血草", "九转还魂草"]
                    herb_count = min(5, multiplier + random.randint(0, 2))
                    found_herbs = random.sample(herbs, min(herb_count, len(herbs)))
                    
                    for herb in found_herbs:
                        user["items"].append(herb)
                    
                    result["rewards"] = found_herbs
                    result["message"] = f"长时间的秘境探索中发现了珍贵的草药：{', '.join(found_herbs)}！"
                
                elif event_type == "monster":
                    # 遇到妖兽
                    monster_names = ["山猪", "赤焰狐", "黑风狼", "幽冥蛇", "雷霆鹰"]
                    monster = random.choice(monster_names)
                    
                    # 简单战斗逻辑
                    monster_level = random.randint(max(1, user["level"] - 5), user["level"] + 5)
                    win_chance = 0.5 + (user["level"] - monster_level) * 0.1  # 等级差影响胜率
                    win_chance = max(0.1, min(0.9, win_chance))  # 胜率限制在10%~90%
                    
                    if random.random() < win_chance:
                        # 战斗胜利
                        exp_gain = monster_level * random.randint(5, 10) * multiplier
                        spirit_stones = monster_level * random.randint(5, 15) * multiplier
                        
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
                    # 机缘
                    opportunities = [
                        "发现了一处修炼宝地",
                        "偶遇前辈指点",
                        "得到一篇功法残卷",
                        "悟道树下顿悟",
                        "天降灵雨洗礼"
                    ]
                    opportunity = random.choice(opportunities)
                    
                    exp_gain = user["level"] * random.randint(10, 20) * multiplier
                    self.add_exp(user_id, exp_gain)
                    
                    # 有小概率获得功法
                    if random.random() < 0.2 * multiplier:
                        techniques = ["吐纳术", "御风术", "小周天功", "金刚不坏", "五行遁法", "太极剑法"]
                        available_techniques = [t for t in techniques if t not in user["techniques"]]
                        
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
            # 收集灵石
            base_stones = 10 * multiplier
            level_bonus = user["level"] * 2 * multiplier
            
            # 随机波动
            stones = base_stones + level_bonus + random.randint(-5, 10) * multiplier
            stones = max(5 * multiplier, stones)  # 至少获得基础灵石
            
            # 小概率暴击
            critical = random.random() < 0.1 * multiplier
            if critical:
                stones = stones * 3
                result["message"] = f"长时间的灵石收集中运气爆棚！你发现了一条灵石矿脉，获得了 {stones} 灵石！"
            else:
                result["message"] = f"长时间的灵石收集结束，你获得了 {stones} 灵石。"
            
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