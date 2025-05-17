/**
 * src/index.js
 *
 * Entry point of the React application.
 * - Wraps the App component with BrowserRouter for routing.
 * - Provides a WalletProvider context for Algorand wallet access.
 * - Enables StrictMode for highlighting potential issues.
 * - Optionally logs web vitals for performance monitoring.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App'
import reportWebVitals from './reportWebVitals'
import { WalletProvider } from './WalletContext'

// Create root React node and render the application
const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <WalletProvider>
        <App />
      </WalletProvider>
    </BrowserRouter>
  </React.StrictMode>
)

// If you want to measure performance, pass a function to log results
reportWebVitals()
