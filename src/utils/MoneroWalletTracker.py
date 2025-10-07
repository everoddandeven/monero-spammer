from time import sleep

from monero import MoneroDaemon, MoneroWallet, MoneroTxQuery
from .Utils import Utils
from .NotEnoughBalanceException import NotEnoughBalanceException


class MoneroWalletTracker:

  _clearedWallets: set[MoneroWallet]

  def __init__(self) -> None:
    self._clearedWallets = set()

  def reset(self) -> None:
    self._clearedWallets.clear()

  def wait_for_wallet_txs_to_clear_pool(self, daemon: MoneroDaemon, sync_period_ms: int, wallets: list[MoneroWallet]) -> None:
    # get wallet tx hashes
    tx_hashes_wallet: set[str] = set()
    tx_query = MoneroTxQuery()
    tx_query.is_confirmed = False

    for wallet in wallets:
      if wallet not in self._clearedWallets:
        wallet.sync()
        print(f"[*] Getting {wallet.get_path()} txs...")
        txs = wallet.get_txs(tx_query)
        print(f"[*] Got {len(txs)} tx(s) from {wallet.get_path()}")
        for tx in txs:
          assert tx.hash is not None
          tx_hashes_wallet.add(tx.hash)
    
    # loop until all wallet txs clear from pool
    is_first: bool = True
    mining_started: bool = False
    num_tx_hashes = len(tx_hashes_wallet)
    while num_tx_hashes > 0:

      # get hashes of relayed, non-failed txs in the pool
      txHashesPool: set[str] = set()
      print(f"[*] Getting tx pool...")
      tx_pool = daemon.get_tx_pool()
      print(f"[*] Found {len(tx_pool)} in pool")
      for tx in tx_pool:
        
        assert tx.hash is not None
        if not tx.is_relayed:
          continue
        elif tx.is_failed:
          daemon.flush_tx_pool(tx.hash)  # flush tx if failed
        else:
          txHashesPool.add(tx.hash)
      
      # get hashes to wait for as intersection of wallet and pool txs
      txHashesPool = txHashesPool.intersection(tx_hashes_wallet)
      
      # break if no txs to wait for
      if len(txHashesPool) == 0:
        break

      # if first time waiting, log message and start mining
      if is_first:
        is_first = False
        print("[*] Waiting for wallet txs to clear from the pool in order to fully sync and avoid double spend attempts (known issue)")
        info = daemon.get_info()
        restricted = info.is_restricted
        if not restricted and not daemon.get_mining_status().is_active:
          try:
            print("[*] Starting mining...")
            daemon.start_mining(Utils.get_mining_address(), 1, False, False)
            print("[*] Mining started")
            mining_started = True
          except: # no problem
            pass
      
      # sleep for a moment
      sleep(sync_period_ms)
    
    # stop mining if started mining
    if (mining_started): 
      print("[*] Stopping mining...")
      daemon.stop_mining()
      print("[*] Mining stopped")

    # sync wallets with the pool
    for wallet in wallets:
      wallet.sync()
      self._clearedWallets.add(wallet)

  def wait_for_unlocked_balances(self, daemon: MoneroDaemon, sync_period_ms: int, wallets: list[MoneroWallet], accountIndex: int, subaddress_index: int | None = None, minAmount: int | None = None):
    for wallet in wallets:
      self.wait_for_unlocked_balance(daemon, sync_period_ms, wallet, accountIndex, subaddress_index, minAmount)

  def wait_for_unlocked_balance(self, daemon: MoneroDaemon, sync_period_ms: int, wallet: MoneroWallet, accountIndex: int, subaddress_index: int | None = None, minAmount: int | None = None):
    if minAmount is None:
      minAmount = 0
    
    # check if wallet has balance
    if (subaddress_index is not None and wallet.get_balance(accountIndex, subaddress_index) < minAmount):
      raise NotEnoughBalanceException(wallet)
    elif subaddress_index is None and wallet.get_balance(accountIndex) < minAmount:
      raise NotEnoughBalanceException(wallet)
    
    # check if wallet has unlocked balance
    if subaddress_index is not None:
      unlocked_balance = wallet.get_unlocked_balance(accountIndex, subaddress_index)
    else:
      unlocked_balance = wallet.get_unlocked_balance(accountIndex)

    if (unlocked_balance > minAmount):
      return unlocked_balance
   
    # start mining
    mining_started: bool = False
    info = daemon.get_info()
    restricted = info.is_restricted
    if not restricted and not daemon.get_mining_status().is_active:
      try:
        print("[*] Starting mining...")
        daemon.start_mining(Utils.get_mining_address(), 1, False, False)
        print("[*] Mining started")
        mining_started = True
      except:
        pass # it's all ok my friend ...
    
    # wait for unlocked balance // TODO: promote to MoneroWallet interface?
    print("[*] Waiting for unlocked balance...")
    
    while (unlocked_balance < minAmount):
      if subaddress_index is not None:
        unlocked_balance = wallet.get_unlocked_balance(accountIndex, subaddress_index)
      else:
        unlocked_balance = wallet.get_unlocked_balance(accountIndex)
        
      try: 
        sleep(sync_period_ms)
      except:
        pass

    print(f"[*] Unlocked balance {unlocked_balance}")

    # stop mining if started
    if (mining_started):
      print("[*] Stopping mining")
      daemon.stop_mining()
      print("[*] Mining stopped")
    
    return unlocked_balance
