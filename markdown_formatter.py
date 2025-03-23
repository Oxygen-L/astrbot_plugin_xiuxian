# 修仙游戏Markdown格式化模块
import time
from .xiuxian_data import XiuXianData

class MarkdownFormatter:
    """
    用于将文本转换为Markdown格式的工具类
    提供各种格式化方法，使输出更加美观
    """
    
    @staticmethod
    def format_help(text):
        """
        格式化帮助信息
        """
        lines = text.strip().split('\n')
        title = "# 修仙游戏指令帮助"
        
        # 提取指令部分
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if not line or line == "【修仙游戏指令】":
                continue
            elif line == "踏上仙途，修炼不止！":
                formatted_lines.append("\n*踏上仙途，修炼不止！*")
                continue
                
            if "-" in line:
                cmd, desc = line.split("-", 1)
                formatted_lines.append(f"\n- **{cmd.strip()}**{desc}")
        
        return f"{title}\n\n{''.join(formatted_lines)}"
    
    @staticmethod
    def format_welcome(user_name, spirit_stones):
        """
        格式化欢迎信息
        """
        return f"## 🎉 欢迎踏上修仙之路！\n\n**{user_name}** 道友，你已成功踏入修仙世界！\n\n💎 初始灵石: **{spirit_stones}** 枚\n\n可使用 `/修仙帮助` 查看所有可用指令。\n\n> *祝你修仙之路一帆风顺，早日飞升成仙！*"
    
    @staticmethod
    def format_user_info(user_name, user_data, all_equipment, status_info=None):
        """
        格式化用户信息
        """
        info = f"## 🧙 {user_name} 的修仙信息\n\n"
        
        # 计算战力
        battle_power = user_data["level"] * 10
        if "stats" in user_data:
            battle_power += user_data["stats"].get("attack", 0) + user_data["stats"].get("defense", 0)
        
        # 基本信息表格
        info += "| 属性 | 数值 |\n| --- | --- |\n"
        info += f"| 境界 | **{user_data['realm']}** |\n"
        info += f"| 修为等级 | {user_data['level']} |\n"
        info += f"| 详细修为 | {user_data['exp']}/{user_data['max_exp']} |\n"
        info += f"| 灵石 | 💎 {user_data['spirit_stones']} |\n"
        info += f"| 战力 | ⚔️ {battle_power} |\n"
        
        # 属性详情
        if "stats" in user_data:
            info += "\n### 🔥 属性详情\n"
            info += "| 属性 | 数值 |\n| --- | --- |\n"
            info += f"| 攻击力 | {user_data['stats'].get('attack', 0)} |\n"
            info += f"| 防御力 | {user_data['stats'].get('defense', 0)} |\n"
            info += f"| 生命值 | {user_data['stats'].get('hp', 0)}/{user_data['stats'].get('max_hp', 100)} |\n"
        
        if "equipment" in user_data and any(user_data["equipment"].values()):
            info += "\n### 🔮 装备信息\n"
            info += "| 装备槽 | 已装备 |\n| --- | --- |\n"
            
            weapon = user_data["equipment"].get("weapon")
            armor = user_data["equipment"].get("armor")
            accessory = user_data["equipment"].get("accessory")
            
            # 查询装备详细名称
            if weapon:
                for item in all_equipment["weapon"]:
                    if item['id'] == weapon:
                        weapon_name = item['name']
                        break
            if armor:
                for item in all_equipment["armor"]:
                    if item['id'] == armor:
                        armor_name = item['name']
                        break
            if accessory:
                for item in all_equipment["accessory"]:
                    if item['id'] == accessory:
                        accessory_name = item['name']
                        break
            
            info += f"| 武器 | {weapon_name if weapon else '无'} |\n"
            info += f"| 护甲 | {armor_name if armor else '无'} |\n"
            info += f"| 饰品 | {accessory_name if accessory else '无'} |\n"
        
        # 丹药库存
        if "inventory" in user_data and "pills" in user_data["inventory"] and user_data["inventory"]["pills"]:
            info += "\n### 💊 丹药库存\n"
            info += "| 丹药 | 数量 |\n| --- | --- |\n"
            for pill_name, count in user_data["inventory"]["pills"].items():
                if count > 0:
                    info += f"| {pill_name} | {count} |\n"
        
        # 已学功法
        if user_data['techniques']:
            info += "\n### 📜 已学功法\n"
            for technique in user_data['techniques']:
                info += f"- *{technique}*\n"
        
        # 冷却时间信息
        current_time = int(time.time())
        cooldown_info = []
        
        # 切磋冷却
        if "last_duel_time" in user_data and current_time - user_data.get("last_duel_time", 0) < 600:
            remaining = 600 - (current_time - user_data.get("last_duel_time", 0))
            minutes = remaining // 60
            seconds = remaining % 60
            cooldown_info.append(f"⚔️ 切磋冷却: {minutes}分{seconds}秒")
        
        # 偷窃冷却
        if "last_steal_time" in user_data and current_time - user_data.get("last_steal_time", 0) < 600:
            remaining = 600 - (current_time - user_data.get("last_steal_time", 0))
            minutes = remaining // 60
            seconds = remaining % 60
            cooldown_info.append(f"🕵️ 偷窃冷却: {minutes}分{seconds}秒")
        
        # 探险冷却
        if "last_adventure_time" in user_data:
            cooldown = 60 * 60 * 2  # 假设最大冷却时间为2小时
            if current_time - user_data.get("last_adventure_time", 0) < cooldown:
                remaining = cooldown - (current_time - user_data.get("last_adventure_time", 0))
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                cooldown_info.append(f"🔍 探险冷却: {hours}小时{minutes}分钟")
        
        if cooldown_info:
            info += "\n### ⏱️ 冷却时间\n"
            for cd_info in cooldown_info:
                info += f"- {cd_info}\n"
        
        # 状态信息
        if status_info and status_info["has_status"]:
            info += f"\n### ⏳ 当前状态\n**{status_info['message']}**"
        
        return info
    
    @staticmethod
    def format_rank(sorted_users):
        """
        格式化排行榜
        """
        rank_text = "## 🏆 修仙世界排行榜\n\n"
        rank_text += "| 排名 | 修士 | 境界 | 等级 |\n| --- | --- | --- | --- |\n"
        
        for i, (user_id, user_data) in enumerate(sorted_users[:10], 1):
            rank_text += f"| {i} | {user_data['username']} | {user_data['realm']} | {user_data['level']} |\n"
        
        return rank_text
    
    @staticmethod
    def format_practice_start(user_name, duration_hours, end_time):
        """
        格式化开始修炼信息
        """
        result = f"## ⏳ 闭关修炼\n\n**{user_name}** 道友开始闭关修炼！\n\n"
        result += "> *修炼已开始，你可以随时使用 /结束修炼 命令结束修炼并获取奖励。*\n\n"
        result += "> *修炼时间越长，获得的修为越多，请根据自己的情况决定修炼时长。*"
        
        return result
    
    @staticmethod
    def format_adventure_start(user_name, duration_hours, end_time):
        """
        格式化开始探索信息
        """
        result = f"## 🔍 秘境探索\n\n**{user_name}** 道友开始进入秘境探索！\n\n"
        result += f"- 探索时长: **{round(duration_hours, 3)}** 小时\n"
        # result += f"- 预计归来: **{end_time}**\n\n"
        result += "> *探索时间越长，获得的奖励越丰厚，但风险也越大，请耐心等待。*\n\n"
        result += "> *探索结束后，你将获得丰厚的奖励！*"
        
        return result
    
    @staticmethod
    def format_mining_start(user_name, duration_hours, end_time):
        """
        格式化开始收集灵石信息
        """
        result = f"## 💎 灵石收集\n\n**{user_name}** 道友开始收集灵石！\n\n"
        result += f"- 收集时长: **{round(duration_hours, 3)}** 小时\n"
        # result += f"- 预计完成: **{end_time}**\n\n"
        return result
        
    @staticmethod
    def format_practice_result(user_name, result):
        """
        格式化修炼结果
        """
        message = f"## 🔥 修炼完成\n\n**{user_name}** 道友结束了闭关修炼！\n\n"
        
        # 添加修炼时长信息
        if "status_duration" in result:
            hours = int(result["status_duration"])
            minutes = int((result["status_duration"] - hours) * 60)
            message += f"- 修炼时长: **{hours}小时{minutes}分钟**\n"
        
        # 添加获得的修为信息
        if "exp_gain" in result:
            message += f"- 获得修为: **{result['exp_gain']}**\n"
        
        # 添加是否顿悟的信息
        if result.get("is_critical", False):
            message += f"\n> *恭喜！你在修炼过程中有所顿悟，获得了额外的修为！*\n"
        
        # 添加是否升级的信息
        if result.get("leveled_up", False):
            message += f"\n> *恭喜！你的境界提升了！*\n"
        
        return message
        
    @staticmethod
    def format_breakthrough_result(user_name, result):
        """
        格式化突破结果
        """
        if result["is_breakthrough_success"]:
            # 突破成功
            output = f"## 🎉 突破成功！\n\n**{user_name}** 道友突破成功！\n\n"
            output += f"- 原境界: **{result['old_realm']}**\n"
            output += f"- 新境界: **{result['new_realm']}**\n\n"
            output += "> *恭喜道友修为精进，境界提升！*\n"
        else:
            # 突破失败
            output = f"## ⚠️ 突破失败\n\n**{user_name}** 道友突破失败！\n\n"
            if result["exp_loss"] > 0:
                output += f"- 损失修为: **{result['exp_loss']}**\n"
            output += f"- 当前境界: **{result['old_realm']}**\n\n"
            output += "> *道友不必灰心，继续修炼，终有所成！*\n"
        
        return output
    
    @staticmethod
    def format_breakthrough_info(user_name, next_realm_info):
        """
        格式化突破信息
        """
        if not next_realm_info["has_next"]:
            return f"## ⚠️ 无法突破\n\n**{user_name}** 道友，{next_realm_info['message']}"
        
        # 检查CD时间
        cd_info = ""
        if next_realm_info["cd_remaining"] > 0:
            minutes = next_realm_info["cd_remaining"] // 60
            seconds = next_realm_info["cd_remaining"] % 60
            cd_info = f"- 冷却时间: **{minutes}分{seconds}秒**\n"
        
        # 检查修为是否足够
        exp_info = ""
        if next_realm_info["can_breakthrough"]:
            exp_info = f"- 修为状态: **充足** (当前: {next_realm_info['current_exp']}/{next_realm_info['exp_required']})\n"
        else:
            exp_info = f"- 修为状态: **不足** (当前: {next_realm_info['current_exp']}/{next_realm_info['exp_required']})\n"
        
        # 突破成功率
        rate = next_realm_info["breakthrough_rate"] * 100
        
        output = f"## 🔮 突破信息\n\n**{user_name}** 道友，你的突破信息如下：\n\n"
        output += f"- 当前境界: **{next_realm_info['current_realm']}**\n"
        output += f"- 下一境界: **{next_realm_info['next_realm']}**\n"
        output += exp_info
        output += f"- 基础成功率: **{rate:.1f}%**\n"
        if cd_info:
            output += cd_info
        
        if next_realm_info["can_breakthrough"] and next_realm_info["cd_remaining"] <= 0:
            output += "\n> *道友可以尝试突破了，输入 /突破 开始突破！*\n"
            output += "> *也可以使用渡厄丹辅助突破，失败时不会损失修为，输入 /突破 渡厄丹*\n"
        elif not next_realm_info["can_breakthrough"]:
            output += "\n> *道友修为不足，需要继续修炼积累更多修为。*\n"
        elif next_realm_info["cd_remaining"] > 0:
            output += "\n> *道友需要等待冷却时间结束后才能尝试突破。*\n"
        
        return output
        
    @staticmethod
    def format_mining_start(user_name, duration_hours, end_time):
        """
        格式化开始收集灵石信息
        """
        result = f"## 💎 灵石收集\n\n**{user_name}** 道友开始收集灵石！\n\n"
        result += f"- 收集时长: **{duration_hours}** 小时\n"
        # result += f"- 预计完成: **{end_time}**\n\n"
        result += "> *收集时间越长，获得的灵石越多，请耐心等待。*\n\n"
        result += "> *收集结束后，你将获得丰厚的灵石奖励！*"
        
        return result
    
    @staticmethod
    def format_daily_sign(user_name, message):
        """
        格式化签到信息
        """
        return f"## 📅 每日签到\n\n**{user_name}** 道友，{message}"
    
    @staticmethod
    def format_shop(user_name, available_equipment, available_techniques, available_pills):
        """
        格式化商店信息
        """
        message = f"## 🏪 仙缘阁商店 - {user_name} 道友\n\n"
        
        # 装备区
        message += "### 🔮 装备区\n\n"
        
        # 武器
        message += "#### 武器\n"
        message += "| 状态 | 名称 | ID | 等级需求 | 价格 | 属性 |\n| --- | --- | --- | --- | --- | --- |\n"
        for item in available_equipment["weapon"]:
            status = "✅" if item["equipped"] else "💰" if item["can_buy"] else "🔒"
            message += f"| {status} | {item['name']} | {item['id']} | {item['level']} | {item['cost']} 灵石 | 攻击+{item['attack']} |\n"
        
        # 护甲
        message += "\n#### 护甲\n"
        message += "| 状态 | 名称 | ID | 等级需求 | 价格 | 属性 |\n| --- | --- | --- | --- | --- | --- |\n"
        for item in available_equipment["armor"]:
            status = "✅" if item["equipped"] else "💰" if item["can_buy"] else "🔒"
            message += f"| {status} | {item['name']} | {item['id']} | {item['level']} | {item['cost']} 灵石 | 防御+{item['defense']} |\n"
        
        # 饰品
        message += "\n#### 饰品\n"
        message += "| 状态 | 名称 | ID | 等级需求 | 价格 | 属性 |\n| --- | --- | --- | --- | --- | --- |\n"
        for item in available_equipment["accessory"]:
            status = "✅" if item["equipped"] else "💰" if item["can_buy"] else "🔒"
            message += f"| {status} | {item['name']} | {item['id']} | {item['level']} | {item['cost']} 灵石 | 生命+{item['hp']} |\n"
        
        # 功法区
        message += "\n### 📜 功法区\n"
        message += "| 状态 | 名称 | 等级需求 | 价格 | 描述 |\n| --- | --- | --- | --- | --- |\n"
        for technique in available_techniques:
            status = "✅" if technique["learned"] else "💰" if technique["can_learn"] else "🔒"
            message += f"| {status} | {technique['name']} | {technique['level_required']} | {technique['cost']} 灵石 | {technique['description']} |\n"
        
        # 丹药区
        message += "\n### 💊 丹药区\n"
        message += "| 状态 | 名称 | 等级需求 | 价格 | 拥有 | 描述 |\n| --- | --- | --- | --- | --- | --- |\n"
        for pill in available_pills:
            status = "💰" if pill["can_buy"] else "🔒"
            owned = pill["owned"] if "owned" in pill and pill["owned"] > 0 else 0
            message += f"| {status} | {pill['name']} | {pill['level_required']} | {pill['cost']} 灵石 | {owned} | {pill['description']} |\n"
        
        # 购买指令说明
        message += "\n### 购买指令\n"
        message += "- **购买装备 [装备ID]** - 例如：购买装备 w1\n"
        message += "- **学习功法 [功法名]** - 例如：学习功法 吐纳术\n"
        message += "- **购买丹药 [丹药名]** - 例如：购买丹药 渡厄丹\n"
        message += "- **使用丹药 [丹药名]** - 例如：使用丹药 渡厄丹\n"
        
        return message
    
    @staticmethod
    def format_status(user_name, status_info=None):
        """
        格式化状态信息
        """
        if status_info and status_info["has_status"]:
            return f"## ⏳ 当前状态\n\n**{user_name}** 道友，{status_info['message']}"
        else:
            return f"## 🆓 当前状态\n\n**{user_name}** 道友，你当前处于空闲状态，可以进行修炼、探索或收集灵石等活动。"
    
    @staticmethod
    def format_duel_result(user_name, target_name, user_power, target_power, message):
        """
        格式化切磋结果
        """
        result = f"## ⚔️ 切磋结果\n\n**{user_name}** 与 **{target_name}** 切磋一番！\n\n"
        result += "| 修士 | 战力 |\n| --- | --- |\n"
        result += f"| {user_name} | {user_power} |\n"
        result += f"| {target_name} | {target_power} |\n\n"
        result += f"**结果**: {message}"
        
        return result
    
    @staticmethod
    def format_steal_result(user_name, target_name, message):
        """
        格式化偷窃结果
        """
        return f"## 🕵️ 偷窃行动\n\n**{user_name}** 尝试偷取 **{target_name}** 的灵石！\n\n{message}"
    
    @staticmethod
    def format_learn_result(user_name, message):
        """
        格式化学习功法结果
        """
        return f"## 📚 学习功法\n\n**{user_name}** 道友，{message}"
    
    @staticmethod
    def format_buy_equipment_result(user_name, message):
        """
        格式化购买装备结果
        """
        return f"## 🛒 购买装备\n\n**{user_name}** 道友，{message}"
    
    @staticmethod
    def format_buy_pill_result(user_name, message):
        """
        格式化购买丹药结果
        """
        return f"## 🛒 购买丹药\n\n**{user_name}** 道友，{message}"
    
    @staticmethod
    def format_use_pill_result(user_name, message):
        """
        格式化使用丹药结果
        """
        return f"## 💊 使用丹药\n\n**{user_name}** 道友，{message}"