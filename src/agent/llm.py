from langchain_zhipu import ChatZhipuAI
from setting import ZHIPUAI_API_KEY, ZHIPUAI_MODEL, TEMPERATURE, MAX_TOKENS

# ==================== 智谱AI 大模型（单例） ====================
def get_zhipu_llm():
    """获取智谱AI LLM实例"""
    return ChatZhipuAI(
        api_key=ZHIPUAI_API_KEY,
        model=ZHIPUAI_MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )

# 导出全局LLM实例
llm = get_zhipu_llm()

# ==================== 扩展：其他LLM 在此添加 ====================
# def get_other_llm():
#     pass