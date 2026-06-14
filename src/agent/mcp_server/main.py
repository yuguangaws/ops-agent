from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
from .registry import MCP_TOOLS_REGISTRY
from .tools import *  # 导入所有工具，触发自动注册

app = FastAPI(title="本地MCP运维服务")

# 统一请求体
class McpRequest(BaseModel):
    tool: str
    params: dict[str, Any]

# 统一调用接口
@app.post("/api/mcp/call")
def mcp_call(request: McpRequest):
    tool_func = MCP_TOOLS_REGISTRY.get(request.tool)
    if not tool_func:
        return {
            "code": -1,
            "msg": f"工具 [{request.tool}] 不存在，当前可用工具：{list(MCP_TOOLS_REGISTRY.keys())}",
            "data": None
        }

    try:
        result = tool_func(request.params)
        return {"code": 0, "msg": "success", "data": result}
    except Exception as e:
        return {"code": -2, "msg": f"工具执行异常：{str(e)}", "data": None}


if __name__ == "__main__":
    import uvicorn
    print(f"已注册MCP工具：{list(MCP_TOOLS_REGISTRY.keys())}")
    uvicorn.run(app, host="0.0.0.0", port=8080)