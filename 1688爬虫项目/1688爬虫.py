# 只保留爬虫相关导入，删除所有Flask/CORS相关依赖
import crawl_sites

if __name__ == '__main__':
    # 1. 写死产品ID（替换成你要爬取的真实1688产品ID）
    productId = "894746939153"  # 这里直接填你需要的ID，比如实际ID：123456789012

    # 2. 拼接1688产品详情页URL（和原代码逻辑一致）
    url = (
        f"https://detail.1688.com/offer/{productId}.html"
        "?appKey=6019196&lang=zh&kjSource=pc"
        "&fromkv=refer%3AHVJFCVZUGJKEUTS2KRLDMT2CLJDVCM2UJFHFEWSHJU2FIQ2OJJKEYNKXJBAVGM2GKBDDGVZWGRKEKS2OKNLUGNCUIRHEEUCUINHFUV2HKVMVIRKPJJLEQRK2KRBU6QSUJQ2TKWBSHU6U4111"
        "&bizType=saasTool"
        "&customerId=lanjing"
        "&kj_agent_plugin=zying"
    )

    try:
        # 3. 调用爬虫函数爬取数据
        crawl_result = crawl_sites.crawl_from_1688(url)

    except Exception as e:
        # 异常捕获（避免爬取出错导致程序直接崩溃）
        print(f"爬取失败！错误原因：{str(e)}")