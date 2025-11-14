#!/usr/bin/env python3
"""
MCP 服务器连接测试脚本
用于验证 MCP 服务器是否能够正常启动和响应请求
"""

import subprocess
import sys
import json
import time

def test_mcp_server():
    """测试 MCP 服务器连接"""
    
    # 启动 MCP 服务器进程
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.mcp_ocr_server.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # 发送初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                },
                "capabilities": {}
            }
        }
        
        # 发送请求
        server_process.stdin.write(json.dumps(init_request) + "\n")
        server_process.stdin.flush()
        
        # 等待响应
        time.sleep(1)
        
        # 读取响应
        response = server_process.stdout.readline()
        print(f"服务器响应: {response}")
        
        # 检查进程状态
        if server_process.poll() is not None:
            stderr_output = server_process.stderr.read()
            print(f"服务器已退出，错误输出: {stderr_output}")
            return False
        
        return True
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False
    finally:
        # 清理进程
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    print("开始测试 MCP 服务器连接...")
    success = test_mcp_server()
    if success:
        print("✓ MCP 服务器连接测试成功")
        sys.exit(0)
    else:
        print("✗ MCP 服务器连接测试失败")
        sys.exit(1)