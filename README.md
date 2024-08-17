# OneJudger

## 描述

COJ的judger示例，使用python语言实现了COJ的judger微服务。你可以在该示例的基础上进一步开发。同时COJ的judger相关的接口更新时也会率先更新该judger示例。

## 概览

* api.py 将coj的judger接口进行封装
* app.py 程序的入口。依次进行数据库连接，数据库初始化，初始化robot，启动http服务，向COJ注册服务，启动保活线程等操作。
* config.py judger的配置信息
* constants.py judger内部的一些常量
* controller.py controller层，负责处理http接口
* core.py 编写了一些较为内部的方法
* entity.py 数据模型
* event.py 一些需要自己手动完善的代码
* logger.py 日志，judger的日志将自动写入到同目录的log文件夹下
* service.py service层，负责进一步处理controller层接受到的请求
* utils.py 工具类

其他文件

* database.db 一个小型的数据库，judger理论上不用专门去搞个数据库，直接在文件里搞一个就行
* init.sql 数据库初始化语句，judger在运行时都会执行一下这个脚本（在app.py中触发）

## 流程

**启动流程**

app.py作为程序的入口

* 首先连接本地的数据库
* 然后执行init.sql初始化
* 然后调用初始化robot的方法，然后启动http
* 向COJ注册服务
  * COJ会先判断jid是否已经被占用
    * 如果被占用了则判断已经注册的judger能否继续通信，如果不能继续通信就把已经注册的judger踢掉，允许新的judger注册
    * 如果已经注册的judger仍然能够通信，那么注册失败
  * 如果注册失败了judger仍然继续运行，因为有可能是judger重启
* 然后启动保活线程

**一般接口调用流程**

首先请求打到controller层，controller层调用service层拿到数据，再响应回去

**提交流程**

请求打到controller层，controller调用core.py中的submit。

submit方法先通过submit_get_wait_list获取到该题目能被哪个robot揽收，然后通过submit_select_robot获取到最优的robot

然后将测试点信息打包成一个评测包，投递给目标robot的处理队列中

目标robot一直在等待队列。当有评测包投递到队列后robot将立刻处理（见core.py的robot_loop）。

处理时，首先会设置当前robot的状态为working，然后调用event.py的handle

handle中为爬虫代码，可以向远程oj平台提交评测信息并抓取评测结果

## 开发指南

首先你需要编辑config.py，设置你的信息，然后一般只需要考虑event.py里怎么写就好了
