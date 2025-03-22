from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import MessageChain, At, Plain
import os
import time
import asyncio
from .xiuxian_data import XiuXianData
from .markdown_formatter import MarkdownFormatter
from .utils import XiuXianUtils

@register("xiuxian", "修仙游戏", "一个简单的修仙游戏插件", "1.0.0")
class XiuXianPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化数据管理器
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(plugin_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_manager = XiuXianData(data_dir)
        
        # 存储用户状态任务的字典
        self.user_status_tasks = {}
        logger.info("修仙插件已启动")
    
    @filter.command("修仙帮助")
    async def xiuxian_help(self, event: AstrMessageEvent):
        '''修仙游戏帮助指令'''
        help_text = """【修仙游戏指令】
                    /我要修仙 - 开始修仙之旅
                    /修仙帮助 - 显示帮助
                    /修炼 [时间] - 闭关修炼获取修为，可指定时间（如：2小时30分钟，最长6小时）
                    /修仙信息 - 查看修仙信息
                    /修仙排行 - 查看排行榜
                    /秘境探索 [时间] - 探索秘境获奖励，可指定时间（如：3小时45分钟，最长6小时）
                    /灵石收集 [时间] - 获取灵石，可指定时间（如：1小时15分钟，最长6小时）
                    /修仙状态 - 查看当前状态
                    /修仙签到 - 每日签到
                    /突破 - 尝试突破到更高境界
                    /突破信息 - 查看突破相关信息
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
        
        user_data = self.data_manager.get_user(user_id)
        
        # 检查用户是否已经开始修仙
        if not user_data.get("has_started", False):
            yield event.plain_result(f"道友 {user_name}，你尚未踏上修仙之路，请先输入 /我要修仙 开始你的修仙之旅。")
            return
        
        # 获取状态信息
        status_info = self.data_manager.check_status(user_id)
        
        # 获取所有装备信息
        all_equipment = self.data_manager.get_equipment_list()
        
        # 使用Markdown格式化用户信息
        info_text = MarkdownFormatter.format_user_info(user_name, user_data, all_equipment, status_info)
        
        yield event.plain_result(info_text)
        
    @filter.command("突破信息")
    async def xiuxian_breakthrough_info(self, event: AstrMessageEvent):
        '''查看突破信息'''
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
        
        # 获取下一境界信息
        next_realm_info = self.data_manager.get_next_realm(user_id)
        next_realm_info["current_realm"] = user_data["realm"]
        
        # 格式化突破信息
        formatted_info = MarkdownFormatter.format_breakthrough_info(user_name, next_realm_info)
        
        yield event.plain_result(formatted_info)
    
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
        
        # 使用工具类解析修炼时间参数
        duration_hours = XiuXianUtils.parse_duration(duration)
        
        # 设置修炼状态
        status_result = self.data_manager.set_status(user_id, "修炼中", duration_hours)
        duration_hours = status_result["duration"]  # 更新 duration_hours 为实际的小时数，而不是传入的
        
        if not status_result["success"]:
            yield event.plain_result(f"道友 {user_name}，{status_result['message']}")
            return
        
        # 存储消息ID
        unified_msg_origin = event.unified_msg_origin
        
        # 创建针对该用户的定时任务
        self.create_user_status_task(user_id, user_name, status_result["end_time"], unified_msg_origin)
        
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
        
        all_users = self.data_manager.get_all_users()
        
        # 按等级和修为排序
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
        
        # 使用工具类解析探索时间参数
        duration_hours = XiuXianUtils.parse_duration(duration)
        
        # 设置探索状态
        status_result = self.data_manager.set_status(user_id, "探索中", duration_hours)
        duration_hours = status_result["duration"]  # 更新 duration_hours 为实际的小时数，而不是传入的
        
        # 存储消息ID
        unified_msg_origin = event.unified_msg_origin
        
        if not status_result["success"]:
            yield event.plain_result(f"道友 {user_name}，{status_result['message']}")
            return
        
        # 创建针对该用户的定时任务
        self.create_user_status_task(user_id, user_name, status_result["end_time"], unified_msg_origin)
        
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
        
        # 使用工具类解析收集时间参数
        duration_hours = XiuXianUtils.parse_duration(duration)
        
        # 设置收集灵石状态
        status_result = self.data_manager.set_status(user_id, "收集灵石中", duration_hours)
        duration_hours = status_result["duration"]  # 更新 duration_hours 为实际的小时数，而不是传入的
        
        if not status_result["success"]:
            yield event.plain_result(f"道友 {user_name}，{status_result['message']}")
            return
        
        # 存储消息ID
        unified_msg_origin = event.unified_msg_origin
        
        # 创建针对该用户的定时任务
        self.create_user_status_task(user_id, user_name, status_result["end_time"], unified_msg_origin)
        
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
        elif equipment_id.startswith("ac"):
            equipment_type = "accessory"
        elif equipment_id.startswith("a"):
            equipment_type = "armor"
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
    
    @filter.command("突破")
    async def xiuxian_breakthrough(self, event: AstrMessageEvent, use_pill: str = ""):
        '''尝试突破到更高境界'''
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
        
        # 获取下一境界信息
        next_realm_info = self.data_manager.get_next_realm(user_id)
        
        # 检查是否有下一境界
        if not next_realm_info["has_next"]:
            yield event.plain_result(f"道友 {user_name}，{next_realm_info['message']}")
            return
        
        # 检查CD时间
        if next_realm_info["cd_remaining"] > 0:
            minutes = next_realm_info["cd_remaining"] // 60
            seconds = next_realm_info["cd_remaining"] % 60
            yield event.plain_result(f"道友 {user_name}，突破冷却中，需等待 {minutes}分{seconds}秒")
            return
        
        # 检查修为是否足够
        if not next_realm_info["can_breakthrough"]:
            yield event.plain_result(f"道友 {user_name}，修为不足，无法突破。当前修为：{next_realm_info['current_exp']}，需要：{next_realm_info['exp_required']}")
            return
        
        # 检查是否使用渡厄丹
        use_pill_bool = False
        if use_pill and "渡厄丹" in use_pill:
            # 检查用户是否有渡厄丹
            if "渡厄丹" not in user_data.get("inventory", {}).get("pills", {}) or user_data["inventory"]["pills"]["渡厄丹"] <= 0:
                yield event.plain_result(f"道友 {user_name}，你没有渡厄丹，无法使用。")
                return
            # 减少一个渡厄丹
            user_data["inventory"]["pills"]["渡厄丹"] -= 1
            self.data_manager.update_user(user_id, user_data)
            use_pill_bool = True
        
        # 尝试突破
        result = self.data_manager.breakthrough(user_id, use_pill_bool)
        
        # 格式化突破结果
        formatted_result = MarkdownFormatter.format_breakthrough_result(user_name, result)
        
        yield event.plain_result(formatted_result)
    
    @filter.command("切磋")
    async def xiuxian_duel(self, event: AstrMessageEvent):
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

        # 解析@目标
        target_id = self.parse_at_target(event)
        if not target_id:
            yield event.plain_result(f"道友 {user_name}，请指定要切磋的对象。\n例如：@张三")
            return
        
        # 查找目标用户
        all_users = self.data_manager.get_all_users()
        
        if target_id not in all_users:
            yield event.plain_result(f"道友 {user_name}，找不到这位修仙者。")
            return
        
        # 不能与自己切磋
        if target_id == user_id:
            yield event.plain_result(f"道友 {user_name}，你不能与自己切磋。")
            return
        
        target_name = all_users[target_id]["username"]
        
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
    async def xiuxian_steal(self, event: AstrMessageEvent):
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
        target_id = self.parse_at_target(event)
        if not target_id:
            yield event.plain_result(f"道友 {user_name}，请指定要偷取灵石的对象。\n例如：@张三")
            return
        
        # 查找目标用户
        all_users = self.data_manager.get_all_users()

        if target_id not in all_users:
            yield event.plain_result(f"道友 {user_name}，找不到这位修仙者。")
            return
        
        # 不能偷自己的灵石
        if target_id == user_id:
            yield event.plain_result(f"道友 {user_name}，你不能偷取自己的灵石。")
            return

        target_name = all_users[target_id]["username"]
        
        # 调用数据管理器的偷灵石方法
        result = self.data_manager.steal_spirit_stones(user_id, target_id)
        
        # 构建回复消息
        message = f"道友 {user_name} 悄悄接近 {target_name}，准备偷取灵石...\n\n"
        message += result["message"]
        
        yield event.plain_result(message)
    
    def parse_at_target(self, event):
        """解析@目标"""
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                return str(comp.qq)
        return None
    
    def create_user_status_task(self, user_id: str, user_name: str, end_time: int, unified_msg_origin=None):
        '''为用户创建状态检查任务'''
        # 使用工具类生成唯一的任务ID
        status_type = self.data_manager.get_user(user_id).get("status", "未知")
        task_id = XiuXianUtils.generate_task_id(user_id, status_type)
        
        # 如果用户已有任务，先取消
        for existing_id, task_info in list(self.user_status_tasks.items()):
            if task_info["user_id"] == user_id and not task_info["task"].done():
                task_info["task"].cancel()
                del self.user_status_tasks[existing_id]
                logger.info(f"已取消用户 {user_name}({user_id}) 的旧状态任务 {existing_id}")
        
        # 计算等待时间（秒）
        wait_time = max(0, end_time - int(time.time()))
        
        # 创建新任务
        task = asyncio.create_task(
            self.check_user_status_task(user_id, user_name, wait_time, unified_msg_origin)
        )
        
        # 设置任务完成回调，确保任务完成后从字典中移除
        task.add_done_callback(lambda t: self._cleanup_task(task_id, user_id, user_name))
        
        # 存储任务信息
        self.user_status_tasks[task_id] = {
            "user_id": user_id,
            "task": task,
            "end_time": end_time,
            "status_type": status_type
        }
        
        logger.info(f"已为用户 {user_name}({user_id}) 创建状态任务 {task_id}，将在 {wait_time} 秒后完成")
    
    def _cleanup_task(self, task_id: str, user_id: str, user_name: str):
        '''清理已完成的任务'''
        if task_id in self.user_status_tasks:
            del self.user_status_tasks[task_id]
            logger.info(f"用户 {user_name}({user_id}) 的状态任务 {task_id} 已从任务字典中移除")
    
    async def check_user_status_task(self, user_id: str, user_name: str, wait_time: int, unified_msg_origin):
        '''异步任务：等待指定时间后检查用户状态并发放奖励'''
        try:
            # 等待到状态结束时间
            await asyncio.sleep(wait_time + 5)
            
            # 获取用户数据
            user_data = self.data_manager.get_user(user_id)
            logger.info(f"开始检查用户 {user_name}({user_id}) 的状态")
            
            # 检查用户是否仍有状态
            if user_data.get("status") is not None:
                # 完成状态并获取奖励
                result = self.data_manager.complete_status(user_id)
                logger.info(f"用户 {user_name}({user_id}) 的状态已完成")
                logger.info(f"用户 {user_name}({user_id}) 的状态奖励：{result}")
                
                # 如果状态完成成功
                if result["success"]:
                    # 构建消息链，@用户并发送奖励消息
                    message_chain = MessageChain([
                        At(qq=user_id),
                        Plain(f" 道友 {user_name}，{result['message']}")
                    ])
                    
                    logger.info(f"开始向用户 {user_name}({user_id}) 发送状态完成通知")
                    try:
                        # 尝试发送消息
                        await self.context.send_message(unified_msg_origin, message_chain)
                        logger.info(f"已向用户 {user_name}({user_id}) 发送状态完成通知")
                    except Exception as e:
                        logger.error(f"向用户 {user_name}({user_id}) 发送状态完成通知失败: {e}")
        
        except asyncio.CancelledError:
            # 任务被取消
            logger.info(f"用户 {user_name}({user_id}) 的状态任务被取消")
        except Exception as e:
            logger.error(f"用户 {user_name}({user_id}) 的状态任务出错: {e}")
        # 注意：不需要在finally中清理任务，因为已经通过done_callback处理
    
    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''
        # 取消所有用户状态任务
        if hasattr(self, 'user_status_tasks'):
            for task_id, task_info in list(self.user_status_tasks.items()):
                task = task_info["task"]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"取消任务 {task_id} 时出错: {e}")
            self.user_status_tasks.clear()
            logger.info("所有修仙状态任务已清理完毕")
        
        logger.info("修仙游戏插件已卸载")
