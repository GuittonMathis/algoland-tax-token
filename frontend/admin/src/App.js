/**
 * AdminPage component
 *
 * Shows the current treasury balance and lets you distribute Dumbly tokens
 * either manually (custom amounts) or automatically (equal split).
 *
 * Calls:
 *   GET  /treasury-balance
 *   POST /distribute-manual  { burn, lp, rewards }
 *   POST /distribute-all
 *
 * Dependencies:
 *   axios, React (useState, useEffect)
 */

import { useEffect, useState } from 'react'
import axios from 'axios'
import './App.css'

export default function AdminPage() {
  // Store input values as strings to allow empty fields
  const [manual, setManual] = useState({ burn: '', lp: '', rewards: '' })
  const [balance, setBalance] = useState(null)
  const [error, setError]     = useState(null)
  const [status, setStatus]   = useState(null)
  const [loadingManual, setLoadingManual] = useState(false)
  const [loadingAuto, setLoadingAuto]     = useState(false)

  // Fetch treasury balance when component mounts
  useEffect(() => {
    axios.get('/treasury-balance')
      .then(resp => setBalance(resp.data.treasury_balance))
      .catch(err => setError(err.response?.data?.detail || err.message))
  }, [])

  // Convert input string to integer (or 0 if invalid)
  const toAmt = str => {
    const n = parseInt(str, 10)
    return isNaN(n) ? 0 : n
  }

  // Handle manual distribution
  const handleManual = async () => {
    setStatus(null)
    setError(null)
    setLoadingManual(true)

    const payload = {
      burn:    toAmt(manual.burn),
      lp:      toAmt(manual.lp),
      rewards: toAmt(manual.rewards),
    }

    try {
      await axios.post('/distribute-manual', payload)
      setStatus({ type: 'success', text: 'Distribution réussie !' })

      // Update balance
      const balResp = await axios.get('/treasury-balance')
      setBalance(balResp.data.treasury_balance)

      // Reset inputs
      setManual({ burn: '', lp: '', rewards: '' })
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoadingManual(false)
    }
  }

  // Handle automatic distribution (1/3 split)
  const handleAuto = async () => {
    setStatus(null)
    setError(null)
    setLoadingAuto(true)

    try {
      await axios.post('/distribute-all')
      setStatus({ type: 'success', text: 'Distribution automatique réussie !' })
      const balResp = await axios.get('/treasury-balance')
      setBalance(balResp.data.treasury_balance)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoadingAuto(false)
    }
  }

  return (
    <div className="card">
      <h1>Admin Dashboard</h1>

      {/* Error or success messages */}
      {error  && <p className="status error">Erreur : {error}</p>}
      {status && <p className={`status ${status.type}`}>{status.text}</p>}

      {/* Display balance or loading indicator */}
      {balance === null
        ? <p style={{ color: '#F0F0F0', textAlign: 'center' }}>Chargement…</p>
        : <p style={{ color: '#F0F0F0', fontWeight: '600' }}>
            Solde treasury : {balance} Dumbly
          </p>
      }

      <hr />

      {/* Manual distribution form */}
      <h2>Distribution manuelle</h2>
      <div>
        <label>Burn :</label>
        <input
          type="number"
          value={manual.burn}
          onChange={e => setManual({ ...manual, burn: e.target.value })}
          placeholder="0"
        />
      </div>
      <div>
        <label>LP :</label>
        <input
          type="number"
          value={manual.lp}
          onChange={e => setManual({ ...manual, lp: e.target.value })}
          placeholder="0"
        />
      </div>
      <div>
        <label>Rewards :</label>
        <input
          type="number"
          value={manual.rewards}
          onChange={e => setManual({ ...manual, rewards: e.target.value })}
          placeholder="0"
        />
      </div>
      <button
        className="btn"
        onClick={handleManual}
        disabled={loadingManual || balance === null}
      >
        {loadingManual ? 'En cours…' : 'Distribuer'}
      </button>

      <hr />

      {/* Automatic distribution button */}
      <h2>Distribution automatique (split 1/3)</h2>
      <button
        className="btn"
        onClick={handleAuto}
        disabled={loadingAuto || balance === null}
      >
        {loadingAuto ? 'En cours…' : 'Distribuer tout'}
      </button>
    </div>
  )
}
