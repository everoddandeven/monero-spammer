from time import sleep
from monero import MoneroWallet, MoneroUtils
from src import MoneroSpammer, InputHandler, StringUtils


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
                    accounts_to_use = InputHandler.get_num_accounts_to_use()
                    subaddresses_to_use = InputHandler.get_num_subaddresses_to_use()
                    tx_spammer.send_to_multiple(accounts_to_use, subaddresses_to_use)
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
                try:
                    tx_spammer.sweep_outputs()
                except Exception as e:
                    print(f"[!] Could not sweep outputs: {e}")
                    input("[>] Press Enter to continue: ")
            elif command == 4:
                StringUtils.print_txs(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 5:
                StringUtils.print_subaddresses(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 6:
                StringUtils.print_wallet_outputs(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 7:
                StringUtils.print_wallet_balances(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 8:
                StringUtils.print_wallet_seeds(wallets)
                input("[>] Press Enter to continue: ")
            elif command == 9:
                level = InputHandler.get_log_level()
                MoneroUtils.set_log_level(level)
                print(f"[*] Monero log level set to {level}")
                input("[>] Press Enter to continue: ")
            elif command == 10:
                print("[*] Quit")
                return
            else:
                print(f"[!] Invalid command provided: {command}")
                sleep(3)
    except KeyboardInterrupt:
        print("\n[*] Quit\n")

if __name__ == '__main__':
    main()

