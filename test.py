import requests
import json

def get_ollama_response(prompt, model='llama2'):
    # Ollama API端点
    url = 'http://127.0.0.1:11434/api/generate'

    # 准备请求数据
    data = {
        'model': model,
        'prompt': prompt,
        'stream': False  # 设置为False以获取完整响应
    }

    try:
        # 发送POST请求
        response = requests.post(url, json=data)
        response.raise_for_status()  # 检查请求是否成功

        # 解析响应
        result = response.json()
        return result['response']

    except requests.exceptions.RequestException as e:
        print(f'请求错误: {e}')
        return None
    except json.JSONDecodeError as e:
        print(f'JSON解析错误: {e}')
        return None

# 使用示例
prompt = '你好，请介绍一下你自己'
response = get_ollama_response(prompt)
if response:
    print('模型回复:', response)