# MCP OCR Server

基于 Kimi API 的 Model Context Protocol (MCP) OCR 服务器，提供图片文字提取功能。

## 1. 功能特性

- ✅ 图片文字提取：支持 PNG、JPG 等常见图片格式
- ✅ MCP 1.21.0 协议：使用最新的 FastMCP 实现
- ✅ 高性能：异步处理，支持并发请求
- ✅ 完整日志：控制台和文件双重日志输出
- ✅ 配置灵活：支持环境变量和配置文件两种方式
- ✅ 测试完备：包含完整的测试脚本和测试用例

---

## 2. 项目结构

```text
mcp-ocr/
├── src/
│   └── mcp_ocr_server/
│       ├── __init__.py          # 模块导出
│       └── mcp_server.py        # MCP 服务器主文件
├── config/
│   └── mcp_ocr_config.json      # MCP 客户端配置
├── scripts/
│   └── run_tests.py             # 测试脚本
├── test/
│   ├── 1..png                   # 测试图片 1
│   └── 2..png                   # 测试图片 2
├── logs/                        # 日志目录 (自动创建)
├── .secrets/                    # 密钥目录 (自动创建)
├── requirements.txt             # Python 依赖
├── README.md                    # 项目说明
└── LICENSE                      # 开源协议
```

---

## 3. 快速开始

### 3.1 安装依赖

```bash
pip install -r requirements.txt
```

### 3.2 配置 API 密钥

选择以下任一方式配置 Kimi API 密钥：

**方式一：环境变量**:

```bash
export MOONSHOT_API_KEY="sk-your-api-key-here"
```

**方式二：配置文件**:

```bash
mkdir -p .secrets
echo '{"api_key": "sk-your-api-key-here"}' > .secrets/credentials.json
```

### 3.3 运行测试

```bash
python scripts/run_tests.py
```

### 3.4 启动 MCP 服务器

```bash
python -m src.mcp_ocr_server.mcp_server
```

---

## 4. MCP 工具

从图片文件中提取文字内容。

**参数：**

- `file_path` (string): 图片文件路径

**返回值：**

- 提取的文字内容 (string)

**示例：**

```json
{
  "method": "extract_text_from_image",
  "params": {
    "file_path": "/path/to/image.png"
  }
}
```

---

## 5. 配置说明

### 5.1 环境变量

| **变量名**                | **默认值**                   | **说明**           |
| ------------------------- | ---------------------------- | ------------------ |
| `MOONSHOT_API_KEY`        | -                            | Kimi API 密钥      |
| `KIMI_BASE_URL`           | `https://api.moonshot.cn/v1` | Kimi API 基础地址  |
| `REQUEST_TIMEOUT_SECONDS` | `10`                         | 请求超时时间（秒） |

### 5.2 配置文件

配置文件位于 `.secrets/credentials.json`：

```json
{
  "api_key": "sk-your-api-key-here"
}
```

---

## 6. 开发指南

### 6.1 测试

测试脚本：

```bash
python scripts/run_tests.py
```

### 6.2 日志

日志文件位于 `logs/mcp_ocr_server.log`。

---
