

from langchain_community.chat_models import ChatZhipuAI
from .settings import ZHIPUAI_API_KEY, ZHIPUAI_MODEL, TEMPERATURE, MAX_TOKENS


# 生成用LLM
llm_init = ChatZhipuAI(
    model=ZHIPUAI_MODEL,
    temperature=TEMPERATURE,
    api_key=ZHIPUAI_API_KEY
)
# 导出全局LLM实例
llm = llm_init

# ==================== 扩展：其他LLM 在此添加 ====================
# def get_other_llm():
#     pass