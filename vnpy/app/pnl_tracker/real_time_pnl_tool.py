from copy import copy
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

import numpy as np
from pandas import DataFrame

from vnpy.trader.constant import Direction, Offset
from vnpy.trader.object import BarData

from collections import defaultdict


@dataclass
class PnlOrderData:
    """虚拟委托数据"""
    direction: Direction
    offset: Offset
    price: float
    volume: float


@dataclass
class PnlTradeData:
    """虚拟成交数据"""
    datetime: datetime
    direction: Direction
    offset: Offset
    price: float
    volume: float


class RealtimePnlTracker:
    """"""

    def __init__(self, size: int, balance: int = 0):
        """"""
        self._pos: int = 0                          # 当前持仓
        self._size: int = size                      # 合约乘数
        self._balance: int = balance                # 当前的累计净值
        self._last_bar: BarData = None              # 上一根K线对象
        self._balances: Dict[datetime, float] = {}  # 净值记录
        self._pnls: Dict[datetime, float] = {}      # 盈亏记录
        self._orders: List[PnlOrderData] = []       # 委托记录（活动状态）
        self._trades: List[PnlTradeData] = []       # 成交记录

    def _send_order(
        self, direction: Direction, offset: Offset, price: float, volume: float
    ) -> None:
        """
        缓存限价委托信息
        """
        order = PnlOrderData(direction, offset, price, volume)
        self._orders.append(order)

    def buy(self, price: float, volume: float) -> None:
        """买开"""
        self._send_order(Direction.LONG, Offset.OPEN, price, volume)

    def sell(self, price: float, volume: float) -> None:
        """卖平"""
        self._send_order(Direction.SHORT, Offset.CLOSE, price, volume)

    def short(self, price: float, volume: float) -> None:
        """卖开"""
        self._send_order(Direction.SHORT, Offset.OPEN, price, volume)

    def cover(self, price: float, volume: float) -> None:
        """买平"""
        self._send_order(Direction.LONG, Offset.CLOSE, price, volume)

    def cancel_all(self) -> None:
        """全撤"""
        self._orders.clear()

    def on_bar(self, bar: BarData) -> None:
        """
        K线更新，驱动虚拟委托撮合以及虚拟盈亏计算逻辑。
        """
        # 首先要记录第一根K线收盘价，否则无法计算
        if not self._last_bar:
            self._last_bar = bar
            return

        # 计算盈亏
        holding_pnl = self._calculate_holding_pnl(bar)
        trading_pnl = self._calculate_trading_pnl(bar)

        total_pnl = holding_pnl + trading_pnl
        self._pnls[bar.datetime] = total_pnl

        # 更新累计净值
        self._balance += total_pnl
        self._balances[bar.datetime] = self._balance

        # 保存上一根K线
        self._last_bar = bar

    def _calculate_holding_pnl(self, bar: BarData) -> float:
        """计算持仓盈亏"""
        change = bar.close_price - self._last_bar.close_price
        holding_pnl = change * self._size * self._pos
        return holding_pnl

    def _calculate_trading_pnl(self, bar: BarData) -> float:
        """计算交易盈亏"""
        trading_pnl = 0

        orders = copy(self._orders)
        for order in orders:
            pos_change = 0

            # 买入委托，且K线最低价低于买入限价，则成交
            if (order.direction == Direction.LONG
                    and bar.low_price <= order.price):
                # 成交价格是限价和K线开盘价中的最大值
                trade_price = max(order.price, bar.open_price)
                pos_change = order.volume
            # 卖出则相反
            elif (order.direction == Direction.SHORT
                  and bar.high_price >= order.price):
                trade_price = min(order.price, bar.open_price)
                pos_change = -order.volume

            if pos_change:
                # 更新持仓
                self._pos += pos_change

                # 计算该笔成交到K线收盘的盈亏
                trade_pnl = (bar.close_price - trade_price) * \
                    self._size * pos_change

                # 累加到这根K线的交易盈亏上
                trading_pnl += trade_pnl

                # 从列表中移除已成交的该笔委托
                self._orders.remove(order)

                # 记录成交数据
                trade = PnlTradeData(
                    datetime=bar.datetime,
                    direction=order.direction,
                    offset=order.offset,
                    price=trade_price,
                    volume=order.volume
                )
                self._trades.append(trade)

        return trading_pnl

    def get_pnl_array(self, count: int):
        """获取长度为count的历史盈亏序列"""
        pnls = list(self._pnls.values())
        if len(pnls) < count:
            return None

        array = np.array(pnls[-count:])
        return array

    def get_last_pnl(self):
        """获取最新的盈亏数据"""
        pnls = list(self._pnls.values())
        return pnls[-1]

    def get_last_dt(self):
        """获取最新的盈亏日期"""
        dts = list(self._pnls.keys())
        return dts[-1]

    def get_balance_array(self, count: int):
        """获取长度为count的历史净值序列"""
        balances = list(self._balances.values())
        if len(balances) < count:
            return None

        array = np.array(balances[-count:])
        return array

    def get_last_balance(self):
        """获取最新的净值数据"""
        return self._balance

    def get_all_trades(self):
        """获取所有虚拟成交记录"""
        return copy(self._trades)

    def calculate_result(self):
        """"""
        self.output("开始计算逐日盯市盈亏")

        if not self.trades:
            self.output("成交记录为空，无法计算")
            return

        # Add trade data into daily reuslt.
        for trade in self.trades.values():
            d = trade.datetime.date()
            daily_result = self.daily_results[d]
            daily_result.add_trade(trade)

        # Calculate daily result by iteration.
        pre_close = 0
        start_pos = 0

        for daily_result in self.daily_results.values():
            daily_result.calculate_pnl(
                pre_close,
                start_pos,
                self.size,
                self.rate,
                self.slippage,
                self.inverse
            )

            pre_close = daily_result.close_price
            start_pos = daily_result.end_pos

        # Generate dataframe
        results = defaultdict(list)

        for daily_result in self.daily_results.values():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        self.output("逐日盯市盈亏计算完成")
        return self.daily_df

    def calculate_statistics(self, df: DataFrame = None, output=True):
        """"""
        self.output("开始计算策略统计指标")

        # Check DataFrame input exterior
        if df is None:
            df = self.daily_df

        # Check for init DataFrame
        if df is None:
            # Set all statistics to 0 if no trade.
            start_date = ""
            end_date = ""
            total_days = 0
            profit_days = 0
            loss_days = 0
            end_balance = 0
            max_drawdown = 0
            max_ddpercent = 0
            max_drawdown_duration = 0
            total_net_pnl = 0
            daily_net_pnl = 0
            total_commission = 0
            daily_commission = 0
            total_slippage = 0
            daily_slippage = 0
            total_turnover = 0
            daily_turnover = 0
            total_trade_count = 0
            daily_trade_count = 0
            total_return = 0
            annual_return = 0
            daily_return = 0
            return_std = 0
            sharpe_ratio = 0
            return_drawdown_ratio = 0
        else:
            # Calculate balance related time series data
            df["balance"] = df["net_pnl"].cumsum() + self.capital

            # When balance falls below 0, set daily return to 0
            x = df["balance"] / df["balance"].shift(1)
            x[x <= 0] = np.nan
            df["return"] = np.log(x).fillna(0)

            df["highlevel"] = (
                df["balance"].rolling(
                    min_periods=1, window=len(df), center=False).max()
            )
            df["drawdown"] = df["balance"] - df["highlevel"]
            df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

            # Calculate statistics value
            start_date = df.index[0]
            end_date = df.index[-1]

            total_days = len(df)
            profit_days = len(df[df["net_pnl"] > 0])
            loss_days = len(df[df["net_pnl"] < 0])

            end_balance = df["balance"].iloc[-1]
            max_drawdown = df["drawdown"].min()
            max_ddpercent = df["ddpercent"].min()
            max_drawdown_end = df["drawdown"].idxmin()

            if isinstance(max_drawdown_end, date):
                max_drawdown_start = df["balance"][:max_drawdown_end].idxmax()
                max_drawdown_duration = (max_drawdown_end - max_drawdown_start).days
            else:
                max_drawdown_duration = 0

            total_net_pnl = df["net_pnl"].sum()
            daily_net_pnl = total_net_pnl / total_days

            total_commission = df["commission"].sum()
            daily_commission = total_commission / total_days

            total_slippage = df["slippage"].sum()
            daily_slippage = total_slippage / total_days

            total_turnover = df["turnover"].sum()
            daily_turnover = total_turnover / total_days

            total_trade_count = df["trade_count"].sum()
            daily_trade_count = total_trade_count / total_days

            total_return = (end_balance / self.capital - 1) * 100
            annual_return = total_return / total_days * self.annual_days
            daily_return = df["return"].mean() * 100
            return_std = df["return"].std() * 100

            if return_std:
                daily_risk_free = self.risk_free / np.sqrt(self.annual_days)
                sharpe_ratio = (daily_return - daily_risk_free) / return_std * np.sqrt(self.annual_days)
            else:
                sharpe_ratio = 0

            return_drawdown_ratio = -total_return / max_ddpercent

        # Output
        if output:
            self.output("-" * 30)
            self.output(f"首个交易日：\t{start_date}")
            self.output(f"最后交易日：\t{end_date}")

            self.output(f"总交易日：\t{total_days}")
            self.output(f"盈利交易日：\t{profit_days}")
            self.output(f"亏损交易日：\t{loss_days}")

            self.output(f"起始资金：\t{self.capital:,.2f}")
            self.output(f"结束资金：\t{end_balance:,.2f}")

            self.output(f"总收益率：\t{total_return:,.2f}%")
            self.output(f"年化收益：\t{annual_return:,.2f}%")
            self.output(f"最大回撤: \t{max_drawdown:,.2f}")
            self.output(f"百分比最大回撤: {max_ddpercent:,.2f}%")
            self.output(f"最长回撤天数: \t{max_drawdown_duration}")

            self.output(f"总盈亏：\t{total_net_pnl:,.2f}")
            self.output(f"总手续费：\t{total_commission:,.2f}")
            self.output(f"总滑点：\t{total_slippage:,.2f}")
            self.output(f"总成交金额：\t{total_turnover:,.2f}")
            self.output(f"总成交笔数：\t{total_trade_count}")

            self.output(f"日均盈亏：\t{daily_net_pnl:,.2f}")
            self.output(f"日均手续费：\t{daily_commission:,.2f}")
            self.output(f"日均滑点：\t{daily_slippage:,.2f}")
            self.output(f"日均成交金额：\t{daily_turnover:,.2f}")
            self.output(f"日均成交笔数：\t{daily_trade_count}")

            self.output(f"日均收益率：\t{daily_return:,.2f}%")
            self.output(f"收益标准差：\t{return_std:,.2f}%")
            self.output(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")
            self.output(f"收益回撤比：\t{return_drawdown_ratio:,.2f}")

        statistics = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "capital": self.capital,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "max_drawdown_duration": max_drawdown_duration,
            "total_net_pnl": total_net_pnl,
            "daily_net_pnl": daily_net_pnl,
            "total_commission": total_commission,
            "daily_commission": daily_commission,
            "total_slippage": total_slippage,
            "daily_slippage": daily_slippage,
            "total_turnover": total_turnover,
            "daily_turnover": daily_turnover,
            "total_trade_count": total_trade_count,
            "daily_trade_count": daily_trade_count,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
            "return_drawdown_ratio": return_drawdown_ratio,
        }

        # Filter potential error infinite value
        for key, value in statistics.items():
            if value in (np.inf, -np.inf):
                value = 0
            statistics[key] = np.nan_to_num(value)

        self.output("策略统计指标计算完成")
        return statistics
