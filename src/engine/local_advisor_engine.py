"""Local AI Advisor Engine.

Generates professional investment analysis using rule-based templates
and portfolio data — no external API calls required.

Produces the same structured AdvisorResponse as the Claude-based agent,
but entirely offline with deterministic, data-driven output.
"""

from src.models.advisor import AdvisorContext, AdvisorResponse, RiskItem, ScenarioItem

# ── Risk-level-aware templates ────────────────────────────────────────────

RISK_PROFILE_DESCRIPTIONS = {
    "conservative": {
        "label": "保守型",
        "philosophy": "本金安全优先，追求稳定收益，严格控制波动和回撤",
        "strategy": "以债券等固定收益类资产为核心，辅以少量权益类资产增强收益，同时配置黄金对冲通胀风险",
        "suitable_for": "退休人群、风险厌恶型投资者、短期内有明确资金需求的人士",
        "rebalance": "每季度检查一次配置比例，当权益类资产偏离目标配置超过2%时进行再平衡",
    },
    "moderate": {
        "label": "稳健型",
        "philosophy": "在控制风险的前提下追求适度增值，平衡安全性和收益性",
        "strategy": "债券为底仓提供稳定收益，权益类资产作为增长引擎，黄金作为避险工具分散风险",
        "suitable_for": "中年投资者、有中长期理财目标的家庭、倾向于稳健增值的机构投资者",
        "rebalance": "每半年检查一次配置比例，当任一类资产偏离目标配置超过5%时进行再平衡",
    },
    "balanced": {
        "label": "平衡型",
        "philosophy": "平衡风险与收益，追求长期资本增值的同时保持适度的下行保护",
        "strategy": "股债均衡配置，利用两者之间的低相关性降低组合波动，黄金和现金提供流动性和危机保护",
        "suitable_for": "中年职场人士、有5年以上投资期限的投资者、追求财富稳健增长的个人",
        "rebalance": "每半年进行一次定期再平衡，市场大幅波动时（单类资产涨跌超10%）触发临时再平衡",
    },
    "growth": {
        "label": "成长型",
        "philosophy": "以长期资本增值为核心目标，接受中高波动以换取更高预期收益",
        "strategy": "以权益类资产为主导，通过跨市场和跨风格的分散配置降低个股风险，债券作为组合稳定器",
        "suitable_for": "年轻专业人士、投资期限10年以上的投资者、对市场波动有较高承受能力的人士",
        "rebalance": "每年进行一次再平衡，除非市场出现极端行情（单类资产涨跌超15%）否则避免频繁调整",
    },
    "aggressive": {
        "label": "激进型",
        "philosophy": "最大化长期资本增值，接受显著波动和较大回撤，追求超越市场平均的回报",
        "strategy": "高比例配置权益类资产，通过精选宽基和行业ETF捕捉市场超额收益，少量债券和黄金仅作为极端情况下的缓冲",
        "suitable_for": "年轻投资者、有长期投资视野（15年以上）、高净值且现金流充裕的人士",
        "rebalance": "每年进行一次评估，容忍较高偏离度（20%以内），避免因频繁交易侵蚀收益",
    },
}

RISK_RECOMMENDATIONS = {
    "conservative": {
        "dos": [
            "优先配置短期国债和高评级公司债，降低利率风险",
            "选择费用率低于0.2%的ETF，减少持有成本对收益的侵蚀",
            "建立6-12个月生活开支的现金储备，应对突发流动性需求",
            "考虑阶梯式债券配置（laddering strategy），分散到期日以管理利率风险",
        ],
        "donts": [
            "不要因短期市场波动而恐慌性抛售",
            "不要追逐高收益产品而忽视本金安全",
            "避免投资流动性差的资产",
        ],
    },
    "moderate": {
        "dos": [
            "定期定额投资（定投），平滑市场波动对买入成本的影响",
            "配置一定比例的TIPS（通胀保护债券），对冲长期通胀风险",
            "保持5-10%的现金仓位，在市场回调时有资金可以加仓",
            "关注组合的税收效率，优先在免税账户中持有高收益资产",
        ],
        "donts": [
            "不要集中投资单一行业或地区的ETF",
            "避免在市场高位时大幅加仓权益类资产",
            "不要忽视再平衡——漂移的组合会偏离你的风险目标",
        ],
    },
    "balanced": {
        "dos": [
            "采用核心-卫星策略：核心仓位（70-80%）持有宽基指数ETF，卫星仓位配置行业/主题ETF",
            "每年进行一次税务亏损收割（tax-loss harvesting），优化税后收益",
            "监控组合的相关性结构，确保各类资产之间保持有效的分散化",
            "根据生命周期变化（如结婚、购房）动态调整目标配置",
        ],
        "donts": [
            "不要因短期表现不佳而频繁调整策略",
            "避免在市场狂热时大幅超配热门板块",
            "不要忽视国际分散——美股之外也应关注全球市场",
        ],
    },
    "growth": {
        "dos": [
            "考虑配置一定比例的国际股票ETF（如VXUS），获取全球增长红利",
            "在债券部分适当增加高收益债和新兴市场债的敞口，提升固定收益端的回报",
            "利用市场大幅回撤（>20%）作为加仓机会，分批买入降低平均成本",
            "每季度审视组合，确保投资逻辑仍然成立",
        ],
        "donts": [
            "不要使用杠杆或保证金交易放大风险",
            "避免过度交易——频繁买卖会显著侵蚀收益",
            "不要因FOMO（错失恐惧）而追高买入",
        ],
    },
    "aggressive": {
        "dos": [
            "分散配置于不同市值（大盘/中盘/小盘）和不同风格（价值/成长）的ETF",
            "关注新兴市场和前沿市场的长期增长机会，适当配置国际ETF",
            "在市场深度回调（>30%）时，考虑将部分现金和债券仓位转换为权益",
            "定期跟踪组合相对于基准（如S&P 500或MSCI ACWI）的超额收益",
        ],
        "donts": [
            "不要将所有资金一次性投入——分批建仓降低择时风险",
            "避免重仓单一行业或主题ETF（如仅持有科技股），即使看好也要分散",
            "不要忽视尾部风险——配置至少5%的避险资产",
        ],
    },
}

# ── Risk analysis by asset class ──────────────────────────────────────────

def _build_risks(ctx: AdvisorContext) -> list[RiskItem]:
    """Generate risk items based on portfolio composition and risk level."""

    risk_level = ctx.risk_level
    equity_pct = float(ctx.class_weights.get("股票", "0"))
    bond_pct = float(ctx.class_weights.get("债券", "0"))

    risks = []

    # Market risk — affects all but scales with equity exposure
    if equity_pct > 50:
        risks.append(RiskItem(
            risk_name="市场系统性风险",
            severity="high",
            description=f"权益类资产占比{equity_pct:.0f}%，组合净值将随股市波动显著变化。在全球经济衰退或金融危机情景下，"
                        f"组合可能面临{ctx.max_drawdown_pct}%甚至更高的回撤。历史数据显示，美股主要指数在2008年和2020年分别回撤超过50%和30%。",
            mitigation="通过跨市场和跨资产类别的分散配置降低系统性风险；在市场极端高估时适度降低权益仓位；"
                       "使用止损策略保护极端下行风险。",
        ))
    elif equity_pct > 25:
        risks.append(RiskItem(
            risk_name="市场系统性风险",
            severity="medium",
            description=f"权益类资产占比{equity_pct:.0f}%，组合对市场波动有一定敞口。在中等幅度的市场调整中（10-20%回调），"
                        f"组合预计将受到可控影响。主要风险来源于全球经济增长放缓和地缘政治不确定性。",
            mitigation="保持股债平衡，在权益市场大幅上涨后适度再平衡；关注VIX等恐慌指标，在市场极端恐慌时保持冷静。",
        ))
    else:
        risks.append(RiskItem(
            risk_name="市场系统性风险",
            severity="low",
            description=f"权益类资产仅占{equity_pct:.0f}%，组合整体波动较低，对股市大幅回调有较强防御能力。"
                        f"主要风险敞口来自于债券市场的利率变动。",
            mitigation="关注美联储政策动向和通胀数据，及时调整债券久期；保持少量权益敞口以对抗通胀。",
        ))

    # Inflation risk — bigger issue for conservative portfolios
    if equity_pct < 30:
        risks.append(RiskItem(
            risk_name="通货膨胀侵蚀风险",
            severity="high",
            description=f"当前组合预期收益率为{ctx.expected_return_pct}%，在通胀持续高于3%的环境下，"
                        f"实际购买力可能不增反降。以30年维度计算，3%的年通胀率将使¥100的购买力下降至约¥41。"
                        f"固定收益类资产对此风险尤为敏感。",
            mitigation="适当增加通胀保护债券（TIPS）和实物资产（黄金、大宗商品ETF）的配置；"
                       "考虑将少量资金配置于权益类资产以获取长期通胀对冲。",
        ))
    elif equity_pct < 60:
        risks.append(RiskItem(
            risk_name="通货膨胀侵蚀风险",
            severity="medium",
            description=f"组合中债券占{bond_pct:.0f}%，在通胀超预期时固定收益部分的实际回报将受损。"
                        f"虽然权益类资产长期能对冲通胀，但短期内通胀超预期可能导致美联储加速加息，对股债形成双重压力。",
            mitigation="配置TIPS和黄金ETF作为通胀对冲工具；关注实际收益率而非名义收益率；"
                       "在通胀预期上升时缩短债券久期。",
        ))
    else:
        risks.append(RiskItem(
            risk_name="通货膨胀侵蚀风险",
            severity="low",
            description="权益类资产长期来看能够有效对冲通胀风险，因为公司可以将成本上涨转嫁给消费者。"
                       "但短期内，超预期的通胀仍可能通过货币政策收紧对组合估值产生负面影响。",
            mitigation="保持黄金配置作为极端通胀情景下的保险；关注美联储FOMC会议和CPI数据发布。",
        ))

    # Interest rate / duration risk
    if bond_pct > 30:
        risks.append(RiskItem(
            risk_name="利率上行风险",
            severity="high" if bond_pct > 50 else "medium",
            description=f"债券类资产占比{bond_pct:.0f}%，对利率变动高度敏感。若美联储加息100个基点，"
                        f"长久期债券ETF（如TLT）可能面临15-20%的价格下跌。2022年美联储激进加息期间，"
                        f"美国综合债券指数全年跌幅超过13%，为近50年最差表现。",
            mitigation="采用债券阶梯配置策略，混合短久期和长久期债券ETF；"
                       "在加息周期中缩短久期，降息周期中延长久期；关注美联储点阵图和利率期货定价。",
        ))
    elif bond_pct > 10:
        risks.append(RiskItem(
            risk_name="利率上行风险",
            severity="medium",
            description=f"债券类资产占比{bond_pct:.0f}%，利率上升对组合有一定影响但整体可控。"
                        f"部分长久期债券ETF对利率变动较为敏感，需持续关注美联储政策路径。",
            mitigation="定期审查债券组合的久期结构；在加息预期升温时适当增加浮息债和短久期债券。",
        ))

    # Concentration risk
    risks.append(RiskItem(
        risk_name="集中度风险",
        severity="medium",
        description="组合中部分ETF（如追踪标普500指数的SPY/IVV）对大市值科技股有较高集中度。"
                   "截至近期，Magnificent 7（苹果、微软、英伟达、亚马逊、谷歌、Meta、特斯拉）"
                   "合计占标普500权重超过30%。若科技行业出现调整，组合将受到不成比例的影响。",
        mitigation="配置等权重指数ETF或中小盘ETF（如IWM）分散大市值集中风险；"
                   "定期检查前十大持仓的权重占比；考虑配置国际股票ETF（VXUS）降低对美股的单一依赖。",
    ))

    # Specific risks based on risk level
    if risk_level == "conservative":
        risks.append(RiskItem(
            risk_name="收益不足风险",
            severity="medium",
            description=f"保守型组合预期收益{ctx.expected_return_pct}%，在扣除管理费和通胀后，"
                        f"实际净收益可能难以满足长期财务目标（如退休规划、子女教育）。"
                        f"若投资期限为{ctx.horizon_years}年，复利效应不足可能导致退休时资产缺口。",
            mitigation="考虑在风险承受范围内将权益配置从下限向上限小幅调整；"
                       "增加储蓄率作为收益不足的补充；定期（每年）评估实际收益与目标的差距。",
        ))
    elif risk_level == "aggressive":
        risks.append(RiskItem(
            risk_name="行为偏差风险",
            severity="high",
            description="激进型组合波动率较高，在市场大幅下跌时投资者容易因恐慌而做出非理性决策"
                       "（如底部割肉），导致永久性资本损失。行为金融学研究表明，"
                       "个人投资者在市场极端波动时的操作往往是亏损的主要来源。",
            mitigation="预设投资计划和规则（如定投、再平衡规则），在市场波动时严格按计划执行；"
                       "在市场恐慌时避免频繁查看账户；考虑寻求专业投资顾问的情感支持。",
        ))

    return risks


def _build_scenarios(ctx: AdvisorContext) -> list[ScenarioItem]:
    """Build market scenario analysis based on portfolio composition."""

    ret = float(ctx.expected_return_pct)
    vol = float(ctx.volatility_pct)

    scenarios = []

    # Bull scenario
    bull_ret = ret + vol * 1.5
    bull_desc = (
        f"在经济持续增长、企业盈利超预期、货币政策宽松的背景下，权益类资产表现出色。"
        f"该组合凭借合理的风险资产敞口，预计可实现{bull_ret:.1f}%左右的年化回报。"
        f"权益类ETF（如SPY、QQQ）将成为主要收益贡献者，债券部分提供稳定的利息收入。"
        f"若以¥{ctx.initial_amount}初始投资计算，{ctx.horizon_years}年后组合价值有望达到"
        f"约¥{int(float(ctx.percentile_95.replace(',', '')))}（接近95%置信度上限）。"
    )
    scenarios.append(ScenarioItem(
        scenario="牛市",
        probability="中低 (约15-25%)",
        description=bull_desc,
        projected_impact=f"组合年化回报预计可达{bull_ret:.1f}%，权益类资产为主要驱动力。"
                         f"建议在市场上涨过程中适度再平衡，将部分盈利转入债券以锁定收益。",
    ))

    # Bear scenario
    bear_ret = ret - vol * 1.5
    bear_desc = (
        f"在经济衰退、企业盈利下滑、地缘政治风险加剧的背景下，全球风险资产面临抛售压力。"
        f"该组合预计可能出现{bear_ret:.1f}%的年度损失。权益类资产跌幅最为显著，"
        f"债券和黄金将发挥避险功能，部分对冲股票损失。"
        f"Monte Carlo模拟的5%分位数显示，{ctx.horizon_years}年后的资产终值约为"
        f"¥{ctx.percentile_5}。重要的是，即使在悲观情景下，分散化的组合也比"
        f"集中投资单一资产类别的损失更可控。"
    )
    scenarios.append(ScenarioItem(
        scenario="熊市",
        probability="中低 (约15-20%)",
        description=bear_desc,
        projected_impact=f"组合可能承受{bear_ret:.1f}%的年度损失。债券和黄金提供下行缓冲。"
                         f"建议在市场恐慌时保持纪律，按计划定投或逢低加仓优质ETF。",
    ))

    # Sideways scenario
    sideways_desc = (
        f"在市场横盘震荡、多空力量均衡的环境下，该组合预计可获得{ret:.1f}%左右的年化回报，"
        f"主要依赖债券利息和股票股息等「carry」收益。此情景下选股能力让位于资产配置的纪律性，"
        f"定期再平衡将成为超额收益的重要来源——通过卖出相对强势的资产、买入相对弱势的资产，"
        f"在震荡中持续收获再平衡溢价（Rebalancing Premium）。"
        f"Monte Carlo模拟的中位数显示，{ctx.horizon_years}年后预期终值约为¥{ctx.median_final}。"
    )
    scenarios.append(ScenarioItem(
        scenario="震荡市",
        probability="高 (约55-65%)",
        description=sideways_desc,
        projected_impact=f"组合年化回报预计在{ret:.1f}%左右。再平衡纪律和成本控制是此情景下超额收益的关键来源。"
                         f"建议保持耐心，避免频繁交易，让复利效应随着时间发挥作用。",
    ))

    return scenarios


# ── Main engine ────────────────────────────────────────────────────────────

def generate_advisor_response(ctx: AdvisorContext) -> AdvisorResponse:
    """Generate a full AI advisor response using local rule-based engine.

    Args:
        ctx: AdvisorContext with portfolio data, simulation results,
             and user preferences.

    Returns:
        AdvisorResponse with structured analysis — same format as Claude API output.
    """

    risk_level = ctx.risk_level
    profile = RISK_PROFILE_DESCRIPTIONS.get(risk_level, RISK_PROFILE_DESCRIPTIONS["balanced"])

    # ── Summary ────────────────────────────────────────────────────────────
    equity_pct = float(ctx.class_weights.get("股票", "0"))
    bond_pct = float(ctx.class_weights.get("债券", "0"))
    gold_pct = float(ctx.class_weights.get("黄金", "0"))

    summary = (
        f"您的{profile['label']}投资组合（风险评分{ctx.risk_score_pct}分）遵循"
        f"「{profile['philosophy']}」的投资理念。当前配置中，股票类资产占{equity_pct:.0f}%、"
        f"债券类占{bond_pct:.0f}%、黄金占{gold_pct:.0f}%。"
        f"组合预期年化收益率为{ctx.expected_return_pct}%，年化波动率{ctx.volatility_pct}%，"
        f"夏普比率{ctx.sharpe_ratio}，风险调整后收益处于合理水平。"
        f"基于{ctx.horizon_years}年期Monte Carlo模拟（{ctx.initial_amount}初始投资），"
        f"资产终值中位数为¥{ctx.median_final}，实现正收益的概率为{ctx.probability_positive_pct}%。"
    )

    # ── Allocation Rationale ───────────────────────────────────────────────
    allocation_rationale = (
        f"该投资组合的核心策略是：{profile['strategy']}。\n\n"

        f"**为什么权益类配置{equity_pct:.0f}%？** "
        f"根据您的{profile['label']}风险等级，权益类资产的目标配置区间为"
    )

    # Add asset class details based on what's in the portfolio
    asset_details = []
    for cls_label, cls_pct in ctx.class_weights.items():
        cls_pct_val = float(cls_pct)
        if cls_pct_val > 0.5:
            continue
        if "股票" in cls_label or "equity" in cls_label.lower():
            asset_details.append(
                f"股票类（{cls_pct}%）作为组合的「增长引擎」，通过分散投资于美国大盘股（SPY）、"
                f"科技股（QQQ）、全市场（VTI）等宽基ETF，以较低成本获取市场Beta收益。"
            )
        elif "债券" in cls_label or "bond" in cls_label.lower():
            asset_details.append(
                f"债券类（{cls_pct}%）作为组合的「稳定器」，配置综合债（AGG）、长期国债（TLT）、"
                f"投资级公司债（LQD）和通胀保护债（TIP），提供稳定的票息收入并在股市下跌时起到对冲作用。"
            )
        elif "黄金" in cls_label or "gold" in cls_label.lower():
            asset_details.append(
                f"黄金（{cls_pct}%）作为「避险资产」，在通胀超预期和地缘政治风险上升时提供保护。"
                f"黄金与股票和债券的相关性较低，能有效改善组合的风险收益特征。"
            )
        elif "现金" in cls_label or "cash" in cls_label.lower():
            asset_details.append(
                f"现金/货币基金（{cls_pct}%）提供流动性和灵活性，可用于市场回调时加仓或应对突发资金需求。"
            )

    allocation_rationale += "\n\n".join(asset_details)

    allocation_rationale += (
        f"\n\n**现代投资组合理论（MPT）的实践**：该组合建立在Harry Markowitz的均值-方差优化框架之上。"
        f"通过选择相关性较低的资产类别，组合实现了在给定风险（波动率{ctx.volatility_pct}%）下"
        f"最大化预期收益（{ctx.expected_return_pct}%），或在给定收益目标下最小化风险。"
        f"夏普比率{ctx.sharpe_ratio}表明，组合每承担1%的波动风险，可获得约"
        f"{float(ctx.sharpe_ratio):.1f}%的超额收益补偿（相对于{3}%无风险利率）。"
    )

    # ── Key Risks ──────────────────────────────────────────────────────────
    key_risks = _build_risks(ctx)

    # ── Market Scenarios ───────────────────────────────────────────────────
    market_scenarios = _build_scenarios(ctx)

    # ── Investment Recommendations ─────────────────────────────────────────
    recs = RISK_RECOMMENDATIONS.get(risk_level, RISK_RECOMMENDATIONS["balanced"])

    dos_text = "\n".join([f"- {d}" for d in recs["dos"]])
    donts_text = "\n".join([f"- {d}" for d in recs["donts"]])

    investment_recommendations = (
        f"基于您的{profile['label']}风险特征和{ctx.horizon_years}年投资期限，以下是具体建议：\n\n"
        f"**✅ 应该做的：**\n{dos_text}\n\n"
        f"**❌ 应该避免的：**\n{donts_text}\n\n"
        f"**📋 再平衡方案：**{profile['rebalance']}\n\n"
        f"**💡 针对您的投资目标「{ctx.investment_goal}」，额外建议：**\n"
        f"- 将投资目标拆分为短期（1-3年）、中期（3-7年）和长期（7年以上）三个层次，分别匹配不同的风险预算\n"
        f"- 建议每月或每季度定额投入新增资金，利用平均成本法（DCA）降低择时风险\n"
        f"- 每年度回顾投资目标的进展，根据实际情况（收入变化、家庭状况、市场环境）调整储蓄率和配置方案\n"
        f"- 建议将投资组合的总费用率控制在0.3%以下，长期来看能显著提升净收益"
    )

    # ── Disclaimer ─────────────────────────────────────────────────────────
    disclaimer_note = (
        "⚠️ 投资有风险，过往表现不代表未来收益。本分析基于历史数据和统计模型（Geometric Brownian Motion）"
        "生成，实际投资结果可能与模拟结果存在重大差异。Monte Carlo模拟基于假设的预期收益和波动率参数，"
        "这些参数可能随市场条件变化而发生显著改变。本报告中的任何内容均不构成投资建议、"
        "税务建议或法律建议。在做出任何投资决策前，建议咨询持牌的专业投资顾问。"
        "请根据自身的财务状况、风险承受能力和投资目标审慎做出投资决策。"
    )

    return AdvisorResponse(
        summary=summary,
        allocation_rationale=allocation_rationale,
        key_risks=key_risks,
        market_scenarios=market_scenarios,
        investment_recommendations=investment_recommendations,
        disclaimer_note=disclaimer_note,
    )
