import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np

# Clean and prepare data
data = pd.read_csv("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv")
data.columns = data.columns.str.strip().str.lower()  # Clean column names
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])  # Drop unnamed columns

# Map columns to required format
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

# Ensure datetime is in the correct format
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# Strategy Implementation
class VWAPStrategy(Strategy):
    # Parameters for optimization
    rsi_period = 14
    atr_period = 14
    risk_per_trade = 0.01  # 1% risk per trade
    take_profit_multiplier = 2  # 2:1 risk-reward ratio
    stop_loss_multiplier = 1  # 1x ATR for stop loss

    def init(self):
        # Calculate VWAP
        self.vwap = self.I(talib.VWAP, self.data.High, self.data.Low, self.data.Close, self.data.Volume)

        # Calculate RSI for confirmation
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)

        # Calculate ATR for stop loss
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)

        # Calculate average volume for confirmation
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)

        # Debug prints
        print("🌙 Moon Dev VWAP Strategy Initialized! ✨")
        print(f"RSI Period: {self.rsi_period}, ATR Period: {self.atr_period}")
        print(f"Risk per Trade: {self.risk_per_trade * 100}% 🚀")

    def next(self):
        # Entry Logic
        if not self.position:
            # Bullish Entry: Price crosses above VWAP, RSI > 50, Volume > Average
            if crossover(self.data.Close, self.vwap) and self.rsi > 50 and self.data.Volume[-1] > self.avg_volume[-1]:
                stop_loss = self.data.Close[-1] - self.stop_loss_multiplier * self.atr[-1]
                take_profit = self.data.Close[-1] + self.take_profit_multiplier * (self.data.Close[-1] - stop_loss)
                position_size = (self.equity * self.risk_per_trade) / (self.data.Close[-1] - stop_loss)
                self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                print(f"🌙 Bullish Entry! 🚀 Price: {self.data.Close[-1]}, SL: {stop_loss}, TP: {take_profit}")

            # Bearish Entry: Price crosses below VWAP, RSI < 50, Volume > Average
            elif crossover(self.vwap, self.data.Close) and self.rsi < 50 and self.data.Volume[-1] > self.avg_volume[-1]:
                stop_loss = self.data.Close[-1] + self.stop_loss_multiplier * self.atr[-1]
                take_profit = self.data.Close[-1] - self.take_profit_multiplier * (stop_loss - self.data.Close[-1])
                position_size = (self.equity * self.risk_per_trade) / (stop_loss - self.data.Close[-1])
                self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                print(f"🌙 Bearish Entry! 🚀 Price: {self.data.Close[-1]}, SL: {stop_loss}, TP: {take_profit}")

        # Exit Logic
        if self.position:
            # Exit if price reverts to VWAP
            if self.position.is_long and crossover(self.vwap, self.data.Close):
                self.position.close()
                print(f"🌙 Long Position Closed! ✨ Price reverted to VWAP: {self.data.Close[-1]}")
            elif self.position.is_short and crossover(self.data.Close, self.vwap):
                self.position.close()
                print(f"🌙 Short Position Closed! ✨ Price reverted to VWAP: {self.data.Close[-1]}")

# Backtest Execution
bt = Backtest(data, VWAPStrategy, cash=1_000_000, commission=0.001)

# Initial Backtest
stats = bt.run()
print(stats)
print(stats._strategy)
bt.plot()

# Parameter Optimization
optimization_results = bt.optimize(
    rsi_period=range(10, 20, 2),
    atr_period=range(10, 20, 2),
    take_profit_multiplier=[1.5, 2, 2.5],
    stop_loss_multiplier=[1, 1.5, 2],
    maximize='Return [%]'
)
print(optimization_results)
bt.plot()