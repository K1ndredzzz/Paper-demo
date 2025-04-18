*- 7.1 面板数据模型
    use mus08psidextract.dta, clear
    xtset stock_code date              // 设定面板数据
    xtsum stock_code date exp wks occ  // 既有组间比较也有组内比较

    *- 面板数据平稳性检验-（主要是长面板,单位根）
    xtset stock_code date
    xtsum
    sum
    xtunitroot llc lnrxrate if oecd, demean lags(aic 10) kernel(bartlett nwest) // LLC检验。假设所有面板数据有相同自回归参数。使用AIC选择滞后阶数回归。
	
    xtunitroot ips lnrxrate, lags(aic 5)               // IPS检验，对全样本共151个国家进行检验
    xtunitroot fisher lnrxrate, dfuller lags(3) drift  // Fisher-ADF检验
    xtunitroot hadri lnrxrate, kernel(parzen 5)        // Hadri LM平稳性检验

    ***************例子***************
    webuse xtcoint
    xtset id time
    describe
    summarize
    xtserial productivity rddomestic rdforeign, output // 面板数据一阶自相关检验，原假设不存在一阶自相关
    xtcointtest kao productivity rddomestic rdforeign  // Kao协整检验
    xtcointtest pedroni productivity rddomestic rdforeign    // 为了进一步确认被解释变量与解释变量之间的协整关系，Predoni检验
    xtcointtest westerlund productivity rddomestic rdforeign // Westerlund协整检验。第一种：检验被解释变量与解释变量是否存在部分协整关系
    xtcointtest westerlund productivity rddomestic rdforeign, allpanels //Westerlund协整检验。第二种：检验被解释变量与解释变量是否存在全局协整
    xtwest depvar varlist  // Westerlund对协整检验的其他补充修正。需安装ssc install xtwest

*- 7.2 静态面板数据模型
    use mus08psidextract.dta, clear
    asdoc sum, replace // 描述性统计分析
    xtset id t // 设定面板数据
    xtdes      // 显示面板数据结构，是否为平衡面板。也可xtdescribe
    xtsum      // 显示组内、组间与整体的统计指标     
    xttab fem  // 显示性别变量fem的组内、组间与整体的分布频率
    xtline wks  // 对每个个体的x1变量分别显示其时间序列图。


    *-比较面板固定效应估计与最小二乘虚拟变量估计结果
    reg lwage exp wks occ ind south smsa ms union i.id
    outreg2 using mmxi, word replace
    xtreg lwage exp wks occ ind south smsa ms union, fe
    outreg2 using mmxi, word 

    *-时间固定效应
    use mus08psidextract.dta, clear
    xtreg lwage exp wks occ ind south smsa ms union i.t, fe        //i.t表时间固定效应。

    xtreg lwage exp wks occ ind south smsa ms union tdum2-tdum7,fe //与上一命令等价。使用时间虚拟变量控制时间固定效应。
                                                               //相较于指示性前缀i.，使用时间虚拟变量好处：不仅可指定年份，还可对时间固定效应检测
    test tdum2 tdum3 tdum4 tdum5 tdum6 tdum7  //原假设：没有固定效应。


    *-还可通过选项cluster() 控制聚类稳健标准误
    xtreg lwage exp wks occ ind south smsa ms union i.t, fe 
    outreg2 using mmxi, word replace
    xtreg lwage exp wks occ ind south smsa ms union tdum2-tdum7,fe
    outreg2 using mmxi, word
    xtreg lwage exp wks occ ind south smsa ms union i.t, fe cluster(id)
    outreg2 using mmxi, word
    xtreg lwage exp wks occ ind south smsa ms union tdum2-tdum7,fe cluster(id)
    outreg2 using mmxi, word

    *-随机效应模型
    use mus08psidextract.dta, clear
    xtreg lwage exp wks occ ind south smsa ms union fem ed blk, re  //re表随机效应模型GLS估计。原来在固定效应模型中不能估计的时间不变因素都可估计。 
    outreg2 using mmxi, word replace
    xtreg lwage exp wks occ ind south smsa ms union fem ed blk, mle //mle表随机效应模型的极大似然估计
    outreg2 using mmxi, word
    xtreg lwage exp wks occ ind south smsa ms union, re
    outreg2 using mmxi, word
    xtreg lwage exp wks occ ind south smsa ms union, mle //随机效应极大似然估计结果更接近固定效应模型而不是OLS
    outreg2 using mmxi, word
 
    *-组间估计
    xtreg lwage exp wks occ ind south smsa ms union fem ed blk, be  //be组间估计量。固定效应不可使用。随机效应也不常使用。

    *-混合面板回归
    reg lwage exp wks occ ind south smsa ms union fem ed blk, cluster(id) //假设前提：不存在个体效应。要对这一假设进行检验


    *-豪斯曼检验
    use mus08psidextract.dta, clear
    xtreg lwage exp wks occ ind south smsa ms union, fe  //豪斯曼检验有效性没有统一说法。通常选择个体固定效应和双向固定效应模型用的较多
    est store fe
    xtreg lwage exp wks occ ind south smsa ms union, re  
    est store re
    hausman fe re //一般固定效应在前


    *-面板随机系数模型
    webuse invest2
    xtset company time
    xtrc invest market stock       //不要求面板数据所有个体都具有相同的估计系数，也称为变系数模型。一般用于长面板。检验个体边际效应是否一致。
    xtrc invest market stock, beta //加入beta后，不仅会估计平均边际效应，还会估计每个个体的边际效应。

    reg invest stock market i.company#c.market i.company, vce(cluster company) //c.是连续变量的指示符号。#交互项。

*- 7.3 面板工具变量法
    webuse nlswork, clear
    summarize
    xtset idcode year
    xtreg ln_w tenure age c.age#c.age not_smsa, fe                  //c.age#c.age,age的平方项，c.是连续变量的指示性符号
    xtivreg ln_w age c.age#c.age not_smsa (tenure=union south), fe  //如果需要第一阶段结果，最加first选项。

    xtivreg ln_w age c.age#c.age not_smsa (tenure=union south) i.year, fe         //如果需要第一阶段结果，最加first选项。

    xtivreg ln_w age c.age#c.age not_smsa (tenure=union south), fe vce(bootstrap) //xtivreg不能使用robust稳健标准误，可以bootstrap再抽样法获得标准误

    xtivreg ln_w age c.age#c.age not_smsa 2.race(tenure=union birth_yrsouth), re //还可以使用广义两阶段最小二乘法随机效应工具变量法估计，
                                                                             //并加入出生年份为工具变量。2.race表黑人虚拟变量。同理，1.race表白人虚拟变量
                                                                        
    xtivreg ln_w age not_smsa (tenure=union birth_yrsouth), fd     //也可一阶差分工具变量估计。该命令不能使用i.或c.等指示性前缀。