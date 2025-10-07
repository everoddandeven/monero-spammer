from monero import MoneroRpcConnection, MoneroWallet, MoneroUtils
from src import MoneroSpammer

class StringUtils:

    @classmethod
    def is_null_or_empty(cls, string: str | None) -> bool:
        return string is None or string == ''
    
    @classmethod
    def print_header(cls) -> None:
        print("""
███╗   ███╗ ██████╗ ███╗   ██╗███████╗██████╗  ██████╗     ███████╗██████╗  █████╗ ███╗   ███╗███╗   ███╗███████╗██████╗ 
████╗ ████║██╔═══██╗████╗  ██║██╔════╝██╔══██╗██╔═══██╗    ██╔════╝██╔══██╗██╔══██╗████╗ ████║████╗ ████║██╔════╝██╔══██╗
██╔████╔██║██║   ██║██╔██╗ ██║█████╗  ██████╔╝██║   ██║    ███████╗██████╔╝███████║██╔████╔██║██╔████╔██║█████╗  ██████╔╝
██║╚██╔╝██║██║   ██║██║╚██╗██║██╔══╝  ██╔══██╗██║   ██║    ╚════██║██╔═══╝ ██╔══██║██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║╚██████╔╝██║ ╚████║███████╗██║  ██║╚██████╔╝    ███████║██║     ██║  ██║██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗██║  ██║
╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝     ╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝                                                                                            
                                    
                                https://github.com/everoddandeven/monero-spammer
""")

class InputHandler:

    @classmethod
    def get_rpc_connection(cls) -> MoneroRpcConnection:
        uri = input(f"[>] Insert daemon RPC uri: ")
        username = input(f"[>] Insert daemon RPC username: ")
        password = ""
        if not StringUtils.is_null_or_empty(username):
            password = input(f"[>] Insert daemon RPC password: ")
        connection = MoneroRpcConnection(uri, username, password)
        return connection
    
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


def main():
    StringUtils.print_header()

    connection = InputHandler.get_rpc_connection()

    if not connection.check_connection():
        msg = f"[!] Could not connect to daemon RPC at {connection.uri}"
        username = connection.username
        password = connection.password

        if not StringUtils.is_null_or_empty(username) and not StringUtils.is_null_or_empty(password):
            msg = f"{msg} with username and password {username}:{password}"

        print(msg)
        return

    num_wallets = InputHandler.get_num_wallets_to_create()
    amount = MoneroSpammer.AMOUNT

    tx_spammer = MoneroSpammer(connection, num_wallets)

    wallets: list[MoneroWallet] = tx_spammer.get_wallets()

    for wallet in wallets:
        balance = wallet.get_balance(0, 0)
        amount_to_deposit = amount - balance if amount > balance else 0

        if amount_to_deposit == 0:
            continue

        print(f"[*] Send at least {MoneroUtils.atomic_units_to_xmr(amount_to_deposit)} XMR ({amount_to_deposit} moneroj) to {wallet.get_primary_address()}")

    while True:
        command = input("[>] Insert a command (start, exit): ")

        if command == 'start':
            try:
                tx_spammer.start()
            except Exception as e:
                print(f"[!] An error occured: {e}")
                continue
        elif command == 'exit':
            return
        else:
            print("[!] Invalid command provided")


if __name__ == '__main__':
    main()

