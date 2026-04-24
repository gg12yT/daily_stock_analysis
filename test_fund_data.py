# -*- coding: utf-8 -*-
"""
===================================
基金数据接口测试脚本
===================================

用于验证 AkShare 基金数据接口可用性。
运行方式：python test_fund_data.py

依赖：
    pip install akshare pandas
"""

import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_fund_data():
    """测试所有基金数据接口"""
    print("=" * 60)
    print("基金数据接口测试")
    print("=" * 60)

    # 1. 测试全量基金列表
    print("\n[1/6] 测试全量基金列表...")
    try:
        import akshare as ak
        df = ak.fund_name_em()
        print(f"    ✅ 全量基金数量: {len(df)}")
        print(f"    列名: {list(df.columns)}")
        print(f"    前3条: {df.head(3).to_dict(orient='records')}")
    except Exception as e:
        print(f"    ❌ 失败: {e}")
        return False

    # 2. 测试实时净值
    print("\n[2/6] 测试实时净值...")
    try:
        df = ak.fund_open_fund_daily_em()
        print(f"    ✅ 实时净值数据: {len(df)} 条")
        print(f"    列名: {list(df.columns)[:10]}...")
        # 找一只基金试试
        sample_code = df.iloc[0]["基金代码"] if "基金代码" in df.columns else None
        if sample_code:
            print(f"    示例基金: {sample_code}")
    except Exception as e:
        print(f"    ❌ 失败: {e}")

    # 3. 测试单只基金历史净值
    print("\n[3/6] 测试单只基金历史净值...")
    test_codes = ["000001", "110022", "162605"]
    success = False
    for code in test_codes:
        try:
            df = ak.fund_open_fund_info_em(fund=code, indicator="单位净值走势")
            print(f"    ✅ 基金 {code} 历史净值: {len(df)} 条")
            print(f"        列名: {list(df.columns)}")
            print(f"        最近3条:")
            print(df.tail(3).to_string())
            success = True
            break
        except Exception as e:
            print(f"    ⚠️ 基金 {code} 失败: {e}")
            continue
    if not success:
        print(f"    ❌ 所有测试代码均失败")

    # 4. 测试基金经理
    print("\n[4/6] 测试基金经理...")
    try:
        df = ak.fund_manager_em()
        print(f"    ✅ 基金经理数据: {len(df)} 条")
        print(f"    列名: {list(df.columns)}")
        print(f"    前3条: {df.head(3).to_dict(orient='records')}")
    except Exception as e:
        print(f"    ❌ 失败: {e}")

    # 5. 测试单只基金详情
    print("\n[5/6] 测试单只基金详情...")
    try:
        info = ak.fund_individual_em(fund="000001")
        print(f"    ✅ 单只基金详情获取成功")
        print(f"    数据条数: {len(info)}")
        if not info.empty:
            print(f"    列名: {list(info.columns)}")
            print(f"    第一行数据:\n{info.iloc[0].to_string()}")
    except Exception as e:
        print(f"    ❌ 失败: {e}")

    # 6. 测试基金规模
    print("\n[6/6] 测试基金规模...")
    try:
        df = ak.fund_scale_em(symbol="000001")
        print(f"    ✅ 基金规模数据获取成功")
        print(f"    数据条数: {len(df)}")
        print(f"    列名: {list(df.columns) if not df.empty else 'N/A'}")
        if not df.empty:
            print(f"    最近3条:\n{df.tail(3).to_string()}")
    except Exception as e:
        print(f"    ⚠️ fund_scale_em 失败: {e}")
        print(f"    （基金规模接口可能暂时不可用）")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


def test_fund_analyzer():
    """测试基金分析器"""
    print("\n" + "=" * 60)
    print("基金分析器测试")
    print("=" * 60)

    try:
        from data_provider.fund_akshare import fetch_fund_full_analysis
        from src.fund_analyzer import analyze_fund, FundTrendAnalyzer

        # 使用模拟数据分析
        mock_data = {
            "individual": {
                "details": {
                    "基金简称": "XX成长混合",
                    "基金类型": "混合型",
                }
            },
            "performance": {
                "recent_1m": 3.5,
                "recent_3m": 8.2,
                "recent_6m": 12.1,
                "recent_1y": 25.6,
            },
            "scale": {
                "current": 45.5,
                "previous": 42.3,
                "change_pct": 7.6,
                "alert": False,
            },
            "max_drawdown": 12.3,
            "volatility": 14.5,
            "sharpe_ratio": 1.85,
            "manager": {
                "name": "张三",
                "tenure_years": 4.5,
                "funds_count": 2,
            },
            "ranking": {
                "ranking": 50,
                "total": 500,
                "percent": 90.0,
            }
        }

        analyzer = FundTrendAnalyzer()
        result = analyzer.analyze("000001", mock_data)

        print("\n分析结果:")
        print(analyzer.format_analysis(result))

        print("\nSchema 验证:")
        schema = result.to_schema()
        print(f"  fund_code: {schema.fund_code}")
        print(f"  signal_type: {schema.signal_type}")
        print(f"  risk_level: {schema.risk_level}")
        print(f"  sentiment_score: {schema.sentiment_score}")
        print(f"  performance: {schema.dashboard.performance if schema.dashboard else 'N/A'}")

    except Exception as e:
        print(f"    ❌ 分析器测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n注意：请确保已安装 akshare 和 pandas")
    print("pip install akshare pandas\n")

    try:
        import akshare
        import pandas
        print(f"akshare 版本: {akshare.__version__}")
        print(f"pandas 版本: {pandas.__version__}\n")
    except ImportError as e:
        print(f"缺少必要依赖: {e}")
        print("请运行: pip install akshare pandas")
        sys.exit(1)

    # 运行数据接口测试
    test_fund_data()

    # 运行分析器测试
    test_fund_analyzer()
