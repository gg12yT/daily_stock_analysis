# 基金智能分析系统 - 股票版改造说明

## 概述

本文档说明如何将现有的 `daily_stock_analysis` 项目从股票分析扩展到基金分析。
主要涉及文件：`main.py`、`src/analyzer.py`、`apps/dsa-web`。

---

## 1. main.py 改造说明

### 1.1 需要修改的股票相关逻辑

#### 1.1.1 入口参数扩展

**现状：** 只接受股票代码输入
```python
# 原代码
parser.add_argument("--codes", nargs="+", help="股票代码列表")
```

**建议修改：** 增加基金代码识别和参数
```python
parser.add_argument("--codes", nargs="+", help="股票或基金代码列表")
parser.add_argument("--fund-mode", action="store_true", help="基金分析模式")
parser.add_argument("--stock-mode", action="store_true", help="股票分析模式（默认）")
```

#### 1.1.2 代码类型识别

**新增函数：**
```python
def is_fund_code(code: str) -> bool:
    """判断是否为基金代码"""
    # 基金代码通常为6位数字，以特定前缀开头
    # 场外基金：000001-999999
    # 基金代码规则可通过 akshare 的 fund_name_em() 获取全量列表后匹配
    return len(code) == 6 and code.isdigit()

def detect_code_type(codes: List[str]) -> Tuple[List[str], List[str]]:
    """分离股票代码和基金代码"""
    stock_codes = []
    fund_codes = []
    for code in codes:
        if is_fund_code(code):
            fund_codes.append(code)
        else:
            stock_codes.append(code)
    return stock_codes, fund_codes
```

#### 1.1.3 分析流程分支

**现状：** 统一调用股票分析流程
```python
# 原代码
analyze_stocks(codes)
```

**建议修改：** 分流到不同分析器
```python
stock_codes, fund_codes = detect_code_type(codes)
if stock_codes:
    analyze_stocks(stock_codes)
if fund_codes:
    analyze_funds(fund_codes)
```

#### 1.1.4 分析结果处理

**现状：** 统一生成股票报告
```python
# 原代码
generate_stock_report(results)
```

**建议修改：** 分别生成报告
```python
if stock_codes:
    generate_stock_report(stock_results)
if fund_codes:
    generate_fund_report(fund_results)
```

---

## 2. src/analyzer.py 改造说明

### 2.1 需要修改的 Prompt

#### 2.1.1 新增基金分析 System Prompt

**建议新增：**
```python
FUND_SYSTEM_PROMPT = """
你是一位专业的基金分析师，基于以下数据进行分析：

【基金数据】
{fund_data}

【分析维度】
1. 净值趋势：近1月/3月/6月/1年涨幅
2. 同类排名：相对于同类基金的排名百分位
3. 风险指标：最大回撤、波动率、夏普比率
4. 基金经理：任职年限、管理稳定性
5. 规模变动：规模异动检测

【输出格式】
请以 JSON 格式输出完整的分析报告，结构如下：
{
  "fund_code": "基金代码",
  "fund_name": "基金名称",
  "sentiment_score": 综合评分(0-100),
  "signal_type": "买入/持有/卖出",
  "risk_level": "低/中/高",
  "dashboard": {
    "core_conclusion": {
      "one_sentence": "一句话结论",
      "signal_type": "信号类型",
      "risk_level": "风险等级"
    },
    "performance": {...},
    "risk": {...},
    "manager": {...},
    "scale": {...},
    "action_checklist": ["检查项1", "检查项2"]
  }
}

【评分标准】
- 买入：评分 >= 70
- 持有：评分 45-70
- 卖出：评分 < 45

【风险等级】
- 低风险：最大回撤 < 15%，波动率 < 15%
- 中风险：最大回撤 15-25%，波动率 15-20%
- 高风险：最大回撤 > 25%，波动率 > 20%
"""
```

#### 2.1.2 分析器路由

**建议新增函数：**
```python
def analyze_fund_with_llm(fund_code: str, fund_data: Dict) -> FundReportSchema:
    """使用 LLM 分析基金"""
    prompt = FUND_SYSTEM_PROMPT.format(fund_data=json.dumps(fund_data, ensure_ascii=False))
    response = call_llm(prompt)
    return parse_fund_report(response)
```

#### 2.1.3 混合分析入口

```python
def analyze_code(code: str, fetcher_manager) -> Dict:
    """智能分析入口，自动识别股票/基金"""
    if is_fund_code(code):
        # 基金分析流程
        fund_data = fetch_fund_full_analysis(code)
        return analyze_fund_with_llm(code, fund_data)
    else:
        # 股票分析流程（现有逻辑）
        stock_data = fetch_stock_data(code, fetcher_manager)
        return analyze_stock_with_llm(code, stock_data)
```

---

## 3. apps/dsa-web 前端改造说明

### 3.1 需要修改的页面

#### 3.1.1 代码输入页面 (pages/index.tsx)

**现状：** 只接受股票代码
```tsx
// 原代码
<Input placeholder="输入股票代码，如 000001" />
```

**建议修改：** 增加基金代码识别提示
```tsx
<Input 
  placeholder="输入股票代码（如 000001）或基金代码（如 000001）" 
/>
<Tabs>
  <Tab value="stock">股票分析</Tab>
  <Tab value="fund">基金诊断</Tab>
</Tabs>
```

#### 3.1.2 分析结果展示页面

**新增基金诊断卡片组件：**
```tsx
// components/FundReportCard.tsx
interface FundReportCardProps {
  fundCode: string;
  fundName: string;
  signalType: '买入' | '持有' | '卖出';
  sentimentScore: number;
  riskLevel: '低' | '中' | '高';
  performance: {
    recent_1m: number;
    recent_3m: number;
    recent_6m: number;
    recent_1y: number;
    rankingPercent: number;
  };
  risk: {
    maxDrawdown: number;
    volatility: number;
    sharpeRatio: number;
  };
  manager: {
    name: string;
    tenureYears: number;
    stability: string;
  };
  scale: {
    current: number;
    changePct: number;
    alert: boolean;
  };
  actionChecklist: string[];
}
```

**关键 UI 改动：**
- 股票分析使用技术指标卡片（MA/MACD/RSI）
- 基金诊断使用净值表现卡片（收益/风险/经理/规模）
- 新增基金类型筛选（股票型/债券型/混合型/指数型）

#### 3.1.3 路由配置

**新增路由：**
```tsx
// 现有
/analysis/stock/:code

// 建议新增
/analysis/fund/:code
```

#### 3.1.4 API 接口

**新增基金分析接口：**
```typescript
// 新增
POST /api/fund/analyze
Body: { fund_codes: string[] }
Response: FundReportSchema[]

GET /api/fund/list
Response: { funds: Array<{ code: string; name: string; type: string }> }

GET /api/fund/realtime
Query: ?codes=000001,000002
Response: FundRealtimeData[]
```

---

## 4. 其他需要关注的文件

### 4.1 src/formatters.py
- 新增 `format_fund_report()` 函数
- 新增基金报告的飞书文档格式化

### 4.2 src/notification.py
- 新增基金报告的通知模板
- 飞书消息卡片需要支持基金类型

### 4.3 src/scheduler.py
- 新增基金定时分析任务
- 股票和基金可分别设置不同分析周期

### 4.4 docs/FUND_MODIFICATION.md
- 本文档，记录改造进度和注意事项

---

## 5. 改造优先级建议

### 第一阶段（核心框架）
1. ✅ `data_provider/fund_akshare.py` - 基金数据获取
2. ✅ `src/fund_analyzer.py` - 基金分析器
3. ✅ `src/schemas/fund_report_schema.py` - 报告 Schema
4. ✅ `templates/fund_report_markdown.j2` - 报告模板

### 第二阶段（集成到主程序）
1. `main.py` - 增加基金模式入口
2. `src/analyzer.py` - 增加基金分析 Prompt
3. `apps/dsa-web` - 前端页面改造

### 第三阶段（完善功能）
1. `src/formatters.py` - 格式化函数
2. `src/notification.py` - 通知功能
3. `src/scheduler.py` - 定时任务

---

## 6. 注意事项

1. **数据源稳定性**：AkShare 基金接口可能有访问限制，建议添加缓存和重试机制
2. **基金代码识别**：部分基金代码和股票代码可能冲突（都是6位数字），建议通过数据验证确认
3. **性能考虑**：基金分析批量处理时注意接口限流
4. **风险提示**：基金投资有风险，报告中必须包含风险提示
