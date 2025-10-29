import os

from time import sleep
from monero import MoneroRpcConnection
from .StringUtils import StringUtils


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
    def wait_for_enter(cls) -> None:
        input("Press Enter to continue: ")

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
    def select_output(cls, num_outputs: int) -> int:
        while True:
            num_str = input(f"[>] Select an output (index 1-{num_outputs}): ")

            try:
                num = int(num_str)

                if num < 1 or num > num_outputs:
                    raise Exception("Invalid input")
                
                return num
            
            except:
                print(f"[!] Invalid input. Please insert an integer > 1.")
                continue

    @classmethod
    def get_num_accounts_to_use(cls) -> int:
        while True:
            num_str = input("[>] Insert number of accounts to send to: ")

            try:
                num = int(num_str)

                if num < 1:
                    raise Exception("Invalid input")
                
                return num
            
            except:
                print(f"[!] Invalid input. Please insert an integer > 1.")
                continue

    @classmethod
    def get_num_subaddresses_to_use(cls) -> int:
        while True:
            num_str = input("[>] Insert number of subaddresses to send to for each account: ")

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
[3] Sweep outputs
[4] Show transactions
[5] Show addresses
[6] Show unspent outputs
[7] Show wallet balances
[8] Show wallet seeds
[9] Set log level
[10] Quit

[>] Insert command: """

        while True:
            cls.print_header()
            
            try:
                cmd = int(input(msg))

                if cmd < 1 or cmd > 10:
                    raise Exception(f"{cmd}")
                
                return cmd
            
            except Exception as e:
                print(f"[!] Invalid command provided: {e}")
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
