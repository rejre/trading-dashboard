from core.backtester import Backtester
from datetime import datetime

if __name__ == "__main__":
    param_grid = {
        'score_threshold': [3, 2, 1]
    }

    for threshold in param_grid['score_threshold']:
        print(f"\n{'='*40}")
        print(f"Running Backtest: Market Judge Threshold >= {threshold}")
        print(f"{'='*40}")

        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        initial_capital = 1000000
        strategy_params = {'trough_distance': 10}

        backtester = Backtester(
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            strategy_params=strategy_params,
            market_judge_score_threshold=threshold
        )
        
        backtester.run()
        backtester.generate_report()

