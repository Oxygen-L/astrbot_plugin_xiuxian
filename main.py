from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
import time
from .xiuxian_data import XiuXianData
from .markdown_formatter import MarkdownFormatter

@register("xiuxian", "修仙游戏", "一个简单的修仙游戏插件", "1.0.0")
class XiuXianPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化数据管理器
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(plugin_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_manager = XiuXianData(data_dir)
    
    async def check_and_complete_status(self, event: AstrMessageEvent, user_id: str, user_name: str):
        '''检查并完成状态，如果状态已结束则发放奖励'''
        user_data = self.data_manager.get_user(user_id)
        
        # 如果用户没有状态或状态未结束，直接返回False
        if user_data["status"] is None:
            return False
            
        current_time = int(time.time())
        if current_time < user_data["status_end_time"]:
            return False
            
        # 状态已结束，获取奖励
        result = self.data_manager.complete_status(user_id)
        
        if result["success"]:
            # 发送奖励消息
            await event.reply(f"道友 {user_name}，{result['message']}")
            return True
            
        return False
    
    @filter.command("修仙帮助")
    async def xiuxian_help(self, event: AstrMessageEvent):
        '''修仙游戏帮助指令'''
        help_text = """【修仙游戏指令】
                    /我要修仙 - 开始修仙之旅
                    /修仙帮助 - 显示帮助
                    /修炼 [1-3小时] - 闭关修炼获取修为，可指定1-3小时
                    /修仙信息 - 查看修仙信息
                    /修仙排行 - 查看排行榜
                    /秘境探索 [1-3小时] - 探索秘境获奖励，可指定1-3小时
                    /灵石收集 [1-3小时] - 获取灵石，可指定1-3小时
                    /修仙状态 - 查看当前状态
                    /修仙签到 - 每日签到
                    /修仙商店 - 查看统一商店（功法、装备、丹药）
                    /购买装备 [装备ID] - 购买装备
                    /学习功法 [功法名] - 学习功法
                    /购买丹药 [丹药名] - 购买丹药
                    /使用丹药 [丹药名] - 使用丹药

                    踏上仙途，修炼不止！"""
        # 使用Markdown格式化帮助信息
        formatted_help = MarkdownFormatter.format_help(help_text)
        yield event.plain_result(formatted_help)
    
    @filter.command("我要修仙")
    async def xiuxian_start(self, event: AstrMessageEvent):
        '''开始修仙之旅'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你已经踏上修仙之路，不必重新开始。")
            return
        
        # 标记用户已开始修仙并保存用户名称
        user_data["has_started"] = True
        user_data["username"] = user_name
        self.data_manager.update_user(user_id, user_data)
        
        # 使用Markdown格式化欢迎信息
        welcome_text = MarkdownFormatter.format_welcome(user_name, user_data['spirit_stones'])
        
        yield event.plain_result(welcome_text)
    
    @filter.command("修仙信息")
    async def xiuxian_info(self, event: AstrMessageEvent):
        '''查看修仙信息'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        
        # 检查并完成状态，如果状态已结束则发放奖励
        status_completed = await self.check_and_complete_status(event, user_id, user_name)
        
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
        
        # 获取状态信息
        status_info = self.data_manager.check_status(user_id)
        
        # 使用Markdown格式化用户信息
        info_text = MarkdownFormatter.format_user_info(user_name, user_data, status_info)
        
        yield event.plain_result(info_text)
    
    @filter.command("修炼")
    async def xiuxian_practice(self, event: AstrMessageEvent, duration: str = "1"):
        '''修炼获取修为'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
        
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 解析修炼时间参数
        duration_hours = 1  # 默认1小时
        
        # 处理参数，支持"x小时"格式和纯数字格式
        if duration:
            # 移除可能的"小时"后缀
            duration = duration.replace("小时", "").strip()
            try:
                duration_hours = int(duration)
                # 限制在1-3小时之间
                duration_hours = max(1, min(3, duration_hours))
            except ValueError:
                pass
        
        # 设置修炼状态
        status_result = self.data_manager.set_status(user_id, "修炼中", duration_hours)
        
        if not status_result["success"]:
            yield event.plain_result(f"道友 {user_name}，{status_result['message']}")
            return
        
        # 计算结束时间的可读形式
        end_time = time.strftime("%H:%M:%S", time.localtime(status_result["end_time"]))
        
        # 使用Markdown格式化修炼开始信息
        result = MarkdownFormatter.format_practice_start(user_name, duration_hours, end_time)
        
        yield event.plain_result(result)
    
    @filter.command("修仙排行")
    async def xiuxian_rank(self, event: AstrMessageEvent):
        '''查看修仙排行榜'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        
        # 检查并完成状态，如果状态已结束则发放奖励
        status_completed = await self.check_and_complete_status(event, user_id, user_name)
        
        all_users = self.data_manager.get_all_users()
        
        # 按等级和经验排序
        sorted_users = sorted(all_users.items(), key=lambda x: (x[1]['level'], x[1]['exp']), reverse=True)
        
        # 使用Markdown格式化排行榜
        rank_text = MarkdownFormatter.format_rank(sorted_users)
        
        yield event.plain_result(rank_text)

    @filter.command("秘境探索")
    async def xiuxian_adventure(self, event: AstrMessageEvent, duration: str = "1"):
        '''秘境探索，获取奖励'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
        
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 解析探索时间参数
        duration_hours = 1  # 默认1小时
        
        # 处理参数，支持"x小时"格式和纯数字格式
        if duration:
            # 移除可能的"小时"后缀
            duration = duration.replace("小时", "").strip()
            try:
                duration_hours = int(duration)
                # 限制在1-3小时之间
                duration_hours = max(1, min(3, duration_hours))
            except ValueError:
                pass
        
        # 设置探索状态
        status_result = self.data_manager.set_status(user_id, "探索中", duration_hours)
        
        if not status_result["success"]:
            yield event.plain_result(f"道友 {user_name}，{status_result['message']}")
            return
        
        # 计算结束时间的可读形式
        end_time = time.strftime("%H:%M:%S", time.localtime(status_result["end_time"]))
        
        # 使用Markdown格式化探索开始信息
        result = MarkdownFormatter.format_adventure_start(user_name, duration_hours, end_time)
        
        yield event.plain_result(result)
    
    @filter.command("灵石收集")
    async def xiuxian_mine(self, event: AstrMessageEvent, duration: str = "1"):
        '''挖矿获取灵石'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
        
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 解析收集时间参数
        duration_hours = 1  # 默认1小时
        
        # 处理参数，支持"x小时"格式和纯数字格式
        if duration:
            # 移除可能的"小时"后缀
            duration = duration.replace("小时", "").strip()
            try:
                duration_hours = int(duration)
                # 限制在1-3小时之间
                duration_hours = max(1, min(3, duration_hours))
            except ValueError:
                pass
        
        # 设置收集灵石状态
        status_result = self.data_manager.set_status(user_id, "收集灵石中", duration_hours)
        
        if not status_result["success"]:
            yield event.plain_result(f"道友 {user_name}，{status_result['message']}")
            return
        
        # 计算结束时间的可读形式
        end_time = time.strftime("%H:%M:%S", time.localtime(status_result["end_time"]))
        
        # 构建回复消息
        result = MarkdownFormatter.format_mining_start(user_name, duration_hours, end_time)
        
        yield event.plain_result(result)
    
    @filter.command("修仙签到")
    async def xiuxian_daily(self, event: AstrMessageEvent):
        '''每日签到'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
            
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 调用数据管理器的签到方法
        result = self.data_manager.daily_sign(user_id)
        
        if not result["success"]:
            yield event.plain_result(f"道友 {user_name}，{result['message']}")
            return
        
        # 使用Markdown格式化签到信息
        formatted_message = MarkdownFormatter.format_daily_sign(user_name, result['message'])
        yield event.plain_result(formatted_message)
    
    @filter.command("修仙商店")
    async def xiuxian_shop(self, event: AstrMessageEvent):
        '''查看统一商店'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
            
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 获取可购买装备列表
        available_equipment = self.data_manager.get_available_equipment(user_id)
        # 获取可学习功法列表
        available_techniques = self.data_manager.get_available_techniques(user_id)
        # 获取可购买丹药列表
        available_pills = self.data_manager.get_available_pills(user_id)
        
        # 使用Markdown格式化商店信息
        message = MarkdownFormatter.format_shop(user_name, available_equipment, available_techniques, available_pills)
        
        yield event.plain_result(message)
    
    @filter.command("学习功法")
    async def xiuxian_learn(self, event: AstrMessageEvent, technique_name: str = ""):
        '''学习功法'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
            
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 检查参数
        if not technique_name:
            yield event.plain_result(f"道友 {user_name}，请指定要学习的功法名称。\n例如：/学习功法 吐纳术")
            return
        
        # 调用数据管理器的学习功法方法
        result = self.data_manager.learn_technique(user_id, technique_name)
        
        # 构建回复消息
        yield event.plain_result(f"道友 {user_name}，{result['message']}")
    
    @filter.command("购买装备")
    async def xiuxian_buy_equipment(self, event: AstrMessageEvent, equipment_id: str = ""):
        '''购买装备'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
            
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 检查参数
        if not equipment_id:
            yield event.plain_result(f"道友 {user_name}，请指定要购买的装备ID。\n例如：/购买装备 w1")
            return
        
        # 根据装备ID前缀确定装备类型
        equipment_type = ""
        if equipment_id.startswith("w"):
            equipment_type = "weapon"
        elif equipment_id.startswith("a"):
            equipment_type = "armor"
        elif equipment_id.startswith("ac"):
            equipment_type = "accessory"
        else:
            yield event.plain_result(f"道友 {user_name}，无效的装备ID。")
            return
        
        # 调用数据管理器的购买装备方法
        result = self.data_manager.buy_equipment(user_id, equipment_type, equipment_id)
        
        # 构建回复消息
        yield event.plain_result(f"道友 {user_name}，{result['message']}")
    
    @filter.command("购买丹药")
    async def xiuxian_buy_pill(self, event: AstrMessageEvent, pill_name: str = ""):
        '''购买丹药'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
            
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 检查参数
        if not pill_name:
            yield event.plain_result(f"道友 {user_name}，请指定要购买的丹药名称。\n例如：/购买丹药 渡厄丹")
            return
        
        # 调用数据管理器的购买丹药方法
        result = self.data_manager.buy_pill(user_id, pill_name)
        
        # 构建回复消息
        yield event.plain_result(f"道友 {user_name}，{result['message']}")
    
    @filter.command("使用丹药")
    async def xiuxian_use_pill(self, event: AstrMessageEvent, pill_name: str = ""):
        '''使用丹药'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
            
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 检查参数
        if not pill_name:
            yield event.plain_result(f"道友 {user_name}，请指定要使用的丹药名称。\n例如：/使用丹药 渡厄丹")
            return
        
        # 调用数据管理器的使用丹药方法
        result = self.data_manager.use_pill(user_id, pill_name)
        
        # 构建回复消息
        yield event.plain_result(f"道友 {user_name}，{result['message']}")
        
        # 显示
    
    @filter.command("修仙状态")
    async def xiuxian_status(self, event: AstrMessageEvent):
        '''查看当前状态'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
        
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}")
        else:
            yield event.plain_result(f"道友 {user_name}，你当前处于空闲状态，可以进行修炼、探索或收集灵石等活动。")
    
    @filter.command("切磋")
    async def xiuxian_duel(self, event: AstrMessageEvent, target_name: str = ""):
        '''与其他修仙者切磋'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
        
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 检查参数
        if not target_name:
            yield event.plain_result(f"道友 {user_name}，请指定要切磋的对象。\n例如：/切磋 张三")
            return
        
        # 查找目标用户
        target_id = None
        all_users = self.data_manager.get_all_users()
        for uid, data in all_users.items():
            if data.get("username") == target_name:
                target_id = uid
                break
        
        if not target_id:
            yield event.plain_result(f"道友 {user_name}，找不到名为 {target_name} 的修仙者。")
            return
        
        # 不能与自己切磋
        if target_id == user_id:
            yield event.plain_result(f"道友 {user_name}，你不能与自己切磋。")
            return
        
        # 调用数据管理器的切磋方法
        result = self.data_manager.duel(user_id, target_id)
        
        if not result["success"]:
            yield event.plain_result(f"道友 {user_name}，{result['message']}")
            return
        
        # 构建回复消息
        message = f"道友 {user_name} 与 {target_name} 切磋一番！\n"
        message += f"你的战力：{result['user_power']}\n"
        message += f"对方战力：{result['target_power']}\n\n"
        message += result["message"]
        
        yield event.plain_result(message)
    
    @filter.command("偷灵石")
    async def xiuxian_steal(self, event: AstrMessageEvent, target_name: str = ""):
        '''偷取其他修仙者的灵石'''
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
        
        # 检查用户当前状态
        status_info = self.data_manager.check_status(user_id)
        if status_info["has_status"]:
            yield event.plain_result(f"道友 {user_name}，{status_info['message']}，无法进行其他操作。")
            return
        
        # 检查参数
        if not target_name:
            yield event.plain_result(f"道友 {user_name}，请指定要偷取灵石的对象。\n例如：/偷灵石 张三")
            return
        
        # 查找目标用户
        target_id = None
        all_users = self.data_manager.get_all_users()
        for uid, data in all_users.items():
            if data.get("username") == target_name:
                target_id = uid
                break
        
        if not target_id:
            yield event.plain_result(f"道友 {user_name}，找不到名为 {target_name} 的修仙者。")
            return
        
        # 不能偷自己的灵石
        if target_id == user_id:
            yield event.plain_result(f"道友 {user_name}，你不能偷取自己的灵石。")
            return
        
        # 调用数据管理器的偷灵石方法
        result = self.data_manager.steal_spirit_stones(user_id, target_id)
        
        # 构建回复消息
        message = f"道友 {user_name} 悄悄接近 {target_name}，准备偷取灵石...\n\n"
        message += result["message"]
        
        yield event.plain_result(message)
    
    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''
        logger.info("修仙游戏插件已卸载")
