# -*- coding: utf-8 -*-
"""
===================================
基金智能分析层
===================================

基于用户交易理念，针对基金产品进行智能分析：
1. 净值趋势分析（近1月/3月/6月/1年涨幅）
2. 同类排名百分位计算
3. 最大回撤计算
4. 夏普比率计算（如数据可用）
5. 基金经理稳定性评估
6. 规模异动检测
7. 生成操作建议（买入/持有/卖出）

参考：src/stock_analyzer.py 设计模式
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

import pandas as pd
import numpy as np

from src.schemas.fund_report_schema import (
    FundReportSchema,
    FundDashboard,
    FundCoreConclusion,
    FundPerformance,
    FundRisk,
    FundManager,
    FundScale,
)

logger = logging.getLogger(__name__)


class FundSignal(Enum):
    """基金操作信号"""
    STRONG_BUY = "强烈买入"     # 多条件满足
    BUY = "买入"               # 基本条件满足
    HOLD = "持有"              # 维持现状
    WAIT = "观望"              # 等待时机
    SELL = "卖出"              # 考虑赎回
    STRONG_SELL = "强烈卖出"   # 趋势破坏


class FundRiskLevel(Enum):
    """风险等级"""
    LOW = "低"      # 低风险
    MEDIUM = "中"   # 中风险
    HIGH = "高"     # 高风险


class ManagerStability(Enum):
    """基金经理稳定性"""
    STABLE = "稳定"
    CAUTION = "注意"
    UNSTABLE = "不稳定"


@dataclass
class FundAnalysisResult:
    """基金分析结果"""
    fund_code: str
    fund_name: str = ""
    fund_type: str = ""

    # 收益表现
    recent_1m: float = 0.0    # 近1月涨幅 (%)
    recent_3m: float = 0.0    # 近3月涨幅 (%)
    recent_6m: float = 0.0    # 近6月涨幅 (%)
    recent_1y: float = 0.0    # 近1年涨幅 (%)
    ranking_percent: float = 0.0  # 同类排名百分位 (0-100)

    # 风险指标
    max_drawdown: float = 0.0     # 最大回撤 (%)
    volatility: float = 0.0       # 年化波动率 (%)
    sharpe_ratio: float = 0.0    # 夏普比率

    # 基金经理
    manager_name: str = ""
    manager_tenure_years: float = 0.0
    manager_funds_count: int = 0
    manager_stability: str = "稳定"

    # 规模
    scale_current: float = 0.0    # 当前规模（亿元）
    scale_change_pct: float = 0.0  # 规模变化百分比
    scale_alert: bool = False     # 是否异动

    # 综合评分与信号
    sentiment_score: int = 50     # 综合评分 0-100
    signal_type: str = "持有"      # 买入/持有/卖出
    risk_level: str = "中"         # 低/中/高

    # 理由与提示
    signal_reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    action_checklist: List[str] = field(default_factory=list)

    # 原始数据
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_schema(self) -> FundReportSchema:
        """转换为 Pydantic Schema"""
        dashboard = FundDashboard(
            core_conclusion=FundCoreConclusion(
                one_sentence=self._generate_one_sentence(),
                signal_type=self.signal_type,
                risk_level=self.risk_level,
            ),
            performance=FundPerformance(
                recent_1m=self.recent_1m,
                recent_3m=self.recent_3m,
                recent_6m=self.recent_6m,
                recent_1y=self.recent_1y,
                ranking_percent=self.ranking_percent,
            ),
            risk=FundRisk(
                max_drawdown=self.max_drawdown,
                volatility=self.volatility,
                sharpe_ratio=self.sharpe_ratio,
            ),
            manager=FundManager(
                name=self.manager_name,
                tenure_years=self.manager_tenure_years,
                funds_count=self.manager_funds_count,
                stability=self.manager_stability,
            ),
            scale=FundScale(
                current=self.scale_current,
                change_pct=self.scale_change_pct,
                alert=self.scale_alert,
            ),
            action_checklist=self.action_checklist,
        )

        return FundReportSchema(
            fund_code=self.fund_code,
            fund_name=self.fund_name,
            fund_type=self.fund_type,
            sentiment_score=self.sentiment_score,
            signal_type=self.signal_type,
            risk_level=self.risk_level,
            dashboard=dashboard,
            analysis_summary=self._generate_summary(),
            risk_warning=" ".join(self.risk_factors) if self.risk_factors else None,
            buy_reason="；".join(self.signal_reasons) if self.signal_reasons else None,
            operation_advice=self.signal_type,
        )

    def _generate_one_sentence(self) -> str:
        """生成一句话结论"""
        if self.signal_type in ["强烈买入", "买入"]:
            if self.recent_1y > 20:
                return f"近1年涨幅{self.recent_1y:.1f}%，表现优异，建议买入"
            elif self.recent_1y > 0:
                return f"净值稳步上行，同类排名领先，建议买入"
            else:
                return f"净值处于相对低位，可考虑分批买入"
        elif self.signal_type == "持有":
            if self.recent_1y > 0:
                return f"基金净值走势稳健，建议继续持有"
            else:
                return f"净值有所波动，建议谨慎持有观察"
        elif self.signal_type in ["卖出", "强烈卖出"]:
            return f"风险因素较多，建议考虑赎回"
        else:
            return f"暂无明确信号，建议保持观望"

    def _generate_summary(self) -> str:
        """生成分析摘要"""
        parts = []
        if self.recent_1y != 0:
            parts.append(f"近1年{self.recent_1y:+.1f}%")
        if self.recent_3m != 0:
            parts.append(f"近3月{self.recent_3m:+.1f}%")
        if self.ranking_percent > 0:
            parts.append(f"同类排名前{int(100 - self.ranking_percent)}%")
        if self.max_drawdown > 0:
            parts.append(f"最大回撤{self.max_drawdown:.1f}%")
        if self.manager_name:
            parts.append(f"基金经理{self.manager_name}")
        return "，".join(parts) if parts else "暂无数据"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "fund_code": self.fund_code,
            "fund_name": self.fund_name,
            "fund_type": self.fund_type,
            "performance": {
                "recent_1m": self.recent_1m,
                "recent_3m": self.recent_3m,
                "recent_6m": self.recent_6m,
                "recent_1y": self.recent_1y,
                "ranking_percent": self.ranking_percent,
            },
            "risk": {
                "max_drawdown": self.max_drawdown,
                "volatility": self.volatility,
                "sharpe_ratio": self.sharpe_ratio,
            },
            "manager": {
                "name": self.manager_name,
                "tenure_years": self.manager_tenure_years,
                "funds_count": self.manager_funds_count,
                "stability": self.manager_stability,
            },
            "scale": {
                "current": self.scale_current,
                "change_pct": self.scale_change_pct,
                "alert": self.scale_alert,
            },
            "signal": {
                "sentiment_score": self.sentiment_score,
                "signal_type": self.signal_type,
                "risk_level": self.risk_level,
                "reasons": self.signal_reasons,
                "risk_factors": self.risk_factors,
                "checklist": self.action_checklist,
            },
        }


class FundTrendAnalyzer:
    """
    基金趋势分析器

    基于用户交易理念实现：
    1. 净值趋势 - 关注近期表现
    2. 风险指标 - 最大回撤、波动率、夏普比率
    3. 基金经理 - 稳定性评估
    4. 规模检测 - 异动检测
    5. 综合信号 - 买入/持有/卖出建议
    """

    # 评分阈值
    BUY_THRESHOLD = 70        # 买入阈值（0-100）
    SELL_THRESHOLD = 30      # 卖出阈值（0-100）
    HOLD_THRESHOLD = 45      # 持有阈值（0-100）

    # 表现权重
    PERFORMANCE_WEIGHT = 40   # 收益表现权重
    RISK_WEIGHT = 30         # 风险控制权重
    MANAGER_WEIGHT = 15      # 基金经理权重
    SCALE_WEIGHT = 15        # 规模稳定性权重

    # 表现评级阈值
    EXCELLENT_RETURN = 20    # 优秀收益（%）
    GOOD_RETURN = 10         # 良好收益（%）
    POOR_RETURN = -10        # 较差收益（%）

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze(self, fund_code: str, data: Dict[str, Any]) -> FundAnalysisResult:
        """
        分析基金

        Args:
            fund_code: 基金代码
            data: 基金数据字典，包含：
                - individual: 基金详情
                - performance: 收益指标
                - scale: 规模变动
                - max_drawdown: 最大回撤
                - volatility: 波动率
                - manager: 基金经理
                - ranking: 排名信息

        Returns:
            FundAnalysisResult 分析结果
        """
        result = FundAnalysisResult(fund_code=fund_code)

        if not data:
            logger.warning(f"{fund_code} 数据不足，无法完成分析")
            result.risk_factors.append("数据不足，无法完成分析")
            return result

        result.raw_data = data

        # 提取基本信息
        individual = data.get("individual", {})
        if individual:
            details = individual.get("details", {})
            result.fund_name = details.get("基金简称", details.get("基金全称", ""))
            result.fund_type = details.get("基金类型", "")

        # 提取收益数据
        perf = data.get("performance", {})
        result.recent_1m = perf.get("recent_1m", 0.0)
        result.recent_3m = perf.get("recent_3m", 0.0)
        result.recent_6m = perf.get("recent_6m", 0.0)
        result.recent_1y = perf.get("recent_1y", 0.0)

        # 提取排名
        ranking = data.get("ranking", {})
        if ranking:
            result.ranking_percent = ranking.get("percent", 0.0)

        # 提取风险指标
        result.max_drawdown = data.get("max_drawdown", 0.0)
        result.volatility = data.get("volatility", 0.0)
        result.sharpe_ratio = data.get("sharpe_ratio", 0.0)

        # 提取规模数据
        scale = data.get("scale", {})
        result.scale_current = scale.get("current", 0.0)
        result.scale_change_pct = scale.get("change_pct", 0.0)
        result.scale_alert = scale.get("alert", False)

        # 提取基金经理
        manager = data.get("manager", {})
        if manager:
            result.manager_name = manager.get("name", "")
            result.manager_tenure_years = manager.get("tenure_years", 0.0)
            result.manager_funds_count = manager.get("funds_count", 0)
            result.manager_stability = self._evaluate_manager_stability(
                manager.get("tenure_years", 0.0),
                manager.get("funds_count", 0),
            )

        # 生成评分和信号
        self._calculate_score(result)

        # 生成操作检查清单
        self._generate_action_checklist(result)

        return result

    def _evaluate_manager_stability(self, tenure_years: float, funds_count: int) -> str:
        """
        评估基金经理稳定性

        评估标准：
        - 任职年限 >= 3年：稳定
        - 任职年限 1-3年：注意
        - 任职年限 < 1年：不稳定
        - 管理基金数过多(>5)：注意
        """
        if tenure_years >= 3 and funds_count <= 3:
            return "稳定"
        elif tenure_years >= 1 and funds_count <= 5:
            return "注意"
        else:
            return "不稳定"

    def _calculate_score(self, result: FundAnalysisResult) -> None:
        """
        计算综合评分并生成信号

        评分维度：
        - 收益表现 (40分)：短期、中期、长期表现
        - 风险控制 (30分)：回撤、波动率、夏普比率
        - 基金经理 (15分)：稳定性、管理经验
        - 规模稳定性 (15分)：规模异动检测
        """
        score = 0
        reasons = []
        risks = []

        # === 收益表现评分 (40分) ===
        perf_score = 0

        # 近1月表现（10分）
        if result.recent_1m > 5:
            perf_score += 10
            reasons.append(f"✅ 近1月涨幅{result.recent_1m:.1f}%，表现强劲")
        elif result.recent_1m > 0:
            perf_score += 7
            reasons.append(f"⚡ 近1月涨幅{result.recent_1m:.1f}%，稳中有升")
        elif result.recent_1m > -3:
            perf_score += 4
        else:
            perf_score += 1
            risks.append(f"⚠️ 近1月下跌{result.recent_1m:.1f}%，短期走弱")

        # 近3月表现（10分）
        if result.recent_3m > 10:
            perf_score += 10
            reasons.append(f"✅ 近3月涨幅{result.recent_3m:.1f}%，中期表现优异")
        elif result.recent_3m > 0:
            perf_score += 7
            reasons.append(f"⚡ 近3月涨幅{result.recent_3m:.1f}%，中期向好")
        elif result.recent_3m > -5:
            perf_score += 4
        else:
            perf_score += 1
            risks.append(f"⚠️ 近3月下跌{result.recent_3m:.1f}%，中期趋势走弱")

        # 近6月表现（10分）
        if result.recent_6m > 15:
            perf_score += 10
            reasons.append(f"✅ 近6月涨幅{result.recent_6m:.1f}%，长期趋势向好")
        elif result.recent_6m > 0:
            perf_score += 6
        else:
            perf_score += 2
            risks.append(f"⚠️ 近6月下跌{result.recent_6m:.1f}%，注意风险")

        # 近1年表现（10分）
        if result.recent_1y > 20:
            perf_score += 10
            reasons.append(f"🏆 近1年涨幅{result.recent_1y:.1f}%，年度冠军候选")
        elif result.recent_1y > self.EXCELLENT_RETURN:
            perf_score += 8
            reasons.append(f"✅ 近1年涨幅{result.recent_1y:.1f}%，年度表现优秀")
        elif result.recent_1y > self.GOOD_RETURN:
            perf_score += 6
        elif result.recent_1y > 0:
            perf_score += 4
        elif result.recent_1y > self.POOR_RETURN:
            perf_score += 2
            risks.append(f"⚠️ 近1年涨幅{result.recent_1y:.1f}%，年度表现一般")
        else:
            perf_score += 0
            risks.append(f"❌ 近1年下跌{result.recent_1y:.1f}%，年度表现较差")

        # 排名加分（最高5分）
        if result.ranking_percent >= 90:
            perf_score += 5
            reasons.append(f"🏆 同类排名前{int(100 - result.ranking_percent)}%，顶尖水平")
        elif result.ranking_percent >= 70:
            perf_score += 3
            reasons.append(f"✅ 同类排名前{int(100 - result.ranking_percent)}%，表现良好")
        elif result.ranking_percent > 0:
            pass  # 中等及以下不加分

        score += perf_score

        # === 风险控制评分 (30分) ===
        risk_score = 0

        # 最大回撤评分（15分）
        if result.max_drawdown < 10:
            risk_score += 15
            reasons.append(f"✅ 最大回撤{result.max_drawdown:.1f}%，风险控制优秀")
        elif result.max_drawdown < 15:
            risk_score += 12
        elif result.max_drawdown < 20:
            risk_score += 8
        elif result.max_drawdown < 30:
            risk_score += 4
            risks.append(f"⚠️ 最大回撤{result.max_drawdown:.1f}%，波动较大")
        else:
            risk_score += 0
            risks.append(f"❌ 最大回撤{result.max_drawdown:.1f}%，风险较高")

        # 波动率评分（10分）
        if result.volatility < 10:
            risk_score += 10
        elif result.volatility < 15:
            risk_score += 7
        elif result.volatility < 20:
            risk_score += 4
            risks.append(f"⚠️ 波动率{result.volatility:.1f}%，波动适中")
        else:
            risk_score += 1
            risks.append(f"⚠️ 波动率{result.volatility:.1f}%，波动较大")

        # 夏普比率评分（5分）
        if result.sharpe_ratio >= 2:
            risk_score += 5
            reasons.append(f"✅ 夏普比率{result.sharpe_ratio:.2f}，风险收益比优秀")
        elif result.sharpe_ratio >= 1:
            risk_score += 3
        elif result.sharpe_ratio > 0:
            risk_score += 1
        else:
            risk_score += 0  # 夏普比率为负或无数据

        score += risk_score

        # === 基金经理评分 (15分) ===
        manager_score = 0
        if result.manager_name:
            if result.manager_stability == "稳定":
                manager_score += 15
                reasons.append(f"✅ 基金经理{result.manager_name}，任职{result.manager_tenure_years:.1f}年，稳定性好")
            elif result.manager_stability == "注意":
                manager_score += 8
                reasons.append(f"⚡ 基金经理{result.manager_name}，建议关注")
            else:
                manager_score += 3
                risks.append(f"⚠️ 基金经理{result.manager_name}，任职较短，注意稳定性")
        else:
            manager_score += 7  # 无基金经理信息给个基础分

        score += manager_score

        # === 规模稳定性评分 (15分) ===
        scale_score = 0
        if result.scale_current > 0:
            if abs(result.scale_change_pct) < 10:
                scale_score += 15
            elif abs(result.scale_change_pct) < 20:
                scale_score += 10
            elif abs(result.scale_change_pct) < 30:
                scale_score += 5
                risks.append(f"⚠️ 规模变动{result.scale_change_pct:+.1f}%，有一定变化")
            else:
                scale_score += 0
                if result.scale_alert:
                    risks.append(f"❌ 规模异动{result.scale_change_pct:+.1f}%，需关注")
        else:
            scale_score += 7  # 无规模数据给基础分

        score += scale_score

        # === 综合判断 ===
        result.sentiment_score = min(100, max(0, score))
        result.signal_reasons = reasons
        result.risk_factors = risks

        # 生成信号
        if result.sentiment_score >= self.BUY_THRESHOLD:
            result.signal_type = "强烈买入" if result.sentiment_score >= 80 else "买入"
        elif result.sentiment_score >= self.HOLD_THRESHOLD:
            result.signal_type = "持有"
        elif result.sentiment_score >= self.SELL_THRESHOLD:
            result.signal_type = "观望"
        else:
            result.signal_type = "卖出" if result.sentiment_score >= 20 else "强烈卖出"

        # 生成风险等级
        risk_factors_count = len(risks)
        if result.max_drawdown > 30 or risk_factors_count >= 3:
            result.risk_level = "高"
        elif result.max_drawdown > 15 or risk_factors_count >= 1:
            result.risk_level = "中"
        else:
            result.risk_level = "低"

    def _generate_action_checklist(self, result: FundAnalysisResult) -> None:
        """生成操作检查清单"""
        checklist = []

        # 买入检查
        if result.signal_type in ["强烈买入", "买入"]:
            checklist.append("确认买入渠道和费率")
            if result.recent_1m > 5:
                checklist.append("可考虑分批建仓，避免一次性投入")
            if result.ranking_percent >= 70:
                checklist.append("同类排名优秀，可适当提高配置比例")
            if result.manager_stability == "稳定":
                checklist.append("基金经理稳定，适合长期持有")

        # 持有检查
        elif result.signal_type == "持有":
            checklist.append("定期检查净值走势，关注趋势变化")
            if result.max_drawdown > 15:
                checklist.append("注意最大回撤风险，设置止损线")
            if result.scale_alert:
                checklist.append("规模异动需关注，警惕清盘风险")
            checklist.append("与初始买入目标对比，评估是否符合预期")

        # 卖出/观望检查
        elif result.signal_type in ["卖出", "强烈卖出"]:
            checklist.append("评估亏损幅度，考虑止损")
            if result.recent_1m < -5:
                checklist.append("短期跌幅较大，分析下跌原因")
            checklist.append("检查是否需要更换同类更优基金")
            checklist.append("考虑转换成同公司其他基金的可能性")

        # 通用检查
        checklist.append("确认基金类型与自身风险承受能力匹配")
        checklist.append("关注基金经理变动公告")
        checklist.append("定期（季度/半年）复盘基金表现")

        result.action_checklist = checklist

    def format_analysis(self, result: FundAnalysisResult) -> str:
        """
        格式化分析结果为文本

        Args:
            result: 分析结果

        Returns:
            格式化的分析文本
        """
        signal_emoji = {
            "强烈买入": "🟢",
            "买入": "🟢",
            "持有": "🟡",
            "观望": "🟠",
            "卖出": "🔴",
            "强烈卖出": "🔴",
        }.get(result.signal_type, "⚪")

        risk_emoji = {
            "低": "🟢",
            "中": "🟡",
            "高": "🔴",
        }.get(result.risk_level, "⚪")

        lines = [
            f"=== {result.fund_name}({result.fund_code}) 基金诊断 ===",
            f"",
            f"📊 综合评分: {result.sentiment_score}/100",
            f"📌 操作建议: {signal_emoji} {result.signal_type}",
            f"⚠️ 风险等级: {risk_emoji} {result.risk_level}",
            f"",
            f"📈 近期表现:",
            f"   近1月: {result.recent_1m:+.1f}%",
            f"   近3月: {result.recent_3m:+.1f}%",
            f"   近6月: {result.recent_6m:+.1f}%",
            f"   近1年: {result.recent_1y:+.1f}%",
            f"   同类排名: {'前' + str(int(100 - result.ranking_percent)) + '%' if result.ranking_percent > 0 else '暂无数据'}",
            f"",
            f"📉 风险指标:",
            f"   最大回撤: {result.max_drawdown:.1f}%",
            f"   年化波动率: {result.volatility:.1f}%",
            f"   夏普比率: {result.sharpe_ratio:.2f}" if result.sharpe_ratio != 0 else "   夏普比率: 暂无",
            f"",
            f"👤 基金经理:",
            f"   姓名: {result.manager_name or '暂无'}",
            f"   任职年限: {result.manager_tenure_years:.1f}年" if result.manager_tenure_years > 0 else "   任职年限: 暂无",
            f"   管理基金数: {result.manager_funds_count}只" if result.manager_funds_count > 0 else "   管理基金数: 暂无",
            f"   稳定性: {result.manager_stability}",
            f"",
            f"📦 规模情况:",
            f"   当前规模: {result.scale_current:.2f}亿元" if result.scale_current > 0 else "   当前规模: 暂无",
            f"   较上期: {result.scale_change_pct:+.1f}%" if result.scale_current > 0 else "   较上期: 暂无",
            f"   异动警告: {'是' if result.scale_alert else '否'}",
            f"",
        ]

        if result.signal_reasons:
            lines.append(f"✅ 买入理由:")
            for reason in result.signal_reasons:
                lines.append(f"   {reason}")

        if result.risk_factors:
            lines.append(f"")
            lines.append(f"⚠️ 风险因素:")
            for risk in result.risk_factors:
                lines.append(f"   {risk}")

        if result.action_checklist:
            lines.append(f"")
            lines.append(f"📋 操作检查清单:")
            for item in result.action_checklist:
                lines.append(f"   - {item}")

        return "\n".join(lines)


def analyze_fund(fund_code: str, data: Dict[str, Any]) -> FundAnalysisResult:
    """
    便捷函数：分析单只基金

    Args:
        fund_code: 基金代码
        data: 基金数据

    Returns:
        FundAnalysisResult 分析结果
    """
    analyzer = FundTrendAnalyzer()
    return analyzer.analyze(fund_code, data)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # 模拟数据测试
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
    print(analyzer.format_analysis(result))
    print("\n" + "=" * 50)
    print(f"Schema 输出: {result.to_schema().model_dump()}")
