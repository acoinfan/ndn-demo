import os, argparse, sys, shutil, yaml, csv, configparser
def main():
    args = parse_args()
    print_args(args)
    generate_config_directory(args)
    save_args(args)
    generate_node_config(args)
    generate_general_config(args)

def parse_args(test_args=None):
    """
    Parsing command-line arguments 解析命令行参数
    >>> args = parse_args(['structure.file', '-m', '_test_', '--chunk-size', '2MB', '--total-size', '100MB'])
    >>> args.structure
    'structure.file'
    >>> args.message
    '_test_'
    >>> args.chunk_size
    '2MB'
    >>> args.total_size
    '100MB'
    """

    from datetime import datetime
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    parser = argparse.ArgumentParser(description="A parser for arguments of configure.py")

    # Add must-chosen arguments 添加必输的命令行参数
    parser.add_argument('structure', help='the web structure csv file')

    # Add alternative arguments 添加可选的命令行参数
    chunk_group = parser.add_argument_group('Chunk configuration')
    chunk_group.add_argument('--chunk-size', default='1MB', help='size of a single chunk')
    chunk_group.add_argument('--total-size', default='10MB', help='size of the total file')
    
    parser.add_argument('-m', '--message', default=timestamp_str, help='message to mark the configuration, default is localtime (e.g. test, bw100-loss1)')

    # Default: reading from argv except passing in list 不传入参数:默认从argv中获取
    return parser.parse_args(test_args) 

def print_args(args):
    """
    Print the parsed arguments 打印解析后的参数
    >>> args = parse_args(['_test_.csv', '-m', '_test_', '--chunk-size', '2MB', '--total-size', '100MB'])
    >>> print_args(args)
    ------ Arguments ------
    structure: _test_.csv
    message: _test_
    chunk_size: 2MB, total_size: 100MB
    <BLANKLINE>
    """

    print('------ Arguments ------')
    print(f"structure: {args.structure}")
    print(f'message: {args.message}')
    print(f"chunk_size: {args.chunk_size}, total_size: {args.total_size}\n")

def generate_config_directory(args):
    """
    Ensure the directory and csv file exists 确保目录及csv文件存在
    >>> with open('_test_.csv', 'w') as f:
    ...     _ = f.write("from,to,bw,loss,delay,max_queue_number\\n")
    ...     _ = f.write("con0,agg0,100,0,10,10000\\n")
    ...     _ = f.write("con0,agg1,100,1,100,1000\\n")
    >>> args = parse_args(['structure.file', '-m', '_test_', '--chunk-size', '2MB', '--total-size', '100MB'])
    >>> generate_config_directory(args)
    >>> os.path.exists('configure/_test_')
    True
    >>> os.path.exists('configure/_test_/algorithm')
    True
    >>> os.path.exists('configure/_test_/algorithm/aimd')
    True
    >>> os.path.exists('configure/_test_/algorithm/rubic')
    True
    >>> shutil.rmtree('configure/_test_')
    >>> os.remove('_test_.csv')
    """

    relative_path = 'configure/' + args.message

    # detect csv file existence 检测csv文件是否存在
    if not os.path.exists(args.structure):
        FileNotFoundError(f"Structure file {args.structure} does not exist")

    # create directory if not exists 如果目录不存在则创建
    if os.path.exists(relative_path):
        result = input(f"Directory \"{relative_path}\" exists, do you want to rewrite it? (Y/N)\n")
        result = result.upper()
        if (result == "Y" or result == "YES"):
            print(f"Cleaning files in Directory \"{relative_path}\"")

            # equals to "rm -rf {relative_path}" 等价于递归删除目录
            shutil.rmtree(relative_path)   
        else:
            print("Execution terminated")
            sys.exit()
    
    os.makedirs(relative_path + '/algorithm')
    os.makedirs(relative_path + '/algorithm/aimd')
    os.makedirs(relative_path + '/algorithm/rubic')            

def save_args(args):
    """
    Saving arguments into args.yaml 保存参数到args.yaml文件
    >>> with open('_test_.csv', 'w') as f:
    ...     _ = f.write("from,to,bw,loss,delay,max_queue_number\\n")

    >>> args = parse_args(['_test_.csv', '-m', '_test_', '--chunk-size', '2MB', '--total-size', '100MB'])
    >>> generate_config_directory(args)
    >>> save_args(args)
    Writing arguments into File "configure/_test_/args.yaml"
    >>> os.path.exists('configure/_test_/args.yaml')
    True
    >>> with open("configure/_test_/args.yaml", "r") as f :
    ...     actual_data = yaml.safe_load(f)
    ...     actual_data == vars(args)
    True
    >>> shutil.rmtree('configure/_test_')
    >>> os.remove('_test_.csv')
    """

    relative_path = 'configure/' + args.message + '/args.yaml'
    with open(relative_path, 'w') as file:
        yaml.dump(vars(args), file, default_flow_style=False)
    print(f"Writing arguments into File \"{relative_path}\"")

def generate_node_config(args):
    """
    Writing web.conf for ndn server and save csv file 配置ndn-web的conf文件并保存csv文件
    >>> with open('_test_.csv', 'w') as f:
    ...     _ = f.write("from,to,bw,loss,delay,max_queue_number\\n")
    ...     _ = f.write("con0,agg0,100,0,10,1000\\n")
    ...     _ = f.write("con0,agg1,100,1,100,1000\\n")
    >>> args = parse_args(['_test_.csv', '-m', '_test_', '--chunk-size', '2MB', '--total-size', '100MB'])
    >>> generate_config_directory(args)
    >>> generate_node_config(args)
    >>> os.path.exists('configure/_test_/web.conf')
    True

    >>> with open("configure/_test_/web.conf", "r") as f:
    ...     actual_data = f.read()
    ...     print(actual_data)
    [nodes]
    agg0:_
    agg1:_
    con0:_
    <BLANKLINE>
    [links]
    con0:agg0 bw=100 loss=0 delay=10 max_queue_number=1000
    con0:agg1 bw=100 loss=1 delay=100 max_queue_number=1000
    <BLANKLINE>

    >>> shutil.rmtree('configure/_test_')
    >>> os.remove('_test_.csv')
    """

    with open(args.structure, 'r') as file:
        csv_reader = csv.reader(file)
        rows = list(csv_reader)

    header = rows[0]
    num_columns = len(header)

    # set the relative path for the configuration file 设置配置文件的相对路径
    relative_path = 'configure/' + args.message + '/web.conf'\

    # get the nodes from the rows 获取节点列表
    nodes = set([_row[0] for _row in rows[1:]] + [_row[1] for _row in rows[1:]])
    
    with open(relative_path, 'w+') as file:
        file.write("[nodes]\n")

        # ensure the output is in ordered 确保输出的节点是有序的
        nodes = sorted(nodes)  
        for node in nodes:
            file.write(f"{node}:_\n")

        file.write("\n[links]\n")
        
        for row in rows[1:]:
            key = f"{row[0]}:{row[1]}"
            value = ' '.join(f"{header[i]}={row[i]}" for i in range(2, num_columns))
            file.write(f"{key} {value}\n")

    # save "source.csv" to "configure/<directory>/source.csv" 将source.csv保存到指定目录
    shutil.copy(args.structure, f'configure/{args.message}/structure.csv')

def generate_general_config(args):
    """
    Writing conconfig.ini, preconfig.ini, aggregatorcat.ini, aggregatorput.ini 写入四个通用配置文件
    """
    for algorithm in ['aimd', 'rubic']:
        generate_conconfig(args, algorithm)
        generate_proconfig(args, algorithm)
        generate_aggregatorcat(args, algorithm)
        generate_aggregatorput(args, algorithm)

def generate_conconfig(args, algorithm : str):
    """
    Writing conconfig.ini 写入conconfig.ini文件
    """
    relative_path = f"configure/{args.message}/algorithm/{algorithm}/conconfig.ini"

    # calculate the total number of chunks 计算总的chunk数量
    chunk_size = analyse_size(args.chunk_size)
    total_size = analyse_size(args.total_size)
    chunk_number = total_size // chunk_size + (total_size % chunk_size > 0)

    parser = configparser.ConfigParser()
    parser['General'] = {
        'name': f'/{args.message}-con',                             # configuration name identifier 配置名称标识符
        'lifetime': '4000',                                         # interest packet lifetime (ms) 兴趣包生存时间(毫秒)
        'retries': '1024',                                          # maximum retry count 最大重传次数
        'pipeline-type': 'hybla',                                   # pipeline algorithm type 管道算法类型
        'naming-convention': 'typed',                               # naming convention type 命名约定类型
        'quiet': 'false',                                           # quiet mode switch 静默模式开关
        'verbose': 'false',                                         # verbose output switch 详细输出开关
        'totalchunksnumber': str(chunk_number),                     # total number of chunks 总chunk数量
        'recordingcycle': '200',                                    # recording cycle (ms) 记录周期(毫秒)
        'topofilepath': f"./configure/{args.message}/web.conf",     # topology config file path 拓扑配置文件路径
        'primarytopofilepath': f"./configure/{args.message}/web.conf", # primary topology config file path 主拓扑配置文件路径
        'log-level': 'err',                                         # log level (err/warn/info/debug) 日志级别
        'chunk-size': str(chunk_size),                              # single chunk size (bytes) 单个chunk大小(字节)
        'num-faces': '3',                                           # number of network faces 网络接口数量
        'table-size': '10'                                          # forwarding table size 转发表大小
    }
    parser['AdaptivePipeline'] = {
        'ignore-marks': 'false',                                    # ignore congestion marks 忽略拥塞标记
        'disable-cwa': 'false',                                     # disable congestion window avoidance 禁用拥塞窗口避免
        'init-cwnd': '2.0',                                         # initial congestion window size 初始拥塞窗口大小
        'init-ssthresh': '1.7976931348623157e+308',                 # initial slow start threshold 初始慢启动阈值
        'rto-alpha': '0.125',                                       # RTO smoothing factor α RTO平滑因子α
        'rto-beta': '0.25',                                         # RTO variance smoothing factor β RTO方差平滑因子β
        'rto-k': '8',                                               # RTO variance multiplier K RTO方差乘数K
        'min-rto': '200',                                           # minimum retransmission timeout (ms) 最小重传超时(毫秒)
        'max-rto': '60000',                                         # maximum retransmission timeout (ms) 最大重传超时(毫秒)
        'log-cwnd': f"./logs/{args.message}/con-cwnd.txt",          # congestion window log file path 拥塞窗口日志文件路径
        'log-rtt': f"./logs/{args.message}/con-rtt.txt"             # RTT log file path RTT日志文件路径
    }

    parser['AIMDPipeline'] = {
        'aimd-step': '1.0',                                         # AIMD additive increase step 加性增加步长
        'aimd-beta': '0.5',                                         # AIMD multiplicative decrease factor 乘性减少因子
        'reset-cwnd-to-init': 'false'                               # reset window to initial on congestion 拥塞时重置窗口到初始值
    }

    parser['CubicPipeline'] = {
        'cubic-beta': '0.7',                                        # CUBIC window reduction factor CUBIC窗口缩减因子
        'enable-fast-conv': 'true'                                  # enable fast convergence mode 启用快速收敛模式
    }

    parser['HighSpeedPipeline'] = {
        'hscc-growth-factor': '0.01',                               # high-speed congestion control growth factor 高速拥塞控制增长因子
        'hscc-reduction-factor': '0.8',                             # high-speed congestion control reduction factor 高速拥塞控制减少因子
        'hscc-bandwidth-exp': '0.9',                                # bandwidth estimation exponent parameter 带宽估算指数参数
        'bdp-scale': '1.1'                                          # bandwidth-delay product scale factor 带宽延迟积缩放因子
    }

    # write the configuration to the file 将配置写入文件
    with open(relative_path, 'w') as configfile:
        parser.write(configfile)
    print(f"Writing conconfig.ini to {relative_path}")

def generate_proconfig(args, algorithm): 
    """
    Writing proconfig.ini 写入proconfig.ini文件
    """
    relative_path = f"configure/{args.message}/algorithm/{algorithm}/proconfig.ini"

    # calculate the total number of chunks 计算总的chunk数量
    chunk_size = analyse_size(args.chunk_size)
    
    parser = configparser.ConfigParser()
    parser['general'] = {
        'freshness': '10000',                                       # data packet freshness period (ms) 数据包新鲜度周期(毫秒)
        'size': '4096',                                             # default data packet size (bytes) 默认数据包大小(字节)
        'naming-convention': 'typed',                               # naming convention type 命名约定类型
        'print-data-version': 'false',                              # print data version switch 打印数据版本开关
        'quiet': 'false',                                           # quiet mode switch 静默模式开关
        'verbose': 'false',                                         # verbose output switch 详细输出开关
        'chunk-size': str(chunk_size)                               # single chunk size (bytes) 单个chunk大小(字节)
        # 'input-file': 'DISABLED'                                  # input data file path 输入数据文件路径
    }

    parser['Logging'] = {
        'log-file': f'./logs/{args.message}/producer.txt',          # producer log file path 生产者日志文件路径
        'log-level': 'debug'                                        # log level (err/warn/info/debug) 日志级别
    }
    
    # write the configuration to the file 将配置写入文件
    with open(relative_path, 'w') as configfile:
        parser.write(configfile)
    print(f"Writing preconfig.ini to {relative_path}")

def generate_aggregatorcat(args, algorithm): 
    """
    Writing aggregatorcat.ini 写入aggregatorcat.ini文件
    """
    relative_path = f"configure/{args.message}/algorithm/{algorithm}/aggregatorcat.ini"

    # calculate the total number of chunks 计算总的chunk数量
    chunk_size = analyse_size(args.chunk_size)
    total_size = analyse_size(args.total_size)
    chunk_number = total_size // chunk_size + (total_size % chunk_size > 0)

    parser = configparser.ConfigParser()
    parser['General'] = {
        'name': f'/{args.message}-agg',                              # producer name identifier 生产者名称标识符
        'lifetime': '4000',                                         # interest packet lifetime (ms) 兴趣包生存时间(毫秒)
        'retries': '1024',                                          # maximum retry count 最大重传次数
        'pipeline-type': f"{algorithm}",                            # pipeline algorithm type 管道算法类型
        'naming-convention': 'typed',                               # naming convention type 命名约定类型
        'quiet': 'false',                                           # quiet mode switch 静默模式开关
        'verbose': 'false',                                         # verbose output switch 详细输出开关
        'totalchunksnumber': str(chunk_number),                     # total number of chunks 总chunk数量
        'recordingcycle': '1000',                                   # recording cycle (ms) 记录周期(毫秒)
        'topofilepath': f"./configure/{args.message}/web.conf",     # topology config file path 拓扑配置文件路径
        'primarytopofilepath': f"./configure/{args.message}/web.conf", # primary topology config file path 主拓扑配置文件路径
        'log-level': 'err',                                         # log level (err/warn/info/debug) 日志级别
        'chunk-size': str(chunk_size),                              # single chunk size (bytes) 单个chunk大小(字节)
        'num-faces': '1',                                           # number of network faces 网络接口数量
        'table-size': '10',                                         # forwarding table size 转发表大小
        'max-buffered-chunks': '1024'                               # maximum buffered chunks 最大缓冲chunk数量
    }

    parser['AdaptivePipeline'] = {
        'ignore-marks': 'false',                                    # ignore congestion marks 忽略拥塞标记
        'disable-cwa': 'false',                                     # disable congestion window avoidance 禁用拥塞窗口避免
        'init-cwnd': '2.0',                                         # initial congestion window size 初始拥塞窗口大小
        'init-ssthresh': '1.7976931348623157e+308',                 # initial slow start threshold 初始慢启动阈值
        'rto-alpha': '0.125',                                       # RTO smoothing factor α RTO平滑因子α
        'rto-beta': '0.25',                                         # RTO variance smoothing factor β RTO方差平滑因子β
        'rto-k': '8',                                               # RTO variance multiplier K RTO方差乘数K
        'min-rto': '200',                                           # minimum retransmission timeout (ms) 最小重传超时(毫秒)
        'max-rto': '60000',                                         # maximum retransmission timeout (ms) 最大重传超时(毫秒)
        'log-cwnd': f"./logs/{args.message}/agg-cwnd.txt",          # congestion window log file path 拥塞窗口日志文件路径
        'log-rtt': f"./logs/{args.message}/agg-rtt.txt"             # RTT log file path RTT日志文件路径
    }

    parser['AIMDPipeline'] = {
        'aimd-step': '1.0',                                         # AIMD additive increase step 加性增加步长
        'aimd-beta': '0.5',                                         # AIMD multiplicative decrease factor 乘性减少因子
        'reset-cwnd-to-init': 'false'                               # reset window to initial on congestion 拥塞时重置窗口到初始值
    }

    parser['CUBICPipeline'] = {
        'cubic-beta': '0.7',                                        # CUBIC window reduction factor CUBIC窗口缩减因子
        'enable-fast-conv': 'false'                                 # enable fast convergence mode 启用快速收敛模式
    }

    # 写入配置文件
    with open(relative_path, 'w') as configfile:
        parser.write(configfile)
    print(f"Writing aggregatorcat.ini to {relative_path}")

def generate_aggregatorput(args, algorithm): 
    """
    Writing aggregatorput.ini 写入aggregatorput.ini文件
    """
    relative_path = f"configure/{args.message}/algorithm/{algorithm}/aggregatorput.ini"

    # calculate the total number of chunks 计算总的chunk数量
    chunk_size = analyse_size(args.chunk_size)
    
    parser = configparser.ConfigParser()
    parser['General'] = {
        'freshness': '10000',                                       # data packet freshness period (ms) 数据包新鲜度周期(毫秒)
        'size': '4096',                                             # default data packet size (bytes) 默认数据包大小(字节)
        'naming-convention': 'typed',                               # naming convention type 命名约定类型
        'print-data-version': 'false',                              # print data version switch 打印数据版本开关
        'quiet': 'false',                                           # quiet mode switch 静默模式开关
        'verbose': 'false',                                         # verbose output switch 详细输出开关
        'chunk-size': str(chunk_size)                               # single chunk size (bytes) 单个chunk大小(字节)
        # 'input-file': 'DISABLED'                                  # input data file path 输入数据文件路径
    }

    parser['Logging'] = {
        'log-file': f'logs/{args.message}/agg-producer.txt',        # producer log file path 生产者日志文件路径
        'log-level': 'debug'                                        # log level (err/warn/info/debug) 日志级别
    }

    # 写入配置文件
    with open(relative_path, 'w') as configfile:
        parser.write(configfile)
    print(f"Writing aggregatorput.ini to {relative_path}")

def analyse_size(size_str: str) -> int:
    """
    Based on the input size, transform the size string into bytes 根据输入的大小，将大小字符串转换为字节数

    >>> analyse_size('1MB')
    1048576
    >>> analyse_size('2.5GB')
    2684354560
    """
    
    import re

    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024,
        'TB': 1024 * 1024 * 1024 * 1024
    }
    
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([A-Za-z]+)$', size_str.strip())
    if not match:
        raise ValueError(f"{size_str} is not a valid storage unit (expected formats: KB, MB, GB, etc.).")
    
    value, unit = match.groups()
    value = float(value)
    unit = unit.upper()
    
    if unit not in units:
        raise ValueError(f"{unit} is not a valid storage unit (expected formats: KB, MB, GB, etc.).")
    
    return int(value * units[unit])
    

if __name__ == "__main__":
    main()
