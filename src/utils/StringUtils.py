from monero import MoneroWallet, MoneroUtils, MoneroOutgoingTransfer, MoneroIncomingTransfer, MoneroOutputWallet, MoneroOutputQuery
from .Utils import Utils


class StringUtils:

    @classmethod
    def is_null_or_empty(cls, string: str | None) -> bool:
        return string is None or string == ''

    @classmethod
    def print_output(cls, output: MoneroOutputWallet | None, skip_spent: bool = True) -> None:
        if output is None or (skip_spent and output.is_spent):
            return
        
        assert output.amount is not None

        print(f"\t[*] Output: {MoneroUtils.atomic_units_to_xmr(output.amount):.12f} XMR, Subaddress index: {output.account_index},{output.subaddress_index}, Key: {output.stealth_public_key}, spent: {output.is_spent}")

    @classmethod
    def print_outputs(cls, outputs: list[MoneroOutputWallet]) -> None:
        for output in outputs:
            cls.print_output(output)

    @classmethod
    def print_wallet_outputs(cls, wallets: list[MoneroWallet]) -> None:
        query = MoneroOutputQuery()
        index: int = 1
        for wallet in wallets:
            print(f"[*] spam_wallet_{index} unspent outputs:")
            outputs = wallet.get_outputs(query)
            cls.print_outputs(outputs)
            index += 1
    
    @classmethod
    def print_outgoing_transfer(cls, transfer: MoneroOutgoingTransfer | None) -> None:
        if transfer is None:
            return
        
        for dest in transfer.destinations:
            assert dest.amount is not None
            print(f"\t\t[*] Sent {MoneroUtils.atomic_units_to_xmr(dest.amount):.12f} XMR from account: {transfer.account_index}, Destination: {dest.address}")

    @classmethod
    def print_incoming_transfer(cls, transfer: MoneroIncomingTransfer | None) -> None:
        if transfer is None:
            return
        
        assert transfer.amount is not None
        print(f"\t\t[*] Received {MoneroUtils.atomic_units_to_xmr(transfer.amount):.12f} XMR to account {transfer.account_index}, subaddress idx: {transfer.subaddress_index}, address: {transfer.address}")

    @classmethod
    def print_incoming_transfers(cls, transfers: list[MoneroIncomingTransfer]) -> None:
        for transfer in transfers:
            cls.print_incoming_transfer(transfer)

    @classmethod
    def print_txs(cls, wallet: MoneroWallet | list[MoneroWallet]) -> None:
        wallets: list[MoneroWallet] = [wallet] if isinstance(wallet, MoneroWallet) else wallet
        
        for wallet in wallets:
            print(f"[*] Getting wallet {wallet.get_path()} transactions...")
            txs = wallet.get_txs()
            print(f"[*] Wallet {wallet.get_path()} has {len(txs)} transaction(s)")
            for tx in txs:
                sent = MoneroUtils.atomic_units_to_xmr(Utils.get_tx_sent_amount(tx))
                received = MoneroUtils.atomic_units_to_xmr(Utils.get_tx_received_amount(tx))
                print(f"\t[*] hash {tx.hash}, sent: {sent:.12f} XMR, received: {received:.12f} XMR, confirmations: {tx.num_confirmations}")
                cls.print_incoming_transfers(tx.incoming_transfers)
                cls.print_outgoing_transfer(tx.outgoing_transfer)

    @classmethod
    def print_primary_addresses(cls, wallets: list[MoneroWallet]) -> None:
        i: int = 1
        for wallet in wallets:
            balance = wallet.get_balance(0, 0)
            print(f"[{i}] address {wallet.get_primary_address()}, balance: {MoneroUtils.atomic_units_to_xmr(balance):.12f} XMR")
            i += 1

    @classmethod
    def print_wallet_subaddresses(cls, wallet: MoneroWallet, index: int) -> None:
        print(f"[*] spam_wallet_{index} subaddresses")
        accounts = wallet.get_accounts(True)

        for account in accounts:
            for subaddress in account.subaddresses:
                print(f"\t[*] Account: {subaddress.account_index}, Index: {subaddress.index}, Balance {subaddress.balance}, Address: {subaddress.address}")

    @classmethod
    def print_subaddresses(cls, wallets: list[MoneroWallet]) -> None:
        i: int = 1
        for wallet in wallets:
            cls.print_wallet_subaddresses(wallet, i)
            i += 1

    @classmethod
    def print_wallet_balances(cls, wallets: list[MoneroWallet]) -> None:
        i: int = 1
        for wallet in wallets:
            balance = wallet.get_balance()
            print(f"[*] spam_wallet_{i} balance: {MoneroUtils.atomic_units_to_xmr(balance):.12f} XMR")
            i += 1

    @classmethod
    def print_wallet_seeds(cls, wallets: list[MoneroWallet]) -> None:
        i: int = 1
        for wallet in wallets:
            seed = wallet.get_seed()
            restore_height = wallet.get_restore_height()
            print(f"[*] spam_wallet_{i}")
            print(f"\tseed: {seed}")
            print(f"\trestore height: {restore_height}")
            i += 1
