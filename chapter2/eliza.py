import re
import random

# 上下文记忆：存储用户信息
user_memory = {
    "name": None,
    "age": None,
    "job": None
}

# 定义规则库: 模式(正则表达式) -> 响应模板列表
rules = {
    # 新增：提取姓名
    r'my name is (.*)|i am (.*)|i\'m (.*)': [
        "Nice to meet you, {0}!",
        "Hello {0}, how are you feeling today?",
        "Got it, your name is {0}."
    ],
    # 新增：提取年龄
    r'i am (\d+) years old|i\'m (\d+)|my age is (\d+)': [
        "So you're {0} years old. That's a great age!",
        "{0} years old, interesting! What do you do at your age?",
        "Thanks for sharing, you are {0} years old."
    ],
    # 新增：提取职业
    r'i am a (.*)|i work as a (.*)|my job is (.*)': [
        "So you work as {0} — that's cool!",
        "{0} sounds like an interesting job.",
        "Got it, you're a {0}."
    ],
    # 原有规则
    r'I need (.*)': [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?"
    ],
    r'Why don\'t you (.*)\?': [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?"
    ],
    r'Why can\'t I (.*)\?': [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?"
    ],
    r'I am (.*)': [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?"
    ],
    r'.* mother .*': [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?"
    ],
    r'.* father .*': [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?"
    ],
    r'.*': [
        "Please tell me more.",
        "Let's change focus a bit... Tell me about your family.",
        "Can you elaborate on that?"
    ]
}

# 代词转换
pronoun_swap = {
    "i": "you", "you": "i", "me": "you", "my": "your",
    "am": "are", "are": "am", "was": "were", "i'd": "you would",
    "i've": "you have", "i'll": "you will", "yours": "mine",
    "mine": "yours"
}

def swap_pronouns(phrase):
    """
    对输入短语中的代词进行第一/第二人称转换
    修复：如果 phrase 是 None，直接返回空字符串
    """
    if phrase is None:  # 关键修复
        return ''
    words = phrase.lower().split()
    swapped_words = [pronoun_swap.get(word, word) for word in words]
    return " ".join(swapped_words)

def extract_info(user_input):
    """从用户输入中提取姓名、年龄、职业并保存到记忆"""
    user_input = user_input.strip().lower()

    # 提取姓名
    name_match = re.search(r'my name is (.*)|i am ([a-z]+)|i\'m ([a-z]+)', user_input)
    if name_match:
        name = None
        for g in name_match.groups():
            if g and len(g) < 20:
                name = g.strip()
                break
        if name:
            user_memory["name"] = name.capitalize()

    # 提取年龄
    age_match = re.search(r'i am (\d+) years old|i\'m (\d+)|my age is (\d+)', user_input)
    if age_match:
        for g in age_match.groups():
            if g and g.isdigit():
                user_memory["age"] = g
                break

    # 提取职业
    job_match = re.search(r'i am a (.*)|i work as a (.*)|my job is (.*)', user_input)
    if job_match:
        job = None
        for g in job_match.groups():
            if g:
                job = g.strip()
                break
        if job:
            user_memory["job"] = job

def insert_memory(response):
    """在回复中自动插入记住的信息"""
    name = user_memory["name"]
    age = user_memory["age"]
    job = user_memory["job"]

    # 如果记住了姓名，随机在回复里带上名字
    if name and random.random() > 0.3:
        response = response.replace("!", f", {name}!")
        if "?" in response:
            response = response.replace("?", f", {name}?")
        if not name in response:
            response = f"{name}, " + response

    # 随机引用年龄或职业
    if age and random.random() > 0.5:
        response += f" By the way, you're {age} years old."
    if job and random.random() > 0.5:
        response += f" I remember you're a {job}."

    return response

def respond(user_input):
    # 先提取信息，更新记忆
    extract_info(user_input)

    for pattern, responses in rules.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            # 安全获取捕获组
            captured_group = match.group(1) if match.groups() else ''
            swapped_group = swap_pronouns(captured_group)
            # 格式化时如果没有内容，就不传参数
            try:
                response = random.choice(responses).format(swapped_group)
            except:
                response = random.choice(responses)
            # 插入记忆内容
            response = insert_memory(response)
            return response

    response = random.choice(rules[r'.*'])
    response = insert_memory(response)
    return response

# 主聊天循环
if __name__ == '__main__':
    print("Therapist: Hello! How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Therapist: Goodbye. It was nice talking to you.")
            break
        response = respond(user_input)
        print(f"Therapist: {response}")
# >>>
# Therapist: Hello! How can I help you today?
# You: I am feeling sad today.
# Therapist: How long have you been feeling sad today?
# You: I need some help with my project.
# Therapist: Are you sure you need some help with your project?
# You: My mother is not happy with my work.
# Therapist: Tell me more about your mother.
# You: quit
# Therapist: Goodbye. It was nice talking to you.