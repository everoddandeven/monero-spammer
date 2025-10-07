from typing import Optional
from time import sleep
from monero import (
    MoneroDaemon, MoneroDaemonRpc, MoneroWallet, MoneroRpcConnection, MoneroTxPriority,
    MoneroAccount, MoneroTxConfig, MoneroDestination, MoneroTxWallet, MoneroError, MoneroUtils,
    MoneroSubaddress
)
from .utils import MoneroWalletLoader, MoneroWalletTracker, NotEnoughBalanceException, WaitingForUnlockedFundsException


class MoneroSpammer:

    AMOUNT: int = 750000
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

    def _send_to_multiple(self, wallet: MoneroWallet, num_accounts: int = 1, num_subaddresses_per_account: int = 2, can_split: bool = True, send_amount_per_subaddress: Optional[int] = None, subtract_fee_from_destinations: bool = False) -> list[MoneroTxWallet]:
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
            account = wallet.create_account()
            print(f"[*] Created account {account.index} for wallet {wallet.get_path()}")
            i += 1

        # create minimum number of subaddresses per account and collect destination addresses
        destination_addresses: list[str] = []

        for i in range(num_accounts):
            subaddresses = wallet.get_subaddresses(i)
            
            for j in range(num_subaddresses_per_account - len(subaddresses)):
                print(f"[*] Creating subaddress {j} for account {i}...")
                wallet.create_subaddress(i)
                print(f"[*] Created subaddress {j} for account {i}")
            
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
            print("[*] Creating txs...")
            txs = wallet.create_txs(config)
            print(f"[*] Created {len(txs)}")
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

    def _send_from_multiple(self, wallet: MoneroWallet, can_split: bool = True) -> list[MoneroTxWallet]:
        daemon = self.get_daemon()
        self._tracker.wait_for_wallet_txs_to_clear_pool(daemon, self.SYNC_PERIOD_MS, [wallet])
        config = MoneroTxConfig()
        config.can_split = can_split

        # number of subaddresses to send from
        num_subaddresses: int = 2

        # get first account with (NUM_SUBADDRESSES + 1) subaddresses with unlocked balances
        accounts = wallet.get_accounts(True)
        assert len(accounts) > 2, "This test requires at least 2 accounts; run send-to-multiple test"
        src_account: Optional[MoneroAccount] = None
        unlocked_subaddresses: list[MoneroSubaddress] = []
        has_balance: bool = False

        for account in accounts:
            unlocked_subaddresses.clear()
            num_subaddress_balances: int = 0

            for subaddress in account.subaddresses:
                assert subaddress.balance is not None
                assert subaddress.unlocked_balance is not None
                if subaddress.balance > self.AMOUNT:
                    num_subaddress_balances += 1
                if subaddress.unlocked_balance > self.AMOUNT:
                    unlocked_subaddresses.append(subaddress)
            
            if num_subaddress_balances >= num_subaddresses + 1:
                has_balance = True
            
            if len(unlocked_subaddresses) >= num_subaddresses + 1:
                src_account = account
                break

        
        assert has_balance, f"Wallet does not have account with {num_subaddresses + 1} subaddresses with balances; run send-to-multiple tests"
        assert len(unlocked_subaddresses) >= num_subaddresses + 1, f"Wallet {wallet.get_path()} is waiting on unlocked funds"
        assert src_account is not None
        assert src_account.index is not None

        # determine the indices of the first two subaddresses with unlocked balances

        from_subaddress_indices: list[int] = []

        for i in range(num_subaddresses):
            index = unlocked_subaddresses[i].index
            assert index is not None
            from_subaddress_indices.append(index)

        # determine the amount to send

        send_amount: int = 0

        for from_subaddress_index in from_subaddress_indices:
            amount = src_account.subaddresses[from_subaddress_index].unlocked_balance
            assert amount is not None
            send_amount += amount

        send_amount = int(send_amount / self.SEND_DIVISOR)

        from_balance: int = 0
        from_unlocked_balance: int = 0

        for subaddress_index in from_subaddress_indices:
            subaddress: MoneroSubaddress = wallet.get_subaddress(src_account.index, subaddress_index)
            assert subaddress.balance is not None
            assert subaddress.unlocked_balance is not None
            from_balance += subaddress.balance
            from_unlocked_balance += subaddress.unlocked_balance

        # send from the first subaddresses with unlocked balances

        address: str = wallet.get_primary_address()
        destinations: list[MoneroDestination] = [MoneroDestination(address, send_amount)]
        config = MoneroTxConfig()
        config.destinations = destinations
        config.account_index = src_account.index
        config.subaddress_indices = from_subaddress_indices
        config.relay = True
        txs: list[MoneroTxWallet] = []

        if config.can_split is not False:
            txs.extend(wallet.create_txs(config))
        else:
            txs.append(wallet.create_tx(config))
        
        if config.can_split is False:
            assert len(txs) == 1, "Must have exactly one tx if no split"
        
        return txs

    def send_to_multiple(self) -> None:
        print("[*] Sending to multiple subaddresses...")
        wallets = self.get_wallets()
        total_txs: int = 0

        for wallet in wallets:
            try:
                txs = self._send_to_multiple(wallet)
                total_txs = len(txs)
                print(f"[*] Spammed {len(txs)} txs from wallet at {wallet.get_path()}")
                sleep(2)
                wallet.save()
            except Exception as e:
                print(f"[!] Could not send txs from {wallet.get_path()}: {e}")
                input(f"[>] Press Enter to continue: ")

        print(f"[*] Spammed a total of {total_txs} txs")

    def send_from_multiple(self) -> None:
        print("[*] Sending from multiple subaddresses...")
        wallets = self.get_wallets()
        total_txs: int = 0

        for wallet in wallets:
            try:
                txs = self._send_from_multiple(wallet)
                total_txs = len(txs)
                print(f"[*] Spammed {len(txs)} txs from wallet at {wallet.get_path()}")
                sleep(2)
                wallet.save()
            except Exception as e:
                print(f"[!] Could not send txs from {wallet.get_path()}: {e}")
                input(f"[>] Press Enter to continue: ")

        print(f"[*] Spammed a total of {total_txs} txs")
    
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
