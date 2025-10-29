from typing import override

from monero import MoneroWalletListener


class SyncProgressHandler(MoneroWalletListener):

    wallet_name: str

    def __init__(self, wallet_name: str) -> None:
        MoneroWalletListener.__init__(self)
        self.wallet_name = wallet_name
    
    @override
    def on_sync_progress(self, height: int, start_height: int, end_height: int, percent_done: float, message: str) -> None:
        print(f"[{self.wallet_name}] sync progress {height}/{end_height} {percent_done*100} %")
