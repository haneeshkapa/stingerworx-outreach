import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Box } from '@chakra-ui/react'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Dealers from './pages/Dealers'
import Campaigns from './pages/Campaigns'

function App() {
  return (
    <Router>
      <Box minH="100vh" bg="gray.50">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dealers" element={<Dealers />} />
          <Route path="/campaigns" element={<Campaigns />} />
        </Routes>
      </Box>
    </Router>
  )
}

export default App
