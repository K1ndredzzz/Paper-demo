cd"C:\Users\92339\Desktop\第12个视频 快速完成一篇实证论文"

**********************************************************
/***********利用Stata快速完成一篇实证论文的模板**********/
**********************************************************

/*数据整理*/

rename 综合税率A x2
rename 净资产收益率ROE y
rename 资产负债率 x1
rename 总资产周转率A x3
rename 资产对数 x4
rename 前十大股东持股比例 x5


*xtset 股票代码 截止日期
encode 股票代码 ,gen(id)
encode 截止日期 ,gen(time)
xtset id time

/*描述性统计*/
logout,save(基本统计描述)word replace:tabstat y x1 x2 x3 x4 x5,s(N mean p50 sd min max) f(%12.3f) c(s)

/*相关性分析*/
logout,save(相关分析)word replace:pwcorr_a y x1 x2 x3 x4 x5

/*共线性诊断*/
reg y x1 x2 x3 x4 x5,r
vif
logout,save(共线性诊断)word replace:vif

order y x1 x2 x3 x4 x5

/*模型选择检验*/

reg y x1 x2 x3 x4 x5
est store ols

xtreg y x1 x2 x3 x4 x5,fe
// 检验个体效应 ，表明固定效应优于混合ols模型 ，p<0.05表示个体效应显著，固定效应更好

qui xtreg y x1 x2 x3 x4 x5,re
xttest0 
//检验时间效应，结果随机效应也优于混合ols模型，p<0.05表示随机效应显著

xtreg y x1 x2 x3 x4 x5,re
est store re

xtreg y x1 x2 x3 x4 x5,fe
est store fe

hausman fe re //豪斯曼检验，结果拒绝原假设，选用固定效应模型 p<0.05固定效应，大于0.05 随机效应

outreg2 using "豪斯曼检验", word ctitle(FE)  adds(Hausman, `r(chi2)',p-value,`r(p)')replace //输出hausman结果

/*检验结果，应该选择固定效应回归分析*/

reg y x1 x2 x3 x4 x5
est store ols

xtreg y x1 x2 x3 x4 x5,fe
est store fe

xtreg y x1 x2 x3 x4 x5,re
est store re

esttab ols fe re using 实证结果.rtf, replace b(%12.3f) se(%12.3f) nogap compress s(N r2 r2_a)star(* 0.1 ** 0.05 *** 0.01) //加入了调整R2，r2_a


/**************************滞后效应************************/

xtreg y x1 x2 x3 x4 x5 L.x5 ,fe
est store fe1

xtreg y x1 x2 x3 x4 x5 L2.x5 ,fe
est store fe2

esttab fe fe1 fe2 using 滞后效应.rtf, replace b(%12.3f) se(%12.3f) nogap compress s(N r2 r2_a)star(* 0.1 ** 0.05 *** 0.01) //加入了调整R2，r2_a

/**************************分组回归************************/

order y x1 x2 x3 x4 x5 分组
*encode 股权性质,gen(分组)

order y x1 x2 x3 x4 x5 // 国企 = 2  外资 = 3 私企 = 4

xtreg y x1 x2 x3 x4 x5 if 分组 == 2 ,fe
est store fe3

xtreg y x1 x2 x3 x4 x5 if 分组 == 3 ,fe
est store fe4

xtreg y x1 x2 x3 x4 x5 if 分组 == 4 ,fe
est store fe5

esttab fe fe3 fe4 fe5 using 分组回归.rtf, replace b(%12.3f) se(%12.3f) nogap compress s(N r2 r2_a)star(* 0.1 ** 0.05 *** 0.01) //加入了调整R2，r2_a

/**************************调节效应************************/

*gen TJ = x4*x5

xtreg y x1 x2 x3 x4 x5 TJ ,fe
est store fe6

esttab fe fe6 using 调节效应.rtf, replace b(%12.3f) se(%12.3f) nogap compress s(N r2 r2_a)star(* 0.1 ** 0.05 *** 0.01) //加入了调整R2，r2_a

/**************************中介效应************************/

* rename 托宾Q值TQ ZJ

xtreg y x1 x2 x3 x4 x5 ,fe
est store fe7

xtreg ZJ x1 x2 x3 x4 x5 ,fe
est store fe8

xtreg y x1 ZJ x2 x3 x4 x5 ,fe
est store fe9

esttab fe7 fe8 fe9 using 中介效应.rtf, replace b(%12.3f) se(%12.3f) nogap compress s(N r2 r2_a)star(* 0.1 ** 0.05 *** 0.01) //加入了调整R2

/***********************控制时间 个体************************/

xtreg y x1 x2 x3 x4 x5 i.id i.time ,fe

estadd local id "Yes"
estadd local time "Yes"

est sto fe10

esttab fe fe10 using 控制个体时间回归.rtf, replace b(%12.3f) se(%12.3f) nogap compress drop(*.id *.time) s(N r2 r2_a id time)star(* 0.1 ** 0.05 *** 0.01) //加入了调整R2
