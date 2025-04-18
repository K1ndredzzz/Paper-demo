import delimited "D:\Code_new\Paper\6_Regression\StructBERT_large\stock_daily_sentiment.csv", numericcols(2) 
encode date ,gen(time)
xtset stock_code time
asdoc summarize
logout,save(相关分析)word replace:pwcorr_a forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude price_change turnover_rate
asdoc pwcorr forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude price_change turnover_rate ,sig star(.05)
reg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude price_change turnover_rate,r
asdoc vif
asdoc reg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude price_change turnover_rate
est store ols
asdoc xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude price_change turnover_rate, fe
est store fe
asdoc xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus close volume amount amplitude price_change turnover_rate, re
est store re
hausman fe re
hausman fe
