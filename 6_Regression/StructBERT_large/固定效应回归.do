**#个体时点双固定效应模型
{
**#组内估计法--> xtreg
xtset stock_code date
xtreg forward_ret_1d avg_sentiment sentiment_std avg_intensity comment_count sentiment_consensus,fe r  
//i. year：生成年份虚拟变量，即LSDV方法的时点固定效应 fe：个体固定效应 r:修正标准误

**#LSDV法-->i.code
reg  patent support Size Lev Roa PPE Capital Cash Gdp i.year i.code,r
//i. year：生成年份虚拟变量，即LSDV方法的时点固定效应 i.code：个体固定效应 r:修正标准误

**#LSDV法-->areg
areg patent support Size Lev Roa PPE Capital Cash Gdp i.year,absorb(code) r
//i. year：生成年份虚拟变量，即LSDV方法的时点固定效应 absorb(code)：个体固定效应 r:修正标准误

**#LSDV法，多维估计-->reghdfe
reghdfe patent support Size Lev Roa PPE Capital Cash Gdp i.year,absorb(code) vce(r)
reghdfe patent support Size Lev Roa PPE Capital Cash Gdp ,absorb(code year) vce(r)
//i. year：生成年份虚拟变量，即LSDV方法的时点固定效应 absorb(code category)：多维固定效应 r:修正标准误

}

**#为什么不加行业
{
**#如果行业不随时间变动而变动
xtreg patent support Size Lev Roa PPE Capital Cash Gdp i.year i.indcd2,fe r    


**#如果取公司当年行业
xtreg patent support Size Lev Roa PPE Capital Cash Gdp i.year i.indcd,fe r    
}

