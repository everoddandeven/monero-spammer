from abc import ABC
from pathlib import Path
from monero import (
    MoneroWallet, MoneroWalletFull, MoneroWalletConfig, 
    MoneroNetworkType, MoneroRpcConnection
)

from .SyncProgressHandler import SyncProgressHandler


class MoneroWalletLoader(ABC):

    WALLETS_DIR: str = "spam_wallets"

    @classmethod
    def _spam_wallets_dir_exists(cls) -> bool:
        folder = Path(cls.WALLETS_DIR)
        return folder.is_dir() and folder.exists()

    @classmethod
    def _create_spam_wallet_dir(cls) -> None:
        folder = Path(cls.WALLETS_DIR)
        folder.mkdir(exist_ok=True)

    @classmethod
    def _get_wallet_name(cls, index: int) -> str:
        return f"spam_wallet_{index}"

    @classmethod
    def _get_wallet_path(cls, index: int) -> str:
        return f"{cls.WALLETS_DIR}/{cls._get_wallet_name(index)}"

    @classmethod
    def load_wallet(cls, index: int, connection: MoneroRpcConnection, restore_height: int) -> MoneroWallet:
        wallet_path = cls._get_wallet_path(index)
        wallet_name = cls._get_wallet_name(index)
        wallet: MoneroWallet

        if not MoneroWalletFull.wallet_exists(wallet_path):
            print(f"[*] Generating wallet {wallet_name}...")
            config = MoneroWalletConfig()
            config.path = wallet_path
            config.account_lookahead = 50
            config.subaddress_lookahead = 2
            config.password = "password"
            config.network_type = MoneroNetworkType.TESTNET
            # config.restore_height = restore_height
            wallet = MoneroWalletFull.create_wallet(config)
            print(f"[*] Generated new wallet {wallet_name} at {wallet_path}")
            wallet.set_restore_height(restore_height)
        else:
            print(f"[*] Loading wallet {wallet_name} at {wallet_path}")
            wallet = MoneroWalletFull.open_wallet(wallet_path, "password", MoneroNetworkType.TESTNET)

        wallet.set_daemon_connection(connection)
        rpc_connection = wallet.get_daemon_connection()

        if rpc_connection is None:
            raise Exception("Could not set wallet daemon rpc connection")

        if not wallet.is_connected_to_daemon():
            raise Exception(f"Wallet could not connect to daemon at {connection.uri}")

        listener = SyncProgressHandler(wallet.get_path())
        wallet.sync(listener)
        wallet.start_syncing()
        wallet.set_subaddress_label(0, 0, wallet_name)
        wallet.save()
        print(f"[*] Loaded wallet {wallet_name}")
        return wallet

    @classmethod
    def load_wallets(cls, connection: MoneroRpcConnection, restore_height: int, n: int = 5) -> list[MoneroWallet]:
        wallets: list[MoneroWallet] = []

        n = int(n)

        if (n < 1):
            raise Exception("n must be > 0")

        if not cls._spam_wallets_dir_exists():
            cls._create_spam_wallet_dir()
        
        if not connection.is_online() and not connection.check_connection():
            raise Exception("RPC daemon is offline")

        print(f"[*] Loading {n} spam wallets...")

        for i in range(n):
            wallets.append(cls.load_wallet(i + 1, connection, restore_height))
        
        print(f"[*] Loaded {n} spam wallets")

        return wallets
    