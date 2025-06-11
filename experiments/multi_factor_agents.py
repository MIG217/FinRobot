import re
import json
import autogen
from autogen.cache import Cache

# from finrobot.utils import create_inner_assistant

from functools import partial


config_list_gpt4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    # filter_dict={
    #     "model": ["gpt-4-0125-preview"],
    # },
)

llm_config = {
    "config_list": config_list_gpt4,
    "cache_seed": 42,
    "temperature": 0,
}

quant_group_config = json.load(open("/Users/mig217/FinRobot/experiments/quantitative_investment_group_config.json"))

# user_proxy = autogen.UserProxyAgent(
#     name="User",
#     # human_input_mode="ALWAYS",
#     human_input_mode="NEVER",
#     code_execution_config=False
# )

group_descs = "\n\n".join(
    [
        "Name: {} \nResponsibility: {}".format(c["name"], c["profile"])
        for c in quant_group_config
    ]
)

group_leader = autogen.AssistantAgent(
    name="Group_Leader",
    system_message="""
    作为小组组长，你负责协调团队的工作，以实现项目的目标。
    你必须确保团队高效、协同地工作。
    每次回复时，都要总结整个项目的进展情况，并为其中一位组员分配任务以推进项目进程。
    指令应遵循以下格式：“[<成员姓名>] <指令内容>”，并出现在你回复的末尾。
    在收到团队成员的反馈后，检查任务的进展情况，并确保任务在继续下一项指令之前已被良好完成。
    如果任务未被良好完成，你的指令应为提供协助与指导，帮助团队成员重新完成该任务。
    仅当整个项目完成时，才回复 TERMINATE。
    你的团队成员如下：\n\n
    """
    + group_descs,
    llm_config=llm_config,
)

executor = autogen.UserProxyAgent(
    name="Executor",
    human_input_mode="NEVER",
    # human_input_mode="ALWAYS",
    is_termination_msg=lambda x: x.get("content", "")
    and "TERMINATE" in x.get("content", ""),
    # max_consecutive_auto_reply=3,
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "quant",
        "use_docker": False,
    },
)

quant_group = {
    c["name"]: autogen.agentchat.AssistantAgent(
        name=c["name"],
        system_message=c["profile"],
        llm_config=llm_config,
    )
    for c in quant_group_config
}


def order_trigger(pattern, sender):
    # print(pattern)
    # print(sender.last_message()['content'])
    return pattern in sender.last_message()["content"]


def order_message(pattern, recipient, messages, sender, config):
    full_order = recipient.chat_messages_for_summary(sender)[-1]["content"]
    pattern = rf"\[{pattern}\](?::)?\s*(.+?)(?=\n\[|$)"
    match = re.search(pattern, full_order, re.DOTALL)
    if match:
        order = match.group(1).strip()
    else:
        order = full_order
    return f"""
    请遵循组长的指令并完成以下任务：{order}。
    对于编程任务，请提供 Python 脚本，由执行器为你运行。
    请将你的结果或任何中间数据保存在本地，并告知组长如何读取这些内容。
    在尚未获得 Python 脚本执行结果之前，**请不要**在回复中包含 TERMINATE。
    如果当前无法完成任务，或者需要其他成员的协助，请向组长报告原因或需求，并以 TERMINATE 结尾。
    """
    # For coding tasks, only use the functions you have been provided with.


for name, agent in quant_group.items():
    executor.register_nested_chats(
        [
            {
                "sender": executor,
                "recipient": agent,
                "message": partial(order_message, name),
                "summary_method": "reflection_with_llm",
                "max_turns": 10,
                "max_consecutive_auto_reply": 3,
            }
        ],
        trigger=partial(order_trigger, f"[{name}]"),
    )

quant_task = """
开发并测试一个量化投资策略的可行性，该策略聚焦于道琼斯30指数成分股。利用你的多因子分析专业知识，识别潜在的投资机会，并优化投资组合的表现。
确保该策略具有稳健性、以数据为驱动，并符合我们的风险管理原则。
"""

with Cache.disk() as cache:
    executor.initiate_chat(group_leader, message=quant_task, cache=cache)
