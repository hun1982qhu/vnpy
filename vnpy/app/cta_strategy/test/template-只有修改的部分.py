    def run_optimization(self, optimization_setting: OptimizationSetting, output=True):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting()
        target_name = optimization_setting.target_name

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return

        # Use multiprocessing pool for running backtesting with different setting
        # Force to use spawn method to create new process (instead of fork on Linux)
        ctx = multiprocessing.get_context("spawn")
        pool = ctx.Pool(multiprocessing.cpu_count())

        optimization_length = len(settings)  # 自己新增 获得参数优化组合总数
        manager = multiprocessing.Manager()  # 自己新增，定义一个多进程管理对象
        processing_counter = manager.Value("i", 0)  # 自己新增，定义一个进程计数器,int类型
        processing_lock = manager.Lock()  # 自己新增，如果counter被一个进程修改时，加锁

        results = []
        # 自己新增，在参数中添加了optimization_length、processing_counter、processing_lock
        for setting in settings:
            result = (pool.apply_async(optimize, (
                target_name,
                self.strategy_class,
                setting,
                self.vt_symbol,
                self.interval,
                self.start,
                self.rate,
                self.slippage,
                self.size,
                self.pricetick,
                self.capital,
                self.end,
                self.mode,
                self.inverse,
                optimization_length,
                processing_counter,
                processing_lock
            )))
            results.append(result)

        pool.close()
        pool.join()

        # Sort results and output
        result_values = [result.get() for result in results]
        result_values.sort(reverse=True, key=lambda result: result[1])

        if output:
            for value in result_values:
                msg = f"参数：{value[0]}, 目标：{value[1]}"
                self.output(msg)

        return result_values

    # 在def calculate_result中增加了count、length、single_round_time
    def calculate_result(self, count: int=0, length: int=0, single_round_time: float=0):
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

        # 自己新增
        print(f"参数组合总数：{length}")
        if count != 0:
            print(f"已完成回测{count}次")
        
        total_backtesting_time = length * single_round_time
        total_timedelta = timedelta(seconds=total_backtesting_time)
        used_time = count * single_round_time
        used_timedelta = timedelta(seconds=used_time)
        remaining_timedelta = total_timedelta - used_timedelta
        expected_finish_time = datetime.now() + remaining_timedelta
        print(f"单次回测时间耗时:{single_round_time}")
        print(f"完成参数优化共需耗时:{total_timedelta}")
        print(f"参数优化程序已用时:{used_timedelta}")     
        print(f"预计完成参数优化时间为:{expected_finish_time}")

        return self.daily_df

    # 自己新增，原来是def calculate_result函数，现在复制该函数，改为calculate_result_ga函数
    def calculate_result_ga(self):
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

def optimize(
    target_name: str,
    strategy_class: CtaTemplate,
    setting: dict,
    vt_symbol: str,
    interval: Interval,
    start: datetime,
    rate: float,
    slippage: float,
    size: float,
    pricetick: float,
    capital: int,
    end: datetime,
    mode: BacktestingMode,
    inverse: bool,
    optimization_length,
    processing_counter,
    processing_lock
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingEngine()

    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        end=end,
        mode=mode,
        inverse=inverse
    )

    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    
    # 自己新增，用于计时
    start1 = time()
    
    engine.run_backtesting()

    # 自己新增，每跑完一次回测，counter就加1
    with processing_lock:
        processing_counter.value += 1

    # 自己新增
    end1 = time()
    # 自己新增
    single_round_time: float = end1 - start1
    # 自己新增
    print(f"单次运行回测时间:{single_round_time}秒")    

    # 原来没有参数，新增了processing_counter.value和optimiza_length作为入参
    engine.calculate_result(processing_counter.value, optimization_length, single_round_time)
    statistics = engine.calculate_statistics(output=False)

    target_value = statistics[target_name]
    return (str(setting), target_value, statistics)

# 自己新增，复制了原有的def optimize函数，将函数名改为def optimize_ga，专门供def _ga_optimize函数调用，在调用遗传算法时使用
# 将该函数中原本调用engine.calculate_result函数的，改为调用engine.calculate_result_ga
def optimize_ga(
    target_name: str,
    strategy_class: CtaTemplate,
    setting: dict,
    vt_symbol: str,
    interval: Interval,
    start: datetime,
    rate: float,
    slippage: float,
    size: float,
    pricetick: float,
    capital: int,
    end: datetime,
    mode: BacktestingMode,
    inverse: bool
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingEngine()

    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        end=end,
        mode=mode,
        inverse=inverse
    )

    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    # 将该函数中原本调用engine.calculate_result函数的，改为调用engine.calculate_result_ga
    engine.calculate_result_ga()
    statistics = engine.calculate_statistics(output=False)

    target_value = statistics[target_name]
    return (str(setting), target_value, statistics)

@lru_cache(maxsize=1000000)
def _ga_optimize(parameter_values: tuple):
    """"""
    setting = dict(parameter_values)

    # 自己新增，原来用的是optimize函数，自己修改成optimize_ga函数
    result = optimize_ga(
        ga_target_name,
        ga_strategy_class,
        setting,
        ga_vt_symbol,
        ga_interval,
        ga_start,
        ga_rate,
        ga_slippage,
        ga_size,
        ga_pricetick,
        ga_capital,
        ga_end,
        ga_mode,
        ga_inverse
    )
    return (result[1],)    