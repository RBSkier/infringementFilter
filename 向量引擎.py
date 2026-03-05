import requests
import json

def call_api(
    url: str,
    method: str = "GET",
    params: dict = None,
    data: dict = None,
    headers: dict = None,
    timeout: int = 10
) -> dict:
    """
    通用的API接口调用函数
    
    Args:
        url: 接口地址
        method: 请求方法，支持GET/POST，默认GET
        params: GET请求的查询参数
        data: POST请求的请求体数据
        headers: 请求头信息
        timeout: 请求超时时间，默认10秒
    
    Returns:
        解析后的JSON响应数据（字典格式）
    
    Raises:
        Exception: 包含具体错误信息的异常
    """
    # 设置默认请求头（适配JSON接口）
    default_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer sk-NIshzWNsXSMZu2lFK7usicnZ1tspQHmpbyn4lWb8n8uqjZx6"
    }
    # 合并自定义请求头（自定义的会覆盖默认值）
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == "POST":
            # POST请求如果是JSON数据，用json参数自动序列化
            response = requests.post(
                url=url,
                params=params,  # POST也可带URL查询参数
                json=data,      # 自动序列化dict为JSON字符串
                headers=default_headers,
                timeout=timeout
            )
        else:
            raise ValueError(f"不支持的请求方法: {method}")
        
        # 检查HTTP状态码（非200系列直接抛出异常）
        response.raise_for_status()
        
        # 解析JSON响应（如果返回非JSON会抛出异常）
        result = response.json()
        print(f"接口调用成功，响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    
    # 捕获请求相关异常
    except requests.exceptions.Timeout:
        raise Exception(f"接口请求超时（{timeout}秒）: {url}")
    except requests.exceptions.ConnectionError:
        raise Exception(f"接口连接失败: {url}")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"接口返回错误状态码: {e.response.status_code}, 详情: {e.response.text}")
    except json.JSONDecodeError:
        raise Exception(f"接口返回非JSON格式数据: {response.text}")
    except Exception as e:
        raise Exception(f"接口调用未知错误: {str(e)}")

# -------------------------- 示例调用 --------------------------
if __name__ == "__main__":
    original_title = ""
    original_desc = ""
    prompt = f"""完成任务：
                    1. 规则：从待处理文本中提取需要剔除的内容，剔除范围：
                        ①从标题文本中剔除小品牌名称，但知名品牌或者ip无需剔除；
                        ②从标题文本中剔除前后缀上的一些无含义乱码；
                        ③从描述文本中剔除小品牌名称、保修天数、质保期限相关描述；
                        ④从描述文本中剔除发货时效、full仓发货描述（美客多平台的包邮政策、售后相关无需剔除）；
                        ⑤从描述文本中剔除带有mercadolibre.com域名的链接的引流信息；
                    2. 处理对象：同时分析【标题文本】和【描述文本】，分别提取各自需要剔除的内容。
                    3. 原标题中剔除掉第1点的内容后，重新生成一个最多60个字母的标题，要求与剔除后的标题有差异化，避免被平台收录为跟卖链接。
                    3. 输出要求：仅返回标准JSON字典，无其他多余文字，字典格式如下：
                        {{
                            "title_exclude": [标题中需剔除的内容1, 标题中需剔除的内容2,...],
                            "description_exclude": [描述中需剔除的内容1, 描述中需剔除的内容2,...],
                            "new_title": "剔除内容新生成的标题"
                        }}
                    若某一文本无需要剔除的内容，对应列表为空数组[]。
                    4. 待处理文本：
                        【标题文本】：{original_title}
                        【描述文本】：{original_desc}"""
    
    try:
        post_result = call_api(
            url="https://api.vectorengine.ai/v1/chat/completions",
            method="POST",
            # params={"token": "test123"},  # URL查询参数
            data={
                    "model": "doubao-seed-1-8-251228",
                    "messages": [
                        {
                        "role": "user",
                        "content": prompt
                        }
                    ],
                    "max_tokens": 10000
                }  # POST请求体
        )
        # 解析嵌套字段
        posted_data = post_result.get("json", {})
        username = posted_data.get("username")
        print(f"\n解析结果 - 提交的用户名: {username}")
    except Exception as e:
        print(f"POST请求失败: {e}")