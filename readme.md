#接口定义文档
###客户端send函数
|function|send format          |return         |remark        |
|--------|---------------------|---------------|--------------|
|login   |login&user_name           |1:success;0:failed|处理登录|
|getmember|getmember                 |[list]       |获取服务器在线成员名字列表        |
|talkto   |talkto&to_user&message    |1:success;0:target user offline;-1:other error|一对一聊天|
|filename|filename&to_user&file_name |1:success;0:target user offline;-1:other error|传输文件名和文件传输对象|
|ready   |ready&file_name            |none|准备好接受服务器穿过来对应文件名的文件


###回调函数id------>sFuncId
> 正整数：执行正常的回调函数

> 0：出错

> -101:响应在线成员列表的变更

> -102:响应其他人对本机的谈话，更新chatDict字典内容

Chat window 定时刷新，所以只需要维护chatDict的值就可以实时改变相应的chat window的状态，
在chat window初始化时就要显示chatDict对应username 的content。

一对一对话的两种情况：
1.主动发起谈话。双击用户名打开chat window，初始化对应chatDict内容，自己发的话加到dict
中，别人发过来的话也加到dict中。
2.被动发起谈话。对应user字体颜色变红说明有未读消息。此时chatDict已经初始化并且将对应的发
过来的文字内容进行了记录，当用户双击打开这个相应的chat window时，将显示已经存在的温度消息
（前提是两个人都在线，离线所有的数据就全部消失了）

tcp协议实现文件传输：
首先客户端向服务器端发送两个信息：1.文件名2.文件大小

然后客户端向服务器发送文件内容。注意：由于文件过大，需要分段传输。
