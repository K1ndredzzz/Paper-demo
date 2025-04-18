* 步骤一：数据导入与准备
import delimited "stock_daily_sentiment.csv", clear 
encode stock_code, gen(stock_id)
encode industry, gen(industry_id)
xtset stock_id date

* 步骤一：单位根检验
* LLC检验
xtunitroot llc avg_sentiment
xtunitroot llc sentiment_std 
xtunitroot llc positive_ratio
xtunitroot llc volume
xtunitroot llc pct_change
xtunitroot llc forward_ret_1d
xtunitroot llc forward_ret_3d  
xtunitroot llc forward_ret_5d

* Fisher-ADF检验
xtunitroot fisher avg_sentiment, dfuller lags(1)
xtunitroot fisher sentiment_std, dfuller lags(1)
xtunitroot fisher positive_ratio, dfuller lags(1)
xtunitroot fisher volume, dfuller lags(1)
xtunitroot fisher pct_change, dfuller lags(1)
xtunitroot fisher forward_ret_1d, dfuller lags(1)
xtunitroot fisher forward_ret_3d, dfuller lags(1)
xtunitroot fisher forward_ret_5d, dfuller lags(1)

* 步骤二：协整检验
* 对每个股票进行协整检验
forvalues i = 1/8 {
    preserve
    keep if stock_id == `i'
    vecrank avg_sentiment volume, trend(constant) max
    restore
}

* Granger因果检验
forvalues i = 1/8 {
    preserve 
    keep if stock_id == `i'
    varsoc avg_sentiment volume
    var avg_sentiment volume
    vargranger
    restore
}

* 步骤三：面板模型估计
* 混合OLS
reg forward_ret_1d avg_sentiment sentiment_std positive_ratio volume pct_change, cluster(stock_id)

* 固定效应模型
* 个体固定效应
xtreg forward_ret_1d avg_sentiment sentiment_std positive_ratio volume pct_change, fe
estimates store fe_ind

* 时间固定效应
xtreg forward_ret_1d avg_sentiment sentiment_std positive_ratio volume pct_change i.date, fe
estimates store fe_time

* 双向固定效应
xtreg forward_ret_1d avg_sentiment sentiment_std positive_ratio volume pct_change i.date, fe cluster(stock_id)
estimates store fe_both

* 随机效应模型
xtreg forward_ret_1d avg_sentiment sentiment_std positive_ratio volume pct_change, re
estimates store re

* F检验(固定效应vs混合OLS)
quietly xtreg forward_ret_1d avg_sentiment sentiment_std positive_ratio volume pct_change, fe
xttest0

* Hausman检验(固定效应vs随机效应)
hausman fe_ind re
