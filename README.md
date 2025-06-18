python3 configure.py structure.csv -m "bw100,delay10,loss0" --chunk-size 3MB --total-size 100MB
python3 autotest.py -a aimd "bw100,dealy10,loss0"

-m 后面指定的参数即是储存文件夹的名字，不输入默认使用时间格式 year-month-day, HOUR-MINUTE-SECOND (eg. 2025-06-09, 00:00:00)
autotest需要指定这个储存文件夹的名字

传输的文件路径还没有输入，可以查找关键词 TO BE COMPLETED
这个坑在实现autotest的时候再填
↑(Dev v2.1)已填坑，删掉了

文件结构
```
autotest
    configure.py
    autotest.py
    exec
        aggapps
            aggregator (从对应main.cpp编译来的, 在Dev v2.1对main.cpp有所修改)
        catapps
            consumer
        putapps
            producer

    logs (暂未完成)

    configure
        test1
            args.yaml (保存某次测试传入的参数)
            structure.csv (对应的网络结构)
            web.conf (网络配置)

            algorithm
                aimd
                    conconfig.ini
                    preconfig.ini
                    aggregatorcat.ini (Dev v2.2:其实这个没用，晚点处理一下)
                    aggregatorput.ini
                rubic
                    conconfig.ini
                    preconfig.ini
                    aggregatorcat.ini 
                    aggregatorput.ini
        2025-06-07 20:25:01
            (类似结构)


