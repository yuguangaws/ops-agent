import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 智谱AI 配置 ====================
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "你的智谱API_KEY")
ZHIPUAI_MODEL = "glm-4"
TEMPERATURE = 0.1  # 运维场景低随机性
MAX_TOKENS = 2048

# ==================== 运维配置 ====================
ALARM_LEVELS = ["P0", "P1", "P2", "P3"]
HIGH_RISK_ACTIONS = ["删除数据", "下线节点", "修改防火墙", "全量重启"]