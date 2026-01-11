import socket
import re
import os
import pandas as pd

# 配置代理环境变量
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'

PRODUCT_IDs_PATH = "C:/Users/jylau/Desktop/脚本/待翻译产品编号.txt"
EXCEL_PATH = "C:/Users/jylau/Desktop/脚本/产品翻译数据.xlsx"

def read_product_list():
    """
    简单读取文件，将逗号分隔的字符串转为字符串列表
    :param file_path: 文件路径
    :return: 分割后的字符串列表
    """
    # 打开文件并读取全部内容，去除首尾空白字符（换行、空格等）
    with open(PRODUCT_IDs_PATH, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    # 按逗号分割字符串，得到最终的列表
    product_list = content.split(',')
    return product_list

# 循环接收查询响应（支持超长消息）
def recv_all(sock, buffer_size=4096):
    """
    循环接收所有数据，直到服务器关闭连接
    :param sock: socket连接对象
    :param buffer_size: 每次接收的缓冲区大小
    :return: 完整的字节串响应数据
    """
    #end_marker = b'\xde\x08'
    
    end_marker = b'\xde\x08\x00'
    
    all_data = b""  # 初始化空字节串，用于拼接所有分段数据
    while True:
        chunk = sock.recv(buffer_size)  # 分段接收数据
        if not chunk:  # 收到空字节串，说明服务器关闭连接，接收完毕
            break
        all_data += chunk  # 拼接分段数据
        if all_data.endswith(end_marker):
            break
    return all_data

def pandas_append_to_excel(new_data):
    """用pandas+openpyxl实现Excel追加写入"""
    # 转换为DataFrame
    df_new = pd.DataFrame(new_data)
    
    if os.path.exists(EXCEL_PATH):
        # 文件存在：追加写入（不写表头）
        with pd.ExcelWriter(
            EXCEL_PATH,
            engine="openpyxl",
            mode="a",  # 追加模式
            if_sheet_exists="overlay"  # 覆盖已有工作表的末尾
        ) as writer:
            # 获取已有数据的最后一行，从下一行开始写入
            startrow = writer.sheets["产品数据"].max_row
            df_new.to_excel(writer, sheet_name="产品数据", startrow=startrow, index=False, header=False)
    else:
        # 文件不存在：新建并写入表头
        df_new.to_excel(EXCEL_PATH, sheet_name="产品数据", index=False)

def simulate_login():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        SERVER_IP = "47.106.171.116"
        SERVER_PORT = 7735
        sock.connect((SERVER_IP, SERVER_PORT))
        print("已建立连接，发送登录请求...")

        # 1. 请求产品详情的二进制字节流
        login_request = bytes.fromhex("4d40000000")
        inquiry_prefix_hex = "122f00004b8fb4b0d8271e448618528122ea7cd81f9d76d7b796b24b83a4da5012e909d60b73616c652e64657461696c02696409000000"
        product_ids = read_product_list() #["543131737"]
        print(f"产品编号列表:{product_ids}")
        for product_id in product_ids:
            # 2. 按id查询产品详情
            product_id_hex = product_id.encode("utf-8").hex()
            inquiry_request = bytes.fromhex(inquiry_prefix_hex + product_id_hex)

            # 3. 发送原始登录请求
            sock.sendall(login_request)

            # 4. 发送查询产品详情请求
            sock.sendall(inquiry_request)
            print(f"发送产品编号{product_id}查询请求...")

            # 5. 调用函数接收完整响应
            inquiry_response = recv_all(sock)

            # 解码为字符串（保留原有的ignore错误处理，避免编码问题导致崩溃）
            response_decode = inquiry_response.decode('utf-8', errors='ignore')

            # 6. 提取标题和描述内容（正则匹配完整的响应字符串）
            pattern = r'\{"es":"(.*?)"\}'  # 原正则表达式，匹配{"es":"内容"}格式
            es_list = re.findall(pattern, response_decode)
            # 核心：判断列表长度，不足则用空字符串填充
            title = es_list[0] if len(es_list) >= 1 else ''
            desc = es_list[1] if len(es_list) >= 2 else ''

            # 9. 写入Excel文件
            data = [{
                '产品编号': product_id,
                '原标题': title,
                '原描述': desc
            }]
            pandas_append_to_excel(data)

simulate_login()