import os
from time import sleep
from monero import MoneroRpcConnection, MoneroWallet, MoneroUtils
from src import MoneroSpammer, Utils

class StringUtils:

    @classmethod
    def is_null_or_empty(cls, string: str | None) -> bool:
        return string is None or string == ''
    
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
                print(f"\t[*] hash {tx.hash}, sent: {sent} XMR, received: {received} XMR, confirmations: {tx.num_confirmations}")

    @classmethod
    def print_primary_addresses(cls, wallets: list[MoneroWallet]) -> None:
        i: int = 1
        for wallet in wallets:
            balance = wallet.get_balance(0, 0)
            print(f"[{i}] address {wallet.get_primary_address()}, balance: {MoneroUtils.atomic_units_to_xmr(balance)} XMR")
            i += 1

    @classmethod
    def print_wallet_balances(cls, wallets: list[MoneroWallet]) -> None:
        i: int = 1
        for wallet in wallets:
            balance = wallet.get_balance()
            print(f"[*] spam_wallet_{i} balance: {MoneroUtils.atomic_units_to_xmr(balance)} XMR")
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

class InputHandler:

    @classmethod
    def print_header(cls) -> None:
        cls.clear()
        print("""
███╗   ███╗ ██████╗ ███╗   ██╗███████╗██████╗  ██████╗     ███████╗██████╗  █████╗ ███╗   ███╗███╗   ███╗███████╗██████╗ 
████╗ ████║██╔═══██╗████╗  ██║██╔════╝██╔══██╗██╔═══██╗    ██╔════╝██╔══██╗██╔══██╗████╗ ████║████╗ ████║██╔════╝██╔══██╗
██╔████╔██║██║   ██║██╔██╗ ██║█████╗  ██████╔╝██║   ██║    ███████╗██████╔╝███████║██╔████╔██║██╔████╔██║█████╗  ██████╔╝
██║╚██╔╝██║██║   ██║██║╚██╗██║██╔══╝  ██╔══██╗██║   ██║    ╚════██║██╔═══╝ ██╔══██║██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║╚██████╔╝██║ ╚████║███████╗██║  ██║╚██████╔╝    ███████║██║     ██║  ██║██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗██║  ██║
╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝     ╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝                                                                                            
                                    
                                https://github.com/everoddandeven/monero-spammer
""")

    @classmethod
    def clear(cls) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    @classmethod
    def get_rpc_connection(cls) -> MoneroRpcConnection:
        uri = input(f"[>] Insert daemon RPC uri (default: http://localhost:28081): ")
        if uri == "":
            uri = "http://localhost:28081"
        
        username = input(f"[>] Insert daemon RPC username (empty for none): ")
        password = ""
        if not StringUtils.is_null_or_empty(username):
            password = input(f"[>] Insert daemon RPC password: ")
        connection = MoneroRpcConnection(uri, username, password)
        return connection
    
    @classmethod
    def get_log_level(cls) -> int:
        while True:
            num_str = input("[>] Insert an integer between 0 and 4: ")

            try:
                num = int(num_str)

                if num < 1 or num > 4:
                    raise Exception("Invalid input")
                
                return num
            
            except:
                print(f"[!] Invalid input. Insert an integer between 0 and 4.")
                continue

    @classmethod
    def get_num_wallets_to_create(cls) -> int:
        while True:
            num_str = input("[>] Insert number of wallets to create: ")

            try:
                num = int(num_str)

                if num < 1:
                    raise Exception("Invalid input")
                
                return num
            
            except:
                print(f"[!] Invalid input. Please insert an integer > 1.")
                continue

    @classmethod
    def get_command(cls) -> int:
        msg = """
[1] Send to multiple subaddresses
[2] Send from multiple subaddresses
[3] Show transactions
[4] Show primary addresses
[5] Show wallet balances
[6] Show wallet seeds
[7] Set log level
[8] Quit

[>] Insert command: """

        while True:
            cls.print_header()
            
            try:
                cmd = int(input(msg))

                if cmd < 1 or cmd > 8:
                    raise Exception("")
                
                return cmd
            
            except:
                print("[!] Invalid command provided")
                sleep(3)
                continue

    @classmethod
    def configure_connection(cls) -> MoneroRpcConnection:
        connection = InputHandler.get_rpc_connection()

        if not connection.check_connection():
            msg = f"[!] Could not connect to daemon RPC at {connection.uri}"
            username = connection.username
            password = connection.password

            if not StringUtils.is_null_or_empty(username) and not StringUtils.is_null_or_empty(password):
                msg = f"{msg} with username and password {username}:{password}"

            raise Exception(msg)
        
        return connection


def main():
    try:
        InputHandler.print_header()

        connection = InputHandler.configure_connection()

        num_wallets = InputHandler.get_num_wallets_to_create()

        tx_spammer = MoneroSpammer(connection, num_wallets)

        wallets: list[MoneroWallet] = tx_spammer.get_wallets()

        while True:
            command = InputHandler.get_command()

            if command == 1:
                try:
                    tx_spammer.send_to_multiple()
                except Exception as e:
                    print(f"[!] Could not send txs: {e}")
                    input("[>] Press Enter to continue: ")
            elif command == 2:
                try:
                    tx_spammer.send_from_multiple()
                except Exception as e:
                    print(f"[!] Could not send txs: {e}")
                    input("[>] Press Enter to continue: ")
            elif command == 3:
                StringUtils.print_txs(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 4:
                StringUtils.print_primary_addresses(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 5:
                StringUtils.print_wallet_balances(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 6:
                StringUtils.print_wallet_seeds(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 7:
                level = InputHandler.get_log_level()
                MoneroUtils.set_log_level(level)
                print(f"[*] Monero log level set to {level}")
                input("[>] Press Enter to continue: ")
            elif command == 8:
                print("[*] Quit")
                return
            else:
                print(f"[!] Invalid command provided: {command}")
                sleep(3)
    except KeyboardInterrupt:
        print("\n[*] Quit\n")

if __name__ == '__main__':
    main()

