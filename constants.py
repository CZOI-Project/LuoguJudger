# 一些常量
robot_status_destroy: int = -4  # robot准备销毁，该状态仅用在judger代码里
robot_status_no_user: int = -3  # robot已经创建，但未绑定账号密码
robot_status_offline: int = 0  # robot离线，一般是judger刚启动时已经保存的robot没能登录
robot_status_ok: int = 1  # robot准备就绪
robot_status_working: int = 2  # robot正在评测

trace_status_ok: int = 0  # 投递成功
trace_status_robot_failed: int = 2  # 投递时发生错误

response_status_ok: int = 200
response_status_space: int = 100
response_status_msg: int = 102
response_status_error: int = 105

"""
0-waiting，正在等待
1-judging，正在评测
2-accepted，AC
3-wrong answer，WA
4-time limit error，TLE
5-memory limit error，MLE
6-runtime error，RE
7-unknown error，UKE
8-partial correct，PC，部分正确，仅得部分分
9-system error，执行过程中发生错误，错误信息可在message中查看
10-compiler error，CE，编译错误
"""
checkpoint_status_waiting: int = 0
checkpoint_status_judging: int = 1
checkpoint_status_ac: int = 2
checkpoint_status_wa: int = 3
checkpoint_status_tle: int = 4
checkpoint_status_mle: int = 5
checkpoint_status_re: int = 6
checkpoint_status_uke: int = 7
checkpoint_status_pc: int = 8
checkpoint_status_se: int = 9
checkpoint_status_ce: int = 10
