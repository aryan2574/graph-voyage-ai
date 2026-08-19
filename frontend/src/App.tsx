import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import TravelPlanner from './pages/TravelPlanner'
import Dashboard from './pages/Dashboard'
import About from './pages/About'
import './styles/App.css'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<TravelPlanner />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Layout>
  )
}

export default App
