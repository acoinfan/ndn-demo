import argparse, os, sys
from time import sleep
from mininet.log import setLogLevel, info

from minindn.minindn import Minindn
from minindn.util import MiniNDNCLI
from minindn.apps.app_manager import AppManager
from minindn.apps.nfd import Nfd
from minindn.apps.nlsr import Nlsr
from minindn.apps.application import Application

def main():
    args = parse_args()
    sys.argv = []  # Clear sys.argv to prevent interference with Mininet
    
    detect_test_config(args)
    print_test_config(args)
    ndn = start_server(args)
    start_nodes(args, ndn)
    MiniNDNCLI(ndn.net)


def parse_args(test_args=None):
    parser = argparse.ArgumentParser(description="A parser for arguments of autotest.py")

    parser.add_argument('config', help='the specified configuration, equals to directory name')
    parser.add_argument('-a', '--algorithm', default='aimd', help='web server algorithm: aimd, rubic')

    return parser.parse_args(test_args)

def detect_test_config(args):
    return None

def print_test_config(args):
    print("starting autotest with the following configuration: \n")
    return None

def start_server(args):
    relative_path = f"./configure/{args.config}/web.conf"
    setLogLevel('info')
    Minindn.cleanUp()
    Minindn.verifyDependencies()

    ndn = Minindn(topoFile=relative_path)

    ndn.start()

    info('Starting NFD on nodes\n')
    nfds = AppManager(ndn, ndn.net.hosts, Nfd)
    info('Starting NLSR on nodes\n')
    nlsrs = AppManager(ndn, ndn.net.hosts, Nlsr)
    sleep(10)

    return ndn

def start_nodes(args, ndn):
    relative_path = f"./configure/{args.config}/algorithm/{args.algorithm}"
        # 获取节点
    consumer = ndn.net['con0']
    aggregators = [h for h in ndn.net.hosts if h.name.startswith('agg')]
    producers = [h for h in ndn.net.hosts if h.name.startswith('pro')]
    
    # 启动生产者
    producer_path = os.path.abspath(f'./exec/putapps/producer')
    for pro in producers:
        info(f'Starting Producer {pro.name}\n')
        Application(pro).start(f'{producer_path} --prefix /{pro.name} --config {relative_path}/proconfig.ini', f'{pro.name}.log')
        sleep(5)
    
    # 启动聚合器
    agg_path = os.path.abspath(f'./exec/aggapps/aggregator')
    for agg in aggregators:
        info(f'Starting Aggregator {agg.name}\n')
        Application(agg).start(f'{agg_path} --prefix /{agg.name} --config {relative_path}/aggregatorput.ini', f'{agg.name}.log')
        sleep(5)
    
    # 通告路由
    for node in producers + aggregators:
        node.cmd(f'nlsrc advertise /{node.name}')
        sleep(2)
    
    # 启动消费者
    info('Starting Consumer\n')
    consumer_path = os.path.abspath(f'./exec/catapps/consumer')
    Application(consumer).start(f'{consumer_path} --config {relative_path}/conconfig.ini', 'consumer.log')

if __name__ == "__main__":
    main()