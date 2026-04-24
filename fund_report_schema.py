# -*- coding: utf-8 -*-
"""
===================================
基金诊断报告 Schema
===================================

定义基金分析报告的数据结构，与 src/schemas/report_schema.py 设计保持一致。
用于验证 LLM 输出的 JSON 报告是否符合预期格式。

使用 Pydantic BaseModel，Optional 字段允许宽松解析。
业务层完整性检查在其他模块处理。
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class FundCoreConclusion(BaseModel):
    """基金核心结论"""
    one_sentence: Optional[str] = None  # 一句话结论
    signal_type: Optional[str] = None   # 买入/持有/卖出
    risk_level: Optional[str] = None    # 风险等级：低/中/高
    time_sensitivity: Optional[str] = None  # 时间敏感性


class FundPerformance(BaseModel):
    """基金收益表现"""
    recent_1m: Optional[float] = None   # 近1月涨幅 (%)
    recent_3m: Optional[float] = None   # 近3月涨幅 (%)
    recent_6m: Optional[float] = None   # 近6月涨幅 (%)
    recent_1y: Optional[float] = None   # 近1年涨幅 (%)
    ranking_percent: Optional[float] = None  # 同类排名百分位 (0-100)


class FundRisk(BaseModel):
    """基金风险指标"""
    max_drawdown: Optional[float] = None  # 最大回撤 (%)
    volatility: Optional[float] = None   # 年化波动率 (%)
    sharpe_ratio: Optional[float] = None  # 夏普比率


class FundManager(BaseModel):
    """基金经理信息"""
    name: Optional[str] = None           # 基金经理姓名
    tenure_years: Optional[float] = None # 任职年限
    funds_count: Optional[int] = None    # 管理基金数
    stability: Optional[str] = None     # 稳定性：稳定/注意/不稳定


class FundScale(BaseModel):
    """基金规模"""
    current: Optional[float] = None     # 当前规模（亿元）
    change_pct: Optional[float] = None  # 较上期变化百分比
    alert: Optional[bool] = None        # 是否异动（变化超30%）


class FundActionChecklist(BaseModel):
    """基金操作检查清单"""
    checklist: Optional[List[str]] = None


class FundDashboard(BaseModel):
    """基金仪表盘（核心数据聚合）"""
    core_conclusion: Optional[FundCoreConclusion] = None
    performance: Optional[FundPerformance] = None
    risk: Optional[FundRisk] = None
    manager: Optional[FundManager] = None
    scale: Optional[FundScale] = None
    action_checklist: Optional[List[str]] = None  # 操作检查清单


class FundReportSchema(BaseModel):
    """
    基金分析报告顶层 Schema
    对应 LLM 报告 JSON 输出格式
    """
    model_config = ConfigDict(extra="allow")  # 允许 LLM 输出额外字段

    fund_code: Optional[str] = None
    fund_name: Optional[str] = None
    fund_type: Optional[str] = None

    # 核心信号
    sentiment_score: Optional[int] = Field(None, ge=0, le=100)  # 综合情绪评分 0-100
    signal_type: Optional[str] = None  # 买入/持有/卖出
    risk_level: Optional[str] = None  # 低/中/高

    # Dashboard
    dashboard: Optional[FundDashboard] = None

    # 补充字段（兼容股票格式）
    analysis_summary: Optional[str] = None
    key_points: Optional[str] = None
    risk_warning: Optional[str] = None
    buy_reason: Optional[str] = None
    operation_advice: Optional[str] = None

    # 趋势预测
    trend_prediction: Optional[str] = None
    medium_term_outlook: Optional[str] = None
    short_term_outlook: Optional[str] = None

    # 分类分析
    performance_analysis: Optional[str] = None
    risk_analysis: Optional[str] = None
    manager_analysis: Optional[str] = None
    scale_analysis: Optional[str] = None

    # 情报
    latest_news: Optional[str] = None
    risk_alerts: Optional[List[str]] = None
    positive_catalysts: Optional[List[str]] = None

    # 搜索标记
    search_performed: Optional[bool] = None
    data_sources: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.model_dump(exclude_none=False)

    def get_signal_display(self) -> str:
        """获取信号显示文本"""
        return {
            "买入": "🟢 买入",
            "持有": "🟡 持有",
            "卖出": "🔴 卖出",
        }.get(self.signal_type or "", "⚪ 待定")

    def get_risk_display(self) -> str:
        """获取风险等级显示"""
        return {
            "低": "🟢 低风险",
            "中": "🟡 中风险",
            "高": "🔴 高风险",
        }.get(self.risk_level or "", "⚪ 未知")

    def get_performance_summary(self) -> str:
        """获取收益摘要"""
        perf = self.dashboard.performance if self.dashboard else None
        if not perf:
            return "暂无数据"
        parts = []
        if perf.recent_1m is not None:
            parts.append(f"近1月 {perf.recent_1m:+.1f}%")
        if perf.recent_3m is not None:
            parts.append(f"近3月 {perf.recent_3m:+.1f}%")
        if perf.recent_1y is not None:
            parts.append(f"近1年 {perf.recent_1y:+.1f}%")
        return " | ".join(parts) if parts else "暂无数据"
