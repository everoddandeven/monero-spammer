from abc import ABC
from secrets import token_hex
from monero import MoneroNetworkType, MoneroTxWallet


class Utils(ABC):
    
    @classmethod
    def get_mining_address(cls, network_type: MoneroNetworkType = MoneroNetworkType.TESTNET) -> str:
        if network_type == MoneroNetworkType.MAINNET:
            return ""
        elif network_type == MoneroNetworkType.TESTNET:
            return "9y1Ye5ZdZQzauBunKyHE3BcheyBFZDAWrheJtDe6UN3HUbPfxcaiHsESXJWyzXFFB3X8gimB9cTx6R3woC4EmCCg2cVhgqK"
        elif network_type == MoneroNetworkType.STAGENET:
            return ""
        
        raise TypeError(f"Invalid argument provided for network_type: {network_type}")

    @classmethod
    def get_tx_sent_amount(cls, tx: MoneroTxWallet) -> int:
        if tx.outgoing_transfer is None:
            return 0

        assert tx.outgoing_transfer.amount is not None
        return tx.outgoing_transfer.amount

    @classmethod
    def get_tx_received_amount(cls, tx: MoneroTxWallet) -> int:
        amount: int = 0

        for transfer in tx.incoming_transfers:
            assert transfer.amount is not None
            amount += transfer.amount

        return amount

    @classmethod
    def get_uuid(cls, length: int = 25) -> str:
        num_bytes = (length + 1) // 2  
        hex_str = token_hex(num_bytes)
        return hex_str[:length]
