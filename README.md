# 文档格式转换服务

一个基于 Flask 的 Web 页面服务：上传文档后可转换为 **PDF / Word / Markdown** 并直接下载。

## 功能

- 支持上传：`txt`、`md`、`docx`、`pdf`
- 支持转换目标：
  - PDF（`.pdf`）
  - Word（`.docx`）
  - Markdown（`.md`）

> 当前实现以文本内容提取+重建方式转换，复杂排版（表格、图片、样式）可能丢失。

## 运行方式

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

打开 `http://127.0.0.1:5000` 即可使用。

## 测试

```bash
source .venv/bin/activate
pytest -q
```

## Demo（自动化演示）

可直接运行脚本完成依赖安装 + 接口调用演示：

```bash
bash scripts/demo.sh
```

脚本会通过 Flask `test_client()` 执行：
- `GET /` 首页连通性检查
- `POST /convert` 的 txt -> markdown 转换示例

## 安装失败排查

如果你在受限网络环境中遇到 `pip install` 失败（例如代理 403 / 无法联网），可优先检查：

1. 是否需要设置企业内部 PyPI 源（`PIP_INDEX_URL`）。
2. 当前代理配置是否可访问 Python 包源。
3. 证书链是否正确（如 `PIP_CERT`、`REQUESTS_CA_BUNDLE`）。
