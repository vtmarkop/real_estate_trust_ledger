import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css' // ΠΡΕΠΕΙ ΝΑ ΥΠΑΡΧΕΙ ΑΥΤΗ Η ΓΡΑΜΜΗ

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)