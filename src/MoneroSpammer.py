from typing import Optional
from time import sleep
from monero import (
    MoneroDaemon, MoneroDaemonRpc, MoneroWallet, MoneroRpcConnection, MoneroTxPriority,
    MoneroAccount, MoneroTxConfig, MoneroDestination, MoneroTxWallet, MoneroError, MoneroUtils
)
from .utils import MoneroWalletLoader, MoneroWalletTracker, Utils, NotEnoughBalanceException, WaitingForUnlockedFundsException


class MoneroSpammer:

    AMOUNT: int = MoneroUtils.xmr_to_atomic_units(0.01)
    SEND_DIVISOR: int = 10
    SYNC_PERIOD_MS: int = 10000

    _disposed: bool
    _connection: MoneroRpcConnection                                                                                                                                                                                                                                                                                                                                                                    
    _daemon: Optional[MoneroDaemon]
    _wallets: Optional[list[MoneroWallet]]
    _tracker: MoneroWalletTracker = MoneroWalletTracker()
    _result: dict[str, list[MoneroTxWallet]] = {}
    _num_wallets: int

    def __init__(self, connection: MoneroRpcConnection, num_wallets: int):
        MoneroUtils.set_log_level(0)
        self._connection = connection
        self._daemon = None
        self._wallets = None
        self._disposed = False
        self._num_wallets = num_wallets

    def __del__(self) -> None:
        self.dispose()

    def _create_txs(self, wallet: MoneroWallet, num_accounts: int, num_subaddresses_per_account: int, can_split: bool, send_amount_per_subaddress: Optional[int] = None, subtract_fee_from_destinations: bool = False) -> list[MoneroTxWallet]:
        daemon = self.get_daemon()

        self._tracker.wait_for_unlocked_balance(daemon, self.SYNC_PERIOD_MS, wallet, 0)

        # compute the minimum account unlocked balance needed in order to fulfill the config
        total_subbadresses: int = num_accounts * num_subaddresses_per_account
        min_account_amount: int = self.AMOUNT + (self.AMOUNT * total_subbadresses * self.SEND_DIVISOR)

        if send_amount_per_subaddress is not None:
            min_account_amount = total_subbadresses * (send_amount_per_subaddress + self.AMOUNT)

        # send funds from first account with sufficient unlocked funds
        src_account: Optional[MoneroAccount] = None
        has_balance: bool = False
        accounts = wallet.get_accounts()

        for account in accounts:
            account_balance = account.balance if account.balance is not None else 0
            account_unlocked_balance = account.unlocked_balance if account.unlocked_balance is not None else 0
            
            if account_balance > min_account_amount:
                has_balance = True
            if account_unlocked_balance > min_account_amount:
                src_account = account
                break
        
        if not has_balance:
            raise NotEnoughBalanceException(wallet)
        
        if src_account is None:
            raise WaitingForUnlockedFundsException(wallet)
        
        if src_account.index is None:
            raise Exception(f"Account index is None")

        balance = src_account.balance if src_account.balance is not None else 0
        unlocked_balance = src_account.unlocked_balance if src_account.unlocked_balance is not None else 0

        # get amount to send total and per subaddress
        send_amount: int = 0

        if send_amount_per_subaddress is None:
            send_amount = self.AMOUNT * 5 * total_subbadresses
            send_amount_per_subaddress = int(send_amount / total_subbadresses)
        else:
            send_amount = send_amount_per_subaddress * total_subbadresses

        # create minimum number of accounts
        accounts = wallet.get_accounts()

        i: int = 0

        while i < (num_accounts - len(accounts)):
            wallet.create_account()
            i += 1

        # create minimum number of subaddresses per account and collect destination addresses
        destination_addresses: list[str] = []

        for i in range(num_accounts):
            subaddresses = wallet.get_subaddresses(i)
            
            for i in range(num_subaddresses_per_account - len(subaddresses)):
                wallet.create_subaddress(i)
            
            subaddresses = wallet.get_subaddresses(i)

            if len(subaddresses) < num_subaddresses_per_account:
                raise Exception(f"Could not create {num_subaddresses_per_account} for account {i}")
            
            for i in range(num_subaddresses_per_account):
                subaddress = subaddresses[i]
                if subaddress.address is None:
                    raise Exception("Subaddress address is None")
                destination_addresses.append(subaddress.address)

        # build tx config
        destinations: list[MoneroDestination] = []
        subtract_fee_from: list[int] = []

        j: int = 0

        for address in destination_addresses:
            destinations.append(MoneroDestination(address, send_amount_per_subaddress))
            subtract_fee_from.append(j)
            j += 1

        config = MoneroTxConfig()
        config.account_index = src_account.index
        # config.subaddress_indices = None
        config.destinations = destinations
        config.relay = True
        config.can_split = can_split
        config.priority = MoneroTxPriority.NORMAL

        if subtract_fee_from_destinations is True:
            config.subtract_fee_from = subtract_fee_from
        
        # send tx(s) with config
        txs: list[MoneroTxWallet] = []

        try:
            txs = wallet.create_txs(config)
        except MoneroError as e:
            # test error applying subtract_from_fee with split txs
            if (subtract_fee_from_destinations and len(txs) == 0):
                if 'subtractfeefrom transfers cannot be split over multiple transactions yet' not in str(e):
                    raise e
                
                return []
            
            raise e
        
        if can_split is not True and len(txs) != 1:
            raise Exception("Expected 1 tx")
        
        # test that wallet balance decreased
        account: MoneroAccount = wallet.get_account(src_account.index)

        if account.balance is None:
            raise Exception("Account balance is None")
        
        if account.unlocked_balance is None:
            raise Exception("Account unlocked balance is None")

        if account.balance >= balance:
            raise Exception(f"Exptected balance decrease from account {account.index}")
        
        if account.unlocked_balance >= unlocked_balance:
            raise Exception(f"Exptected unlocked balance decrease from account {account.index}")
        
        return txs

    def _send_to_multiple(self, wallet: MoneroWallet) -> list[MoneroTxWallet]:
        return self._create_txs(wallet, 3, 15, True)

    def start(self) -> None:
        wallets: list[MoneroWallet] = []
        try:
            wallets = self.get_wallets()

            for wallet in wallets:
                path = wallet.get_path()
                self._result[path] = self._send_to_multiple(wallet)
                
                sleep(10)
                wallet.save()
            
            daemon = self.get_daemon()

            while True:
                self._tracker.wait_for_unlocked_balances(daemon, self.SYNC_PERIOD_MS, wallets, 0)

                for wallet in wallets:
                    txs: list[MoneroTxWallet] = self._send_to_multiple(wallet)

                    for tx in txs:
                        print(f"Spammed tx {tx.hash}, amount: {MoneroUtils.atomic_units_to_xmr(Utils.get_tx_sent_amount(tx))}")

                sleep(10)

        except Exception as e:
            print(f"[!] An error occurred: {e}")
    
    def get_result(self) -> dict[str, list[MoneroTxWallet]]:
        return self._result

    def get_daemon(self) -> MoneroDaemon:
        if self._daemon is None:
            if not self._connection.is_connected() and not self._connection.check_connection(20000):
                msg = f"Could not connect to daemon RPC at {self._connection.uri}"
                print(f"[!] {msg}")
                raise Exception(msg)

            self._daemon = MoneroDaemonRpc(self._connection)

        return self._daemon

    def get_wallets(self) -> list[MoneroWallet]:
        daemon = self.get_daemon()

        if self._wallets is None:
            self._wallets = MoneroWalletLoader.load_wallets(self._connection, daemon.get_height(), self._num_wallets)
        
        return self._wallets
    
    def fund_wallets(self, amount_xmr: int = 1):
        """
        Convenience function for printing funding info
        """

        wallets = self.get_wallets()
        amount = amount_xmr / len(wallets)
        i: int = 1
        
        for wallet in wallets:
            print(f"[{i}] Send {amount} to {wallet.get_primary_address()}")
            i += 1

    def dispose(self) -> None:
        print("[*] Disposing monero spammer...")
        if self._disposed:
            return

        if self._wallets is not None:
            for wallet in self._wallets:
                wallet.close(True)

            self._wallets = None
        print("[*] Monero spammer disposed succesfully")
