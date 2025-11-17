from mcp.server.fastmcp import FastMCP
import asyncio
import os
import json
import base64
import mimetypes
import logging
from urllib import request, error
from openai import OpenAI
from typing import Optional

# 配置日志
logger = logging.getLogger("mcp-ocr")
logger.setLevel(logging.INFO)

# 如果已经配置了处理器，避免重复添加
if not logger.handlers:
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器
    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "mcp_ocr_server.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# API 密钥配置
CREDENTIALS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".secrets")
CREDENTIALS_FILE = os.path.join(CREDENTIALS_DIR, "credentials.json")

# 文件大小限制（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_api_key_format(api_key: str) -> bool:
    """验证 API 密钥格式"""
    if not isinstance(api_key, str):
        return False
    if not (api_key.startswith("sk-") or api_key.startswith("ak-")):
        return False
    if len(api_key) < 16:
        return False
    if any(ch.isspace() for ch in api_key):
        return False
    return True


def get_api_key() -> Optional[str]:
    """获取 API 密钥（环境变量优先，其次配置文件）"""
    env_key = os.environ.get("MOONSHOT_API_KEY")
    if env_key and validate_api_key_format(env_key):
        return env_key
    
    # 尝试从配置文件读取
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                obj = json.load(f)
            k = obj.get("moonshot_api_key")
            if isinstance(k, str) and validate_api_key_format(k):
                return k
        except Exception:
            return None
    return None


def mask_key(api_key: str) -> str:
    """脱敏显示 API 密钥"""
    if not isinstance(api_key, str) or len(api_key) < 8:
        return "***"
    return f"{api_key[:4]}***{api_key[-4:]}"


class KimiFileOCR:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout_seconds: int | None = None) -> None:
        # 优先使用传入的 API 密钥，其次环境变量，最后配置文件
        self.api_key = api_key or os.environ.get("MOONSHOT_API_KEY") or self._get_api_key_from_config()
        self.base_url = (base_url or os.environ.get("KIMI_BASE_URL") or "https://api.moonshot.cn/v1").rstrip("/")
        self.timeout_seconds = int(timeout_seconds or os.environ.get("REQUEST_TIMEOUT_SECONDS", "30"))
        
        if not self.api_key:
            raise RuntimeError("missing MOONSHOT_API_KEY")
        
        logger.info(
            "KimiFileOCR init: api_key_present=%s masked_key=%s base_url=%s",
            bool(self.api_key),
            mask_key(self.api_key),
            self.base_url,
        )
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )
    
    def _get_api_key_from_config(self) -> str | None:
        """从配置文件获取 API 密钥"""
        return get_api_key()

    def extract_text_from_image(self, file_path: str) -> str:
        """使用 Kimi API 提取图片中的文字"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"file not found: {file_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"文件大小超过限制: {file_size} 字节 (最大支持 {MAX_FILE_SIZE} 字节，约10MB)")
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not mime_type.startswith("image/"):
            raise ValueError(f"not an image file: {file_path}")
        
        logger.info("extracting text from image: %s (size: %d bytes)", file_path, file_size)
        
        try:
            with open(file_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')

            response = self.client.chat.completions.create(
                model="kimi-latest",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{img_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "请提取图片中的所有文字内容"
                            }
                        ]
                    }
                ],
                max_tokens=2048,
            )
            
            result = response.choices[0].message.content or ""
            logger.info("text extraction completed: chars=%d", len(result))
            return result
            
        except error.HTTPError as e:
            logger.error("HTTP error: %s", e)
            raise RuntimeError(f"HTTP error: {e}")
        except error.URLError as e:
            logger.error("URL error: %s", e)
            raise RuntimeError(f"network error: {e}")
        except Exception as e:
            logger.error("unexpected error: %s", e)
            raise RuntimeError(f"unexpected error: {e}")

# 创建 FastMCP 服务器实例
mcp_server = FastMCP("mcp-ocr", "0.1.0")
ocr = KimiFileOCR()

@mcp_server.tool()
def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from image files using Kimi API

    :param file_path: Path to the image file
    :return: The extracted text
    """
    try:
        return ocr.extract_text_from_image(file_path)
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return f"Error: {str(e)}"


def main():
    """MCP 服务器主入口函数"""
    print("MCP OCR Server starting with FastMCP...")
    print("Available tool: extract_text_from_image")
    print("Waiting for connections...")
    
    # 运行 FastMCP 服务器（使用默认的 STDIO 传输）
    mcp_server.run()


if __name__ == "__main__":
    main()