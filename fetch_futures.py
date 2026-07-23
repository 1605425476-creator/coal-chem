# -*- coding: utf-8 -*-
"""抓取煤化工期货行情数据"""
import requests
import json
import re
from datetime import datetime, timezone, timedelta

# 北京时间
BJT = timezone(timedelta(hours=8))

# 期货品种配置
SYMBOLS = [
    {'code': 'JM0', 'name': '焦煤主力', 'exchange': '大商所'},
    {'code': 'J0', 'name': '焦炭主力', 'exchange': '大商所'},
    {'code': 'MA0', 'name': '甲醇主力', 'exchange': '郑商所'},
    {'code': 'SA0', 'name': '纯碱主力', 'exchange': '郑商所'},
    {'code': 'UR0', 'name': '尿素主力', 'exchange': '郑商所'},
    {'code': 'EG0', 'name': '乙二醇主力', 'exchange': '大商所'},
    {'code': 'PP0', 'name': '聚丙烯主力', 'exchange': '大商所'},
    {'code': 'L0', 'name': '聚乙烯主力', 'exchange': '大商所'}
]

def fetch_sina_futures():
    """从新浪财经获取期货数据"""
    codes = ','.join([f"nf_{s['code']}" for s in SYMBOLS])
    url = f'https://hq.sinajs.cn/list={codes}'
    headers = {
        'Referer': 'https://finance.sina.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'gb2312'
    
    results = []
    lines = response.text.strip().split('\n')
    
    for i, line in enumerate(lines):
        if i >= len(SYMBOLS):
            break
        
        match = re.search(r'hq_str_nf_\w+="(.+)"', line)
        if not match:
            continue
        
        fields = match.group(1).split(',')
        if len(fields) < 10:
            continue
        
        symbol = SYMBOLS[i]
        price = float(fields[7]) if fields[7] else 0
        prev_close = float(fields[10]) if fields[10] else price
        
        # 如果昨收异常，用开盘价
        if prev_close == 0 or abs(price - prev_close) / prev_close > 0.5:
            prev_close = float(fields[2]) if fields[2] else price
        
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close > 0 else 0
        
        results.append({
            'code': symbol['code'],
            'name': symbol['name'],
            'exchange': symbol['exchange'],
            'price': round(price, 2),
            'prev_close': round(prev_close, 2),
            'change': round(change, 2),
            'changePct': round(change_pct, 2),
            'high': round(float(fields[3]) if fields[3] else 0, 2),
            'low': round(float(fields[4]) if fields[4] else 0, 2),
            'open': round(float(fields[2]) if fields[2] else 0, 2)
        })
    
    return results

def main():
    """主函数"""
    print(f"[{datetime.now()}] 开始抓取期货数据...")
    
    try:
        futures = fetch_sina_futures()
        
        # 生成现货参考价（期货价格作为参考）
        spots = []
        for f in futures:
            spots.append({
                'code': f['code'].replace('0', ''),
                'name': f['name'].replace('主力', '现货'),
                'unit': '元/吨',
                'price': f['price'],
                'change': f['change'],
                'changePct': f['changePct'],
                'note': '参考期货主力合约价格'
            })
        
        data = {
            'updateTime': datetime.now(BJT).isoformat(),
            'futures': futures,
            'spots': spots
        }
        
        # 保存到文件
        with open('data/futures.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功抓取 {len(futures)} 个期货品种")
        print(f"✅ 成功生成 {len(spots)} 个现货参考价")
        
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        raise

if __name__ == '__main__':
    main()
