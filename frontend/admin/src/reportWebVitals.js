/**
 * reportWebVitals.js
 *
 * Measures and reports key web performance metrics using the web-vitals library.
 * You can pass a callback to log results or send them to an analytics endpoint.
 *
 * Usage:
 *   import reportWebVitals from './reportWebVitals';
 *   reportWebVitals(console.log);
 */

const reportWebVitals = onPerfEntry => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals')
      .then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
        getCLS(onPerfEntry)   // Cumulative Layout Shift
        getFID(onPerfEntry)   // First Input Delay
        getFCP(onPerfEntry)   // First Contentful Paint
        getLCP(onPerfEntry)   // Largest Contentful Paint
        getTTFB(onPerfEntry)  // Time to First Byte
      })
      .catch(err => {
        console.error('Failed to load web-vitals:', err)
      })
  }
}

export default reportWebVitals
