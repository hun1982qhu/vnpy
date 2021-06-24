# flake8: noqa
import multiprocessing
import sys
from time import sleep
from datetime import datetime, time

from vnpy.trader.setting import SETTINGS

from vnpy.event import EventEngine

from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy.gateway.ctp import CtpGateway
from vnpy.gateway.ctptest import CtptestGateway
# from vnpy.gateway.mini import MiniGateway
# from vnpy.gateway.minitest import MinitestGateway
# from vnpy.gateway.femas import FemasGateway
# from vnpy.gateway.sopt import SoptGateway
# from vnpy.gateway.sopttest import SopttestGateway
# from vnpy.gateway.sec import SecGateway
# from vnpy.gateway.uft import UftGateway
# from vnpy.gateway.hsoption import HsoptionGateway
# from vnpy.gateway.xtp import XtpGateway
# from vnpy.gateway.tora import ToraStockGateway
# from vnpy.gateway.tora import ToraOptionGateway
# from vnpy.gateway.oes import OesGateway
# from vnpy.gateway.comstar import ComstarGateway
# from vnpy.gateway.futu import FutuGateway
# from vnpy.gateway.ib import IbGateway
# from vnpy.gateway.tiger import TigerGateway
# from vnpy.gateway.tap import TapGateway
# from vnpy.gateway.da import DaGateway
# from vnpy.gateway.mt5 import Mt5Gateway
# from vnpy.gateway.binance import BinanceGateway
# from vnpy.gateway.binances import BinancesGateway
# from vnpy.gateway.huobi import HuobiGateway
# from vnpy.gateway.huobif import HuobifGateway
# from vnpy.gateway.huobis import HuobisGateway
# from vnpy.gateway.huobio import HuobioGateway
# from vnpy.gateway.okex import OkexGateway
# from vnpy.gateway.okexf import OkexfGateway
# from vnpy.gateway.okexs import OkexsGateway
# from vnpy.gateway.okexo import OkexoGateway
# from vnpy.gateway.bitmex import BitmexGateway
# from vnpy.gateway.bybit import BybitGateway
# from vnpy.gateway.gateios import GateiosGateway
# from vnpy.gateway.deribit import DeribitGateway
# from vnpy.gateway.bitfinex import BitfinexGateway
# from vnpy.gateway.coinbase import CoinbaseGateway
# from vnpy.gateway.bitstamp import BitstampGateway
# from vnpy.gateway.onetoken import OnetokenGateway
# from vnpy.gateway.rohon import RohonGateway
# from vnpy.gateway.xgj import XgjGateway
# from vnpy.gateway.alpaca import AlpacaGateway

from vnpy.app.cta_strategy import CtaStrategyApp
from vnpy.app.cta_backtester import CtaBacktesterApp
from vnpy.app.spread_trading import SpreadTradingApp
from vnpy.app.algo_trading import AlgoTradingApp
from vnpy.app.option_master import OptionMasterApp
from vnpy.app.portfolio_strategy import PortfolioStrategyApp
from vnpy.app.script_trader import ScriptTraderApp
from vnpy.app.market_radar import MarketRadarApp
from vnpy.app.chart_wizard import ChartWizardApp
from vnpy.app.rpc_service import RpcServiceApp
from vnpy.app.excel_rtd import ExcelRtdApp
from vnpy.app.data_manager import DataManagerApp
# from vnpy.app.data_recorder import DataRecorderApp
from vnpy.app.risk_manager import RiskManagerApp
from vnpy.app.portfolio_manager import PortfolioManagerApp
# from vnpy.app.paper_account import PaperAccountApp



DAY_START = time(8, 45)
DAY_END = time(15, 1)

NIGHT_START = time(20, 45)
NIGHT_END = time(2, 45)


def check_trading_period():
    """"""
    current_time = datetime.now().time()

    trading = False

    if (
        (DAY_START <= current_time <= DAY_END)
        or (current_time >= NIGHT_START)
        or (current_time <= NIGHT_END)
    ):
        trading = True

    return trading

def run_child():
    """
    Running in the child process.
    """

    ctp_setting = {
    "用户名": "167465",
    "密码": "hun829248",
    "经纪商代码": "9999",
    "交易服务器": "180.168.146.187:10202",
    "行情服务器": "180.168.146.187:10212",
    "产品名称": "simnow_client_test",
    "授权编码": "0000000000000000",
    "产品信息": "simnow_client_test"
    }

    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    main_engine.add_gateway(CtpGateway)
    main_engine.add_gateway(CtptestGateway)
    # main_engine.add_gateway(MiniGateway)
    # main_engine.add_gateway(MinitestGateway)
    # main_engine.add_gateway(FemasGateway)
    # main_engine.add_gateway(SoptGateway)
    # main_engine.add_gateway(SopttestGateway)
    # main_engine.add_gateway(SecGateway)    
    # main_engine.add_gateway(UftGateway)
    # main_engine.add_gateway(HsoptionGateway)
    # main_engine.add_gateway(XtpGateway)
    # main_engine.add_gateway(ToraStockGateway)
    # main_engine.add_gateway(ToraOptionGateway)
    # main_engine.add_gateway(OesGateway)
    # main_engine.add_gateway(ComstarGateway)
    # main_engine.add_gateway(FutuGateway)
    # main_engine.add_gateway(IbGateway)
    # main_engine.add_gateway(TigerGateway)
    # main_engine.add_gateway(TapGateway)
    # main_engine.add_gateway(DaGateway)
    # main_engine.add_gateway(Mt5Gateway)
    # main_engine.add_gateway(BinanceGateway)
    # main_engine.add_gateway(BinancesGateway)    
    # main_engine.add_gateway(HuobiGateway)
    # main_engine.add_gateway(HuobifGateway)
    # main_engine.add_gateway(HuobisGateway)    
    # main_engine.add_gateway(HuobioGateway)
    # main_engine.add_gateway(OkexGateway)
    # main_engine.add_gateway(OkexfGateway)
    # main_engine.add_gateway(OkexsGateway)
    # main_engine.add_gateway(OkexoGateway)
    # main_engine.add_gateway(BitmexGateway)
    # main_engine.add_gateway(BybitGateway)
    # main_engine.add_gateway(GateiosGateway)
    # main_engine.add_gateway(DeribitGateway)
    # main_engine.add_gateway(BitfinexGateway)
    # main_engine.add_gateway(CoinbaseGateway)
    # main_engine.add_gateway(BitstampGateway)
    # main_engine.add_gateway(OnetokenGateway)
    # main_engine.add_gateway(RohonGateway) 
    # main_engine.add_gateway(XgjGateway)       
    # main_engine.add_gateway(AlpacaGateway)

    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(SpreadTradingApp)
    main_engine.add_app(AlgoTradingApp)
    main_engine.add_app(OptionMasterApp)
    main_engine.add_app(PortfolioStrategyApp)
    main_engine.add_app(ScriptTraderApp)
    main_engine.add_app(MarketRadarApp)
    main_engine.add_app(ChartWizardApp)
    main_engine.add_app(RpcServiceApp)
    main_engine.add_app(ExcelRtdApp)
    main_engine.add_app(DataManagerApp)
    # main_engine.add_app(DataRecorderApp)
    main_engine.add_app(RiskManagerApp)
    main_engine.add_app(PortfolioManagerApp)
    # main_engine.add_app(PaperAccountApp)


    
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()

    main_engine.connect(ctp_setting, "CTP")
    main_engine.write_log("连接CTP接口")

    sleep(10)

    current_time = datetime.now().time()

    main_engine.send_email("交易界面启动", f"trading ui started, {current_time}", SETTINGS["email.receiver"])

    while True:
        sleep(10)

        trading = check_trading_period()
        if not trading:
            print("关闭子进程")
            current_time = datetime.now().time()
            main_engine.send_email("终极震荡指标策略关闭", f"trading closed, {current_time}", SETTINGS["email.receiver"])
            main_engine.close()
            sys.exit(0)


def run_parent():
    """
    Running in the parent process.
    """
    print("启动CTA策略守护父进程")

    child_process = None

    while True:
        trading = check_trading_period()

        # Start child process in trading period
        if trading and child_process is None:
            print("启动子进程")
            child_process = multiprocessing.Process(target=run_child)
            child_process.start()
            print("子进程启动成功")

        # 非记录时间则退出子进程
        if not trading and child_process is not None:
            if not child_process.is_alive():
                child_process = None
                print("子进程关闭成功")

        sleep(5)


if __name__ == "__main__":
    run_parent()