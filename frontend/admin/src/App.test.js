/**
 * App.test.js
 *
 * Basic smoke test for the main App (AdminPage) component.
 * Verifies that the "Admin Dashboard" heading is present.
 */

import { render, screen } from '@testing-library/react'
import App from './App'

test('renders Admin Dashboard heading', () => {
  render(<App />)
  // Look for the main dashboard title
  const heading = screen.getByText(/Admin Dashboard/i)
  expect(heading).toBeInTheDocument()
})
