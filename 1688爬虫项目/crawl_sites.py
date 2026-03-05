from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import json
import re

def crawl_from_1688(url):
    # ========== 核心：加载已登录账户的配置文件 ==========
    edge_options = webdriver.EdgeOptions()
    # 1. 父目录：User Data（复制的路径去掉最后的 Default/Profile 1）
    user_data_dir = r"C:\Users\jylau\AppData\Local\Microsoft\Edge\User Data"
    # 2. 子目录：对应你登录账户的文件夹（Default/Profile 1 等）
    profile_dir = "Default"  # 若你的账户是 Profile 1，改为 "Profile 1"
    
    # 添加参数：加载用户配置文件（必须！）
    edge_options.add_argument(f"--user-data-dir={user_data_dir}")
    edge_options.add_argument(f"--profile-directory={profile_dir}")

    # 基础配置（保留反爬，但无需手动加 Cookie）
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('--disable-dev-shm-usage')
    edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0')
    edge_options.add_argument('--lang=zh-CN')
    edge_options.add_argument('--disable-features=WebRTC,AutomationControlled')
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument('--window-size=1920,1080')
    edge_options.add_argument('blink-settings=imagesEnabled=true')

    # 指定驱动路径
    service = Service(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe')
    driver = None
    product_data = {
        "商品标题": "",
        "最低价格": "",
        "最高价格": "",
        "起批量": "",
        "销量": "",
        "发货地": "",
        "商品编号": "",
        "运费说明": "",
        "主图链接列表": [],
        "详情图链接列表": [],
        "核心属性": {},
        "SKU规格价格": {},
        "店铺名称": "",
        "抓取时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }

    try:
        # 初始化驱动（自动复用登录账户）
        driver = webdriver.Edge(service=service, options=edge_options)
        
        # 指纹伪装（保留，避免反爬）
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': r'''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'AutomationControlled', {get: () => false});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [{name: 'Microsoft Edge PDF Viewer', filename: 'microsoft-edge-pdf-viewer'}]
                });
            '''
        })

        # ========== 无需手动加 Cookie！配置文件里已有登录态 ==========
        # 直接访问1688商品页（自动携带登录账户的Cookie）
        driver.get(url)
        # 等待页面加载，检测验证码
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        # 验证码兜底（若触发，手动完成）
        if '验证码' in driver.page_source or 'captcha' in driver.current_url.lower():
            print("⚠️ 触发验证码！请在浏览器中完成验证，完成后按回车继续...")
            input()

        time.sleep(random.uniform(3, 5))

        # 验证是否复用了登录账户（查看1688是否已登录）
        print("✅ 页面标题：", driver.title)

        # ========== 1. 提取商品标题 ==========
        try:
            title_elem = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.title'))
            )
            product_data["商品标题"] = title_elem.text.strip()
            print(f"\n📌 商品标题：{product_data['商品标题']}")
        except:
            try:
                title_elem = driver.find_element(By.CLASS_NAME, 'title-text')
                product_data["商品标题"] = title_elem.text.strip()
                print(f"\n📌 商品标题：{product_data['商品标题']}")
            except:
                print("⚠️ 商品标题提取失败")

        # ========== 2. 提取价格和起批量信息 ==========
        try:
            # 价格区间
            price_elem = driver.find_element(By.CSS_SELECTOR, 'div.price-container .price')
            price_text = price_elem.text.strip().replace('¥', '')
            if '-' in price_text:
                price_range = price_text.split('-')
                product_data["最低价格"] = price_range[0].strip()
                product_data["最高价格"] = price_range[1].strip()
            else:
                product_data["最低价格"] = price_text
                product_data["最高价格"] = price_text
            
            # 起批量
            moq_elem = driver.find_element(By.CSS_SELECTOR, 'div.price-container .moq')
            moq_text = re.sub(r'[^\d]', '', moq_elem.text.strip())
            product_data["起批量"] = moq_text
            
            print(f"💰 价格区间：¥{product_data['最低价格']} - ¥{product_data['最高价格']}")
            print(f"📦 起批量：{product_data['起批量']}件起批")
        except:
            print("⚠️ 价格/起批量提取失败")

        # ========== 3. 提取销量信息 ==========
        try:
            # 多种销量选择器兼容
            sales_selectors = [
                '.sales-volume', 
                '.transaction-data .sales',
                '[data-spm="daili_sales"]'
            ]
            sales_text = ""
            for selector in sales_selectors:
                try:
                    sales_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    sales_text = sales_elem.text.strip()
                    if sales_text:
                        break
                except:
                    continue
            
            # 提取数字
            sales_num = re.findall(r'(\d+(?:\.\d+)?)万?', sales_text)
            if sales_num:
                if '万' in sales_text:
                    product_data["销量"] = f"{float(sales_num[0]) * 10000:.0f}"
                else:
                    product_data["销量"] = sales_num[0]
            print(f"📈 销量：{product_data['销量']}件")
        except:
            print("⚠️ 销量提取失败")

        # ========== 4. 提取发货地 ==========
        try:
            location_elem = driver.find_element(By.CSS_SELECTOR, '.delivery-address, .address')
            location_text = location_elem.text.strip().replace('发货地：', '').replace('产地：', '')
            product_data["发货地"] = location_text
            print(f"📍 发货地：{product_data['发货地']}")
        except:
            print("⚠️ 发货地提取失败")

        # ========== 5. 提取商品编号 ==========
        try:
            # 从URL提取商品编号
            product_id_match = re.search(r'offer/(\d+)\.html', url)
            if product_id_match:
                product_data["商品编号"] = product_id_match.group(1)
            else:
                # 从页面提取
                id_elem = driver.find_element(By.XPATH, '//*[contains(text(), "商品编号")]/following-sibling::span')
                product_data["商品编号"] = id_elem.text.strip()
            print(f"🆔 商品编号：{product_data['商品编号']}")
        except:
            print("⚠️ 商品编号提取失败")

        # ========== 6. 提取运费说明 ==========
        try:
            freight_elem = driver.find_element(By.CSS_SELECTOR, '.freight, .transport-price')
            product_data["运费说明"] = freight_elem.text.strip()
            print(f"🚚 运费说明：{product_data['运费说明']}")
        except:
            print("⚠️ 运费说明提取失败")

        # ========== 7. 提取主图链接 ==========
        try:
            main_img_elems = driver.find_elements(By.CSS_SELECTOR, '.thumb-image img, .item-img img')
            for img_elem in main_img_elems:
                img_src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
                if img_src and 'http' in img_src:
                    # 处理图片尺寸参数，获取原图
                    img_src = re.sub(r'@\d+x\d+', '', img_src)
                    product_data["主图链接列表"].append(img_src)
            # 去重
            product_data["主图链接列表"] = list(set(product_data["主图链接列表"]))
            print(f"🖼️ 主图数量：{len(product_data['主图链接列表'])}")
            for i, img_url in enumerate(product_data["主图链接列表"], 1):
                print(f"   主图{i}：{img_url}")
        except:
            print("⚠️ 主图链接提取失败")

        # ========== 8. 提取详情图链接 ==========
        try:
            # 滚动到详情区域
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5);")
            time.sleep(2)
            
            detail_img_elems = driver.find_elements(By.CSS_SELECTOR, '.detail-content img, .desc-lazyload img')
            for img_elem in detail_img_elems:
                img_src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
                if img_src and 'http' in img_src and '1688.com' in img_src:
                    img_src = re.sub(r'@\d+x\d+', '', img_src)
                    product_data["详情图链接列表"].append(img_src)
            # 去重
            product_data["详情图链接列表"] = list(set(product_data["详情图链接列表"]))
            print(f"📄 详情图数量：{len(product_data['详情图链接列表'])}")
        except:
            print("⚠️ 详情图链接提取失败")

        # ========== 9. 提取核心属性 ==========
        try:
            attr_elems = driver.find_elements(By.CSS_SELECTOR, '.attributes-list li, .attr-item')
            for attr_elem in attr_elems:
                attr_text = attr_elem.text.strip()
                if ':' in attr_text:
                    key, value = attr_text.split(':', 1)
                    product_data["核心属性"][key.strip()] = value.strip()
            print(f"📋 核心属性：")
            for key, value in product_data["核心属性"].items():
                print(f"   {key}：{value}")
        except:
            print("⚠️ 核心属性提取失败")

        # ========== 10. 提取SKU规格价格 ==========
        try:
            # 点击规格选择区域（如果需要）
            try:
                sku_btn = driver.find_element(By.CSS_SELECTOR, '.sku-selector, .specification')
                driver.execute_script("arguments[0].click();", sku_btn)
                time.sleep(2)
            except:
                pass
            
            # 提取SKU信息
            sku_elems = driver.find_elements(By.CSS_SELECTOR, '.sku-item, .spec-item')
            price_elems = driver.find_elements(By.CSS_SELECTOR, '.sku-price, .spec-price')
            
            # 兼容不同的SKU结构
            if sku_elems and price_elems:
                for i, sku_elem in enumerate(sku_elems):
                    sku_name = sku_elem.text.strip()
                    if sku_name and i < len(price_elems):
                        sku_price = price_elems[i].text.strip().replace('¥', '')
                        product_data["SKU规格价格"][sku_name] = sku_price
            
            # 备用提取方式
            if not product_data["SKU规格价格"]:
                sku_script = """
                    return window._data && window._data.priceInfo ? window._data.priceInfo : {};
                """
                sku_data = driver.execute_script(sku_script)
                if sku_data and isinstance(sku_data, dict):
                    for key, value in sku_data.items():
                        if isinstance(value, dict) and 'price' in value:
                            product_data["SKU规格价格"][key] = value['price']
            
            print(f"🎨 SKU规格价格：")
            for sku, price in product_data["SKU规格价格"].items():
                print(f"   {sku}：¥{price}")
        except:
            print("⚠️ SKU规格价格提取失败")

        # ========== 11. 提取店铺名称 ==========
        try:
            shop_elem = driver.find_element(By.CSS_SELECTOR, '.shop-name, .seller-name a')
            product_data["店铺名称"] = shop_elem.text.strip()
            print(f"🏪 店铺名称：{product_data['店铺名称']}")
        except:
            print("⚠️ 店铺名称提取失败")

        return 0

    except Exception as e:
        print(f"❌ 爬取失败！错误原因：{str(e)}")
        return None

    finally:
        input("按回车关闭浏览器...")
        if driver:
            driver.quit()

# 测试调用
if __name__ == "__main__":
    productId = "894746939153"
    test_url = (
        f"https://detail.1688.com/offer/{productId}.html"
        "?appKey=6019196&lang=zh&kjSource=pc"
        "&fromkv=refer%3AHVJFCVZUGJKEUTS2KRLDMT2CLJDVCM2UJFHFEWSHJU2FIQ2OJJKEYNKXJBAVGM2GKBDDGVZWGRKEKS2OKNLUGNCUIRHEEUCUINHFUV2HKVMVIRKPJJLEQRK2KRBU6QSUJQ2TKWBSHU6U4111"
        "&bizType=saasTool"
        "&customerId=lanjing"
        "&kj_agent_plugin=zying"
    )
    result = crawl_from_1688(test_url)
    print("\n📊 爬取结果：", json.dumps(result, ensure_ascii=False, indent=2))