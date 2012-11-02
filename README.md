# Weipan Python SDK

[微盘](http://vdisk.weibo.com) SDK Python版

## 使用

### 验证过程

首先创建一个session

    from weipan import session

    sess = session.WeipanSession(APP_KEY, APP_SECRET, CALLBACK, ACCESS_TYPE)

生成授权页面的url

    url = sess.build_authorize_url()

用户跳转到该授权页面并授权

页面跳转到应用的回调页（会带上code）

根据code获取token

    rst = sess.access_token_with_code(code)
    token = rst['access_token']

### 接口调用

接口调用通过weipan.client.WeipanClient实现

示例：

    from weipan import session, client

    sess = session.WeipanSession(APP_KEY, APP_SECRET, CALLBACK, ACCESS_TYPE)

    # 认证并获取token...

    api_client = client.WeipanClient(sess)

    # 创建目录
    api_client.create_folder('/dir1')

    # 上传文件(PUT)
    api_client.put_file('/dir1/test.txt', 'path/to/test.txt')

    # 上传文件(POST)
    api_client.post_file('/dir1/test.txt', 'path/to/test.txt')

    # 获取信息
    api_client.metadata('/dir1')

    api_client.metadata('/dir1/test.txt')

    #详细接口调用参考client.py和官方文档...

## 测试

    python tests/test_client.py token

或者使用cli_client生成的token:

    python tests/test_client.py `cat weipan_token.txt`

## 命令行工具使用

在weipan-sdk-python目录下新建文件shAdOw.py，文件内容如下：

    APP_KEY = '你的app key'
    APP_SECRET = '你的app secret'
    CALLBACK = '回调地址，例如http://localhost:8414/callback'
    ACCESS_TYPE = 'sandbox'

运行：

    python example/cli_client.py

    Weipan> help
    Weipan> login
    Weipan> ls
    Weipan> mkdir xxx
    Weipan> rm xxx
    Weipan> put xxx
    Weipan> get xxx
    ...

注意：登录时，对于本地的回调地址，会启动一个web服务用于接收；对于其它回调地址，需要手动输入回调的code。


## 问题

- 由于接口数据的延迟，导致连续调用时可能取不到最新数据，因此在测试中加入了0.5s的延迟处理，上传文件后又加入了1s的延迟
- HTTPS暂未支持

## 相关链接

- [微盘](http://vdisk.weibo.com)
- [微盘开放API](http://vdisk.weibo.com/developers/)
- [Github](http://github.com/ddliu/weipan-sdk-python)

