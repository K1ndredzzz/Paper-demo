cd D:\Code_new\Paper\6_Stata_Reg\RoBERTa_330
import delimited "D:\Code_new\Paper\6_Stata_Reg\RoBERTa_330\stock_daily_sentiment.csv", clear

/**************************数据整理**************************/
encode date ,gen(time)
xtset stock_code time

/*描述性统计*/
asdoc summarize, save(描述性统计_相关性分析_多重共线性检验_F检验_Hausman检验_3d.doc) replace

/*相关性分析*/
asdoc pwcorr forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate,sig star(.05)

/*多重共线性检验*/
reg forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate, r
asdoc vif


/**************************模型选择检验**************************/
//混合效应模型
reg forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate
est store ols
//随机效应模型
xtreg forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate, re
est store re
//固定效应模型
asdoc xtreg forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate, fe
est store fe
//F检验(固定效应vs混合OLS)检验个体固定效应 ，F检验表明个体固定效应优于混合ols模型 ，p<0.05表示个体效应显著，固定效应更好
asdoc hausman fe re
//Hausman检验(固定效应vs随机效应)，结果拒绝原假设，选用固定效应模型 p<0.05固定效应，大于0.05 随机效应

/*检验结果，应该选择固定效应回归分析*/


/**************************面板回归**************************/
//固定个体效应
qui xtreg forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate, fe
est store FE_Entity

//固定个体&时间效应
qui xtreg forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time, fe
est store FE_Entity_Time
reg2docx FE_Entity FE_Entity_Time using Regression_3d.docx,replace b(%12.4f)t(%12.4f)drop(*.time)scalars(N r2 F)title(PanelReg_1)note(***p<0.01，**p<0.05，*p<0.10)

//交易量、交易额、换手率
qui xtreg volume avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close amplitude pct_change price_change i.time, fe
est store VOL
qui xtreg amount avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amplitude pct_change price_change i.time, fe
est store AMO
qui xtreg turnover_rate avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amplitude pct_change price_change i.time, fe
est store TR
reg2docx VOL AMO TR using Regression_3d.docx,append b(%12.4f)t(%12.4f)drop(*.time)scalars(N r2 F)title(交易量、交易额、换手率)note(***p<0.01，**p<0.05，*p<0.10)


/*异质性分析*/
/**************************分行业回归************************/
levelsof board_code, local(boards)

foreach i in `boards' {
    quietly xtreg forward_ret_3d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.time if board_code==`i', fe
    estimates store Industry_`i'
}

local estlist ""
foreach i in `boards' {
    local estlist "`estlist' Industry_`i'"
}

reg2docx `estlist' using regression_3d.docx, append b(%9.3f) t(%9.3f) drop(*.time) scalars(N r2 F) title(分行业回归) note(***p<0.01，**p<0.05，*p<0.10)


/*内生性检验*/
/**************************工具变量法**************************/
ivregress 2sls forward_ret_3d (avg_sentiment=L.avg_sentiment L2.avg_sentiment L3.avg_sentiment) sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude pct_change price_change turnover_rate i.stock_code i.time, first cluster(stock_code)
est store IV
reg2docx IV using regression_3d.docx, append b(%12.4f)t(%12.4f)drop(*.stock_code *.time)scalars(N r2 F)title(IV)note(***p<0.01，**p<0.05，*p<0.10)