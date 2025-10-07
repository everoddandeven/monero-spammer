from monero import MoneroWallet


class WaitingForUnlockedFundsException(Exception):

    wallet: MoneroWallet | None

    def __init__(self, wallet: MoneroWallet | None = None) -> None:
        
        msg = f"Wallet is waiting on unlocked funds." if wallet is None else f"Wallet at {wallet.get_path()} is waiting on unlocked funds."
        super(WaitingForUnlockedFundsException, self).__init__(msg)        
        self.wallet = wallet
