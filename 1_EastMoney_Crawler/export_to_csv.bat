@echo off
title 东方财富股票数据导出CSV工具
echo ======================================
echo   东方财富股票数据导出CSV工具
echo ======================================
echo.
echo 正在将MongoDB数据导出为CSV...
echo.

python mongo_export_to_csv.py

echo.
echo 导出任务已完成，按任意键退出...
pause > nul 