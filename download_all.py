from core.data_updater import DataUpdater

if __name__ == "__main__":
    print("Starting the full market data download. This will take a long time...")
    updater = DataUpdater()
    updater.run_full_update()
    print("Full market data download process has finished.")
