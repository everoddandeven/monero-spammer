from monero import MoneroWallet


class NotEnoughBalanceException(Exception):

    wallet: MoneroWallet | None

    def __init__(self, wallet: MoneroWallet | None = None) -> None:
        
        msg = f"Wallet does not have enough balance." if wallet is None else f"Wallet at {wallet.get_path()} does not have enough balance."
        super(NotEnoughBalanceException, self).__init__(msg)        
        self.wallet = wallet
