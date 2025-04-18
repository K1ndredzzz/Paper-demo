cd D:\Code_new\Paper\6_Stata_Reg\StructBERT_large
import delimited "D:\Code_new\Paper\6_Stata_Reg\StructBERT_large\stock_daily_sentiment.csv", clear

/**************************数据整理**************************/
encode date ,gen(time)
xtset stock_code time

//drop negative_ratio avg_positive_prob avg_negative_prob sentiment_net open high low ma_5d std_5d sentiment_change_5d ma_10d std_10d sentiment_change_10d


/*描述性统计*/
asdoc summarize, save(描述性统计_相关性分析_多重共线性检验_F检验_Hausman检验_1d.doc) replace

/*单位根检验*/
// ADF-Fisher检验
xtunitroot fisher forward_ret_1d, dfuller lags(2)
xtunitroot fisher avg_sentiment, dfuller lags(2)
// 或使用IPS检验
xtunitroot ips forward_ret_1d, lags(aic 3)
xtunitroot ips avg_sentiment, lags(aic 3)

/*协整检验*/
xtcointtest kao forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus

/*相关性分析*/
asdoc pwcorr forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate,sig star(.05)

/*多重共线性检验*/
reg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate, r
asdoc vif


/**************************模型选择检验**************************/
//混合效应模型
reg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate
est store ols
//随机效应模型
xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate, re
est store re
//固定效应模型
asdoc xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate, fe
est store fe
//F检验(固定效应vs混合OLS)检验个体固定效应 ，F检验表明个体固定效应优于混合ols模型 ，p<0.05表示个体效应显著，固定效应更好
asdoc hausman fe re
//Hausman检验(固定效应vs随机效应)，结果拒绝原假设，选用固定效应模型 p<0.05固定效应，大于0.05 随机效应

/*检验结果，应该选择固定效应回归分析*/


/**************************主要实证结果**************************/
//固定个体效应
xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate, fe
est store FE_Entity
//固定个体&时间效应
xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time
//固定个体效应加行业
xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate idx_close idx_volume idx_amount idx_pct_change, fe
est store FE_Entity_IND
//固定个体&时间效应加行业
xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate idx_close idx_volume idx_amount idx_pct_change i.time, fe
est store FE_Entity_Time_IND

reg2docx FE_Entity FE_Entity_Time FE_Entity_IND FE_Entity_Time_IND using Regression_1d.docx,replace b(%12.4f)t(%12.4f)drop(*.time)scalars(N r2 F)title(PanelReg_1)note(***p<0.01，**p<0.05，*p<0.10)


/**************************机制分析**************************/
xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close amplitude pct_change price_change i.time, fe
est store FE_Entity_Time_without_VOL
//交易量、交易额、换手率
qui xtreg volume avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close amplitude pct_change price_change i.time, fe
est store VOL
qui xtreg amount avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amplitude pct_change price_change i.time, fe
est store AMO
qui xtreg turnover_rate avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amplitude pct_change price_change i.time, fe
est store TR
xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time
reg2docx FE_Entity_Time_without_VOL VOL FE_Entity_Time using Regression_1d.docx,append b(%12.4f)t(%12.4f)drop(*.time)scalars(N r2 F)title(交易量、交易额、换手率)note(***p<0.01，**p<0.05，*p<0.10)
reg2docx VOL AMO TR using Regression_1d.docx,append b(%12.4f)t(%12.4f)drop(*.time)scalars(N r2 F)title(交易量、交易额、换手率)note(***p<0.01，**p<0.05，*p<0.10)


/**************************异质性分析**************************/
/*分行业回归*/
levelsof board_code, local(boards)

foreach i in `boards' {
    quietly xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time if board_code==`i', fe
    estimates store Industry_`i'
}

local estlist ""
foreach i in `boards' {
    local estlist "`estlist' Industry_`i'"
}

reg2docx `estlist' using regression_1d.docx, append b(%9.3f) t(%9.3f) drop(*.time) scalars(N r2 F) title(分行业回归) note(***p<0.01，**p<0.05，*p<0.10)


/**************************内生性处理**************************/
//工具变量法
/*ivregress 2sls forward_ret_1d (avg_sentiment=L.avg_sentiment L2.avg_sentiment L3.avg_sentiment) sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.stock_code i.time, first cluster(stock_code)
est store IV
reg2docx IV using regression_1d.docx, append b(%12.4f)t(%12.4f)drop(*.stock_code *.time)scalars(N r2 F)title(IV)note(***p<0.01，**p<0.05，*p<0.10)*/
//Granger因果检验
pvar2 forward_ret_1d avg_sentiment ,lag(3) soc
xtgcause forward_ret_1d avg_sentiment, lags(2)
//pvar2 forward_ret_1d avg_sentiment ,lag(2) granger


/**************************稳健性检验**************************/
/*替换解释变量*/
//positive_ratio
xtreg forward_ret_1d positive_ratio sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time_PR
//ma_3d
xtreg forward_ret_1d ma_3d std_3d sentiment_change_3d avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time_ma_3d
//ma_3d
xtreg forward_ret_1d ma_5d std_5d sentiment_change_5d avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time_ma_5d
reg2docx FE_Entity_Time FE_Entity_Time_PR FE_Entity_Time_ma_3d FE_Entity_Time_ma_5d using Regression_1d.docx,append b(%12.4f)t(%12.4f)drop(*.time)scalars(N r2 F)title(positive_ratio与ma_3d对比avg_sentiment)note(***p<0.01，**p<0.05，*p<0.10)
/*替换被解释变量*/
//3d
xtreg forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time_3d
//5d
xtreg forward_ret_5d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time_5d
reg2docx FE_Entity_Time FE_Entity_Time_3d FE_Entity_Time_5d using Regression_1d.docx,append b(%12.4f)t(%12.4f)drop(*.time)scalars(N r2 F)title(ret_3/5d对比1d)note(***p<0.01，**p<0.05，*p<0.10)
/*
//滞后1期
xtreg forward_ret_1d L.avg_sentiment L.sentiment_std L.avg_intensity L.comment_count L.sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time_1
//滞后2期
xtreg forward_ret_1d L2.forward_ret_1d L2.avg_sentiment L2.sentiment_std L2.avg_intensity L2.comment_count L2.sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time_2
//滞后3期
xtreg forward_ret_1d L2.forward_ret_1d L3.forward_ret_1d L3.avg_sentiment L3.sentiment_std L3.avg_intensity L3.comment_count L3.sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time_3
reg2docx FE_Entity FE_Entity_Time FE_Entity_Time_1 FE_Entity_Time_2 FE_Entity_Time_3 using Regression_1d.docx,replace b(%12.4f)t(%12.4f)drop(*.time)scalars(N r2 F)title(PanelReg_1)note(***p<0.01，**p<0.05，*p<0.10)
*/
