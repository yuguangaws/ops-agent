import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 智谱AI 配置 ====================
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "你的智谱API_KEY")
ZHIPUAI_MODEL = "glm-3-turbo"
TEMPERATURE = 0.1  # 运维场景低随机性
MAX_TOKENS = 2048

# ==================== 运维配置 ====================
ALARM_LEVELS = ["P0", "P1", "P2", "P3"]
HIGH_RISK_ACTIONS = ["删除数据", "下线节点", "修改防火墙", "全量重启"]

# ==================== LangGraph Checkpoint 持久化配置（Postgres） ====================
# 用于持久化 human_approval 中断点的执行状态：进程重启/多副本部署后，
# 未审批完成的高危流程仍可通过 thread_id 找回并恢复执行。
# 对应 docker-compose.yml 里的 ops-agent-postgres 服务。
CHECKPOINT_PG_HOST = os.getenv("OPS_CHECKPOINT_PG_HOST", "localhost")
CHECKPOINT_PG_PORT = os.getenv("OPS_CHECKPOINT_PG_PORT", "5442")
CHECKPOINT_PG_USER = os.getenv("OPS_CHECKPOINT_PG_USER", "ops_agent")
CHECKPOINT_PG_PASSWORD = os.getenv("OPS_CHECKPOINT_PG_PASSWORD", "ops_agent")
CHECKPOINT_PG_DATABASE = os.getenv("OPS_CHECKPOINT_PG_DATABASE", "ops_agent_checkpoints")
CHECKPOINT_PG_URI = (
    f"postgresql://{CHECKPOINT_PG_USER}:{CHECKPOINT_PG_PASSWORD}"
    f"@{CHECKPOINT_PG_HOST}:{CHECKPOINT_PG_PORT}/{CHECKPOINT_PG_DATABASE}?sslmode=disable"
)