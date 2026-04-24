# -*- coding: utf-8 -*-
"""
===================================
基金数据获取层 - AkShare 接口封装
===================================

基于 AkShare 库实现基金数据获取，提供：
- 全量基金列表查询
- 实时净值查询
- 历史净值/排名查询
- 基金经理信息查询
- 单只基金详情查询
- 基金规模查询

依赖：akshare >= 1.10.0
安装：pip install akshare
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FundDataError(Exception):
    """基金数据获取异常"""
    pass


def get_fund_list() -> pd.DataFrame:
    """
    获取全量基金列表

    Returns:
        DataFrame，列包含：
        - 基金代码 (基金代码)
        - 基金名称 (基金名称)
        - 拼音缩写 (拼音缩写)
    """
    try:
        import akshare as ak
        df = ak.fund_name_em()
        logger.info(f"成功获取全量基金列表，共 {len(df)} 只")
        return df
    except Exception as e:
        logger.error(f"获取全量基金列表失败: {e}")
        raise FundDataError(f"获取全量基金列表失败: {e}") from e


def get_fund_realtime_nav(fund_code: Optional[str] = None) -> pd.DataFrame:
    """
    获取开放式基金实时净值

    Args:
        fund_code: 基金代码（可选），不传则获取全市场实时净值

    Returns:
        DataFrame，列包含：
        - 基金代码
        - 基金名称
        - 单位净值
        - 累计净值
        - 日增长率
        - 近1月增长率
        - 近3月增长率
        - 近6月增长率
        - 近1年增长率
        - 近2年增长率
        - 近3年增长率
        - 今年来增长率
        - 成立来增长率
    """
    try:
        import akshare as ak
        df = ak.fund_open_fund_daily_em(symbol="全部") if fund_code is None else ak.fund_open_fund_daily_em(symbol=fund_code)
        logger.info(f"成功获取实时净值数据，共 {len(df)} 条")
        return df
    except Exception as e:
        logger.error(f"获取实时净值失败: {e}")
        raise FundDataError(f"获取实时净值失败: {e}") from e


def get_fund_historical_nav(fund_code: str, indicator: str = "单位净值走势") -> pd.DataFrame:
    """
    获取基金历史净值/排名数据

    Args:
        fund_code: 基金代码，如 "000001"
        indicator: 查询类型
            - "单位净值走势"：历史单位净值
            - "累计净值走势"：历史累计净值
            - "累计收益率"：历史收益率
            - "同类排名"：同类排名详情
            - "分红送配"：分红送配记录

    Returns:
        DataFrame，列因 indicator 不同而异
    """
    try:
        import akshare as ak
        df = ak.fund_open_fund_info_em(fund=fund_code, indicator=indicator)
        logger.info(f"成功获取基金 {fund_code} 历史净值({indicator})，共 {len(df)} 条")
        return df
    except Exception as e:
        logger.error(f"获取基金 {fund_code} 历史净值失败: {e}")
        raise FundDataError(f"获取基金历史净值失败: {e}") from e


def get_fund_manager_info() -> pd.DataFrame:
    """
    获取基金经理列表

    Returns:
        DataFrame，列包含：
        - 基金经理代码
        - 基金经理姓名
        - 任职时间
        - 管理基金数量
        - 所属公司
        - 任职期间最佳回报
    """
    try:
        import akshare as ak
        df = ak.fund_manager_em()
        logger.info(f"成功获取基金经理列表，共 {len(df)} 条")
        return df
    except Exception as e:
        logger.error(f"获取基金经理列表失败: {e}")
        raise FundDataError(f"获取基金经理列表失败: {e}") from e


def get_fund_individual(fund_code: str) -> Dict[str, Any]:
    """
    获取单只基金详情

    Args:
        fund_code: 基金代码，如 "000001"

    Returns:
        Dict，包含基金详细信息：
        - 基金全名、简称、代码
        - 基金类型、成立日期
        - 基金管理人、基金托管人
        - 规模、成立来收益率
        - 基金经理、评级信息
    """
    try:
        import akshare as ak
        df = ak.fund_individual_em(fund=fund_code)
        # 转换为字典格式
        if df is not None and not df.empty:
            info = df.to_dict(orient="records")
            result = {
                "fund_code": fund_code,
                "details": info[0] if info else {},
                "raw_dataframe": df
            }
            logger.info(f"成功获取基金 {fund_code} 详情")
            return result
        else:
            logger.warning(f"基金 {fund_code} 详情为空")
            return {"fund_code": fund_code, "details": {}, "raw_dataframe": df}
    except Exception as e:
        logger.error(f"获取基金 {fund_code} 详情失败: {e}")
        raise FundDataError(f"获取单只基金详情失败: {e}") from e


def get_fund_scale(fund_code: str) -> pd.DataFrame:
    """
    获取基金规模变动历史

    Args:
        fund_code: 基金代码，如 "000001"

    Returns:
        DataFrame，列包含：
        - 日期
        - 规模（亿元）
        - 规模变动
    """
    try:
        import akshare as ak
        # fund_scale_em 接口获取规模数据
        df = ak.fund_scale_em(symbol=fund_code)
        logger.info(f"成功获取基金 {fund_code} 规模数据，共 {len(df)} 条")
        return df
    except Exception as e:
        logger.warning(f"获取基金 {fund_code} 规模数据失败，尝试备用方式: {e}")
        # 尝试通过详情接口获取规模
        try:
            details = get_fund_individual(fund_code)
            scale_info = details.get("details", {}).get("规模", None)
            if scale_info:
                logger.info(f"通过详情接口获取基金 {fund_code} 规模: {scale_info}")
                return pd.DataFrame([{"fund_code": fund_code, "scale": scale_info}])
        except Exception:
            pass
        raise FundDataError(f"获取基金规模失败: {e}") from e


def get_fund_ranking(fund_code: str, period: str = "近3月") -> Optional[Dict[str, Any]]:
    """
    获取基金同类排名

    Args:
        fund_code: 基金代码
        period: 时间区间
            - "近1月"
            - "近3月"
            - "近6月"
            - "近1年"
            - "近2年"
            - "近3年"

    Returns:
        Dict，包含排名信息：
        - ranking: 排名
        - total: 同类总数
        - percent: 排名百分位
    """
    try:
        import akshare as ak
        df = ak.fund_open_fund_info_em(fund=fund_code, indicator="同类排名")
        if df is not None and not df.empty:
            # 找到对应期间的数据
            period_map = {
                "近1月": "近1月",
                "近3月": "近3月",
                "近6月": "近6月",
                "近1年": "近1年",
                "近2年": "近2年",
                "近3年": "近3年"
            }
            target_col = period_map.get(period, "近3月")
            if target_col in df.columns:
                row = df[df["周期"] == target_col] if "周期" in df.columns else df.iloc[-1:]
                if not row.empty:
                    ranking = row.iloc[0].get("排名", 0)
                    total = row.iloc[0].get("同类总数量", 0)
                    if ranking and total:
                        percent = (1 - ranking / total) * 100 if total > 0 else 0
                        return {
                            "ranking": int(ranking),
                            "total": int(total),
                            "percent": round(percent, 2)
                        }
        logger.warning(f"未找到基金 {fund_code} 的排名数据")
        return None
    except Exception as e:
        logger.warning(f"获取基金 {fund_code} 排名失败: {e}")
        return None


def get_fund_performance_metrics(fund_code: str) -> Dict[str, float]:
    """
    获取基金收益指标（近1月/3月/6月/1年涨幅）

    Args:
        fund_code: 基金代码

    Returns:
        Dict，包含各区间涨幅：
        - recent_1m: 近1月涨幅 (%)
        - recent_3m: 近3月涨幅 (%)
        - recent_6m: 近6月涨幅 (%)
        - recent_1y: 近1年涨幅 (%)
    """
    try:
        # 优先从实时净值获取
        df_list = get_fund_realtime_nav(fund_code)
        if df_list is not None and not df_list.empty:
            # 找到对应基金
            fund_row = df_list[df_list["基金代码"] == fund_code] if "基金代码" in df_list.columns else df_list.iloc[0:1]
            if not fund_row.empty:
                row = fund_row.iloc[0]
                metrics = {}
                # 尝试读取各期间收益率
                for period, col in [
                    ("recent_1m", "近1月增长率"),
                    ("recent_3m", "近3月增长率"),
                    ("recent_6m", "近6月增长率"),
                    ("recent_1y", "近1年增长率"),
                ]:
                    if col in row.index:
                        val = row[col]
                        try:
                            metrics[period] = float(val) if pd.notna(val) else 0.0
                        except (ValueError, TypeError):
                            metrics[period] = 0.0
                    else:
                        metrics[period] = 0.0
                return metrics

        # 备用：从历史净值计算
        df_nav = get_fund_historical_nav(fund_code, "单位净值走势")
        if df_nav is not None and len(df_nav) >= 20:
            df_nav = df_nav.sort_values("日期") if "日期" in df_nav.columns else df_nav
            latest = df_nav.iloc[-1]
            latest_nav = latest.get("单位净值", latest.get("净值日期", 0))
            latest_date = latest.get("日期", datetime.now())

            metrics = {}
            for period, days in [("recent_1m", 30), ("recent_3m", 90), ("recent_6m", 180), ("recent_1y", 365)]:
                target_date = latest_date - timedelta(days=days)
                # 找最接近的净值
                hist = df_nav[df_nav["日期"] <= target_date]
                if not hist.empty:
                    old_nav = hist.iloc[-1].get("单位净值", 0)
                    if old_nav and latest_nav and float(old_nav) > 0:
                        metrics[period] = round((float(latest_nav) - float(old_nav)) / float(old_nav) * 100, 2)
                    else:
                        metrics[period] = 0.0
                else:
                    metrics[period] = 0.0
            return metrics

        return {"recent_1m": 0.0, "recent_3m": 0.0, "recent_6m": 0.0, "recent_1y": 0.0}
    except Exception as e:
        logger.warning(f"计算基金 {fund_code} 收益指标失败: {e}")
        return {"recent_1m": 0.0, "recent_3m": 0.0, "recent_6m": 0.0, "recent_1y": 0.0}


def get_fund_manager_detail(fund_code: str) -> Optional[Dict[str, Any]]:
    """
    获取某只基金的基金经理详情

    Args:
        fund_code: 基金代码

    Returns:
        Dict，包含基金经理信息：
        - name: 基金经理姓名
        - tenure_start: 任职开始日期
        - tenure_days: 任职天数
        - funds_count: 当前管理基金数
    """
    try:
        import akshare as ak
        df = ak.fund_manager_em()
        if df is not None and not df.empty:
            # 找到该基金经理（通过基金代码匹配）
            # 注：基金经理表通常按基金经理维度，可尝试关联
            # 基金详情中包含基金经理信息
            fund_info = get_fund_individual(fund_code)
            manager_name = fund_info.get("details", {}).get("基金经理", None)
            if manager_name:
                manager_rows = df[df["基金经理姓名"] == manager_name]
                if not manager_rows.empty:
                    row = manager_rows.iloc[0]
                    tenure_str = str(row.get("任职时间", ""))
                    # 计算任职年限
                    try:
                        if tenure_str:
                            tenure_date = pd.to_datetime(tenure_str)
                            tenure_days = (datetime.now() - tenure_date).days
                            tenure_years = round(tenure_days / 365, 1)
                        else:
                            tenure_years = 0.0
                            tenure_days = 0
                    except Exception:
                        tenure_years = 0.0
                        tenure_days = 0

                    return {
                        "name": manager_name,
                        "tenure_start": tenure_str,
                        "tenure_days": tenure_days,
                        "tenure_years": tenure_years,
                        "funds_count": int(row.get("管理基金数量", 0))
                    }
        return None
    except Exception as e:
        logger.warning(f"获取基金 {fund_code} 基金经理详情失败: {e}")
        return None


def calculate_max_drawdown(fund_code: str) -> float:
    """
    计算基金历史最大回撤

    Args:
        fund_code: 基金代码

    Returns:
        最大回撤值（正值表示回撤幅度，如 15.5 表示 15.5%）
    """
    try:
        df = get_fund_historical_nav(fund_code, "单位净值走势")
        if df is None or len(df) < 2:
            return 0.0

        df = df.sort_values("日期") if "日期" in df.columns else df
        nav_col = "单位净值" if "单位净值" in df.columns else df.columns[0]
        nav = df[nav_col].astype(float)

        # 计算历史最高点
        running_max = nav.expanding().max()
        drawdown = (nav - running_max) / running_max * 100  # 回撤为负值

        max_dd = abs(drawdown.min())  # 取最大跌幅（正数）
        return round(max_dd, 2)
    except Exception as e:
        logger.warning(f"计算基金 {fund_code} 最大回撤失败: {e}")
        return 0.0


def calculate_volatility(fund_code: str) -> float:
    """
    计算基金收益波动率（年化）

    Args:
        fund_code: 基金代码

    Returns:
        年化波动率（%）
    """
    try:
        df = get_fund_historical_nav(fund_code, "累计收益率")
        if df is None or len(df) < 2:
            # 尝试从单位净值计算
            df = get_fund_historical_nav(fund_code, "单位净值走势")

        if df is None or len(df) < 30:
            return 0.0

        df = df.sort_values("日期") if "日期" in df.columns else df
        nav_col = "累计收益率" if "累计收益率" in df.columns else ("单位净值" if "单位净值" in df.columns else df.columns[0])

        if nav_col == "累计收益率":
            returns = df[nav_col].dropna().astype(float) / 100
        else:
            nav = df[nav_col].astype(float)
            returns = nav.pct_change().dropna()

        if len(returns) < 10:
            return 0.0

        # 年化波动率（日波动率 * sqrt(252)）
        daily_std = returns.std()
        annualized_vol = daily_std * (252 ** 0.5) * 100
        return round(annualized_vol, 2)
    except Exception as e:
        logger.warning(f"计算基金 {fund_code} 波动率失败: {e}")
        return 0.0


def get_fund_scale_change(fund_code: str) -> Dict[str, Any]:
    """
    获取基金规模变动情况

    Args:
        fund_code: 基金代码

    Returns:
        Dict:
        - current: 当前规模（亿元）
        - previous: 上期规模（亿元）
        - change_pct: 变化百分比
        - alert: 是否异动（变化超过30%）
    """
    try:
        df = get_fund_scale(fund_code)
        if df is not None and len(df) >= 2:
            df = df.sort_values("日期") if "日期" in df.columns else df
            current_scale = df.iloc[-1]
            previous_scale = df.iloc[-2]

            # 尝试找规模列
            scale_col = None
            for col in ["规模", "规模（亿元）", "净资产", "基金规模"]:
                if col in current_scale.index:
                    scale_col = col
                    break

            if scale_col is None:
                # 取第一个数值列
                for col in df.columns:
                    if col not in ["日期", "日期时间"]:
                        try:
                            float(current_scale[col])
                            scale_col = col
                            break
                        except (ValueError, TypeError):
                            continue

            if scale_col:
                curr = float(current_scale[scale_col])
                prev = float(previous_scale[scale_col])
                change_pct = ((curr - prev) / prev * 100) if prev > 0 else 0.0

                return {
                    "current": round(curr, 2),
                    "previous": round(prev, 2),
                    "change_pct": round(change_pct, 2),
                    "alert": abs(change_pct) > 30
                }

        # 备用：从详情获取
        details = get_fund_individual(fund_code)
        scale_str = details.get("details", {}).get("规模", "0亿元")
        try:
            scale_val = float(scale_str.replace("亿元", ""))
            return {
                "current": scale_val,
                "previous": scale_val,
                "change_pct": 0.0,
                "alert": False
            }
        except (ValueError, AttributeError):
            pass

        return {"current": 0.0, "previous": 0.0, "change_pct": 0.0, "alert": False}
    except Exception as e:
        logger.warning(f"获取基金 {fund_code} 规模变动失败: {e}")
        return {"current": 0.0, "previous": 0.0, "change_pct": 0.0, "alert": False}


# =============================================================================
# 便捷封装函数
# =============================================================================

def fetch_fund_full_analysis(fund_code: str) -> Dict[str, Any]:
    """
    获取基金完整分析数据

    一次性获取所有分析所需数据

    Args:
        fund_code: 基金代码

    Returns:
        Dict，包含所有分析数据
    """
    result = {
        "fund_code": fund_code,
        "success": True,
        "error": None,
        "data": {}
    }

    try:
        # 基本信息
        result["data"]["individual"] = get_fund_individual(fund_code)

        # 收益指标
        result["data"]["performance"] = get_fund_performance_metrics(fund_code)

        # 规模变动
        result["data"]["scale"] = get_fund_scale_change(fund_code)

        # 最大回撤
        result["data"]["max_drawdown"] = calculate_max_drawdown(fund_code)

        # 波动率
        result["data"]["volatility"] = calculate_volatility(fund_code)

        # 基金经理
        result["data"]["manager"] = get_fund_manager_detail(fund_code)

        # 同类排名
        result["data"]["ranking"] = get_fund_ranking(fund_code, "近3月")

        logger.info(f"基金 {fund_code} 全量数据获取完成")
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        logger.error(f"获取基金 {fund_code} 全量数据失败: {e}")

    return result


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    print("=" * 50)
    print("基金数据接口测试")
    print("=" * 50)

    # 测试全量基金列表
    try:
        df = get_fund_list()
        print(f"\n✅ 全量基金数量: {len(df)}")
        print(df.head(3))
    except Exception as e:
        print(f"\n❌ 全量基金列表获取失败: {e}")

    # 测试实时净值（单只）
    try:
        df = get_fund_realtime_nav("000001")
        print(f"\n✅ 实时净值数据: {len(df)} 条")
        print(df.head(3))
    except Exception as e:
        print(f"\n❌ 实时净值获取失败: {e}")

    # 测试单只基金历史净值
    try:
        df = get_fund_historical_nav("000001", "单位净值走势")
        print(f"\n✅ 历史净值数据: {len(df)} 条")
        print(df.tail(3))
    except Exception as e:
        print(f"\n❌ 历史净值获取失败: {e}")

    # 测试基金经理
    try:
        df = get_fund_manager_info()
        print(f"\n✅ 基金经理数据: {len(df)} 条")
        print(df.head(3))
    except Exception as e:
        print(f"\n❌ 基金经理数据获取失败: {e}")

    # 测试单只基金详情
    try:
        info = get_fund_individual("000001")
        print(f"\n✅ 单只基金详情获取成功")
        print(f"基金代码: {info.get('fund_code')}")
    except Exception as e:
        print(f"\n❌ 单只基金详情获取失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
