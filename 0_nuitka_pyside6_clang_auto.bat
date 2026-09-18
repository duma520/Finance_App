@echo off
chcp 65001 >nul
rem ============================================================
rem  人民币收支管理系统 - Nuitka 编译脚本（唯一编译入口）
rem  唯一编译源: Finance_App.py（不要用 version\ 里的历史副本）
rem  本项目是 PyQt5，插件必须用 --enable-plugin=pyqt5
rem  （脚本名沿用模板名 0_nuitka_pyside6_clang_auto.bat，勿照抄 pyside6）
rem
rem  ★ 强制约定（见 软件升级迭代记录.md 第十一节）：
rem    主程序改动只要影响打包，必须同步改本脚本：
rem      新增数据文件 → 追加 --include-data-files=源=目标
rem      新增 Qt 模块/第三方依赖 → 确认插件与 --include-package-data 是否覆盖
rem      改入口/图标/输出目录 → 同步改下面的参数
rem
rem  已打包数据文件: icon.ico（程序运行时 QIcon("icon.ico") 读的是 exe 旁的图标）
rem  运行期在程序目录自建的 finance_master.db / finance_<用户>.db / backups\ 一律不要加进来
rem
rem  本文件为 UTF-8 无 BOM + CRLF；后续若加入含中文名的数据文件，chcp 65001 必须保留
rem  如需与其它项目一致改用 clang 编译：在下面命令里加 --clang（本机 D:\mingw64\bin\clang.exe 19.1.1 可用）
rem ============================================================
cls
rmdir /s /q *.build
rmdir /s /q *.dist

nuitka --standalone ^
    --enable-plugin=pyqt5 ^
    --windows-console-mode=disable ^
    --jobs=4 ^
    --remove-output ^
    --output-dir=build_output ^
    --include-package-data=pypinyin ^
    --include-data-files=icon.ico=icon.ico ^
    --windows-icon-from-ico=icon.ico ^
    Finance_App.py
