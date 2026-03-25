# 工业 AI 智能体决策服务（Flask + SQLite + 本地大模型）

这是一个面向工业应用场景的一站式服务网站，聚焦：
- 用户订单管理
- 生产排期可视化
- 仓库物料预警
- 本地大模型辅助决策

后端数据库为 **SQLite**，并支持接入本地大模型（默认兼容 Ollama API）。

## 核心能力

- 首页统一展示：订单 / 排期 / 物料数据
- `POST /api/ai/decision` 提供运营建议
- 自动读取数据库上下文（高优先级订单、低库存物料、延期风险）
- 本地模型不可用时自动降级为规则引擎建议

## 快速启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

访问 `http://127.0.0.1:5000`。

## 本地模型配置（可选）

通过环境变量配置模型接入：

```bash
export LOCAL_LLM_BASE_URL=http://127.0.0.1:11434
export LOCAL_LLM_MODEL=qwen2.5:7b
export LOCAL_LLM_TIMEOUT=20
```

如果本地模型服务不可达，接口会返回可执行的兜底策略建议。

## API

- `GET /api/overview`
  - 返回订单、排期、物料数据
- `POST /api/ai/decision`
  - 请求体：`{"question":"请给出排产建议"}`
  - 返回：问题、上下文统计、AI建议

## 测试

```bash
pytest -q
```
