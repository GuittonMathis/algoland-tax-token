/**
 * WalletContext.jsx
 *
 * Provides a React context for Algorand wallet connection using MyAlgoConnect.
 * Exposes `account`, `connect()`, and `disconnect()` to any child component.
 *
 * Usage:
 *   import { WalletProvider } from './WalletContext';
 *   // Wrap your App:
 *   <WalletProvider><App/></WalletProvider>
 *
 *   // In a component:
 *   const { account, connect, disconnect } = useWallet();
 */

import React, { createContext, useContext, useState } from 'react'
import MyAlgoConnect from '@randlabs/myalgo-connect'

// Create the context object
const WalletContext = createContext()

export function WalletProvider({ children }) {
  const [account, setAccount] = useState(null)
  const connector = new MyAlgoConnect()

  // Connect to the wallet and store the first account address
  const connect = async () => {
    try {
      const wallets = await connector.connect()
      setAccount(wallets[0].address)
    } catch (err) {
      console.error('Wallet connection error:', err)
    }
  }

  // Clear the stored account
  const disconnect = () => {
    setAccount(null)
  }

  return (
    <WalletContext.Provider value={{ account, connect, disconnect }}>
      {children}
    </WalletContext.Provider>
  )
}

// Custom hook to use the WalletContext
export function useWallet() {
  return useContext(WalletContext)
}
