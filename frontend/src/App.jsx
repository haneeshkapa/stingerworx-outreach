import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@chakra-ui/react'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import DealerPipeline from './pages/DealerPipeline'
import ImportDealers from './pages/ImportDealers'
import Campaigns from './pages/Campaigns'

function App() {
  return (
    <Router>
      <Box minH="100vh" bg="gray.50">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dealers" element={<DealerPipeline />} />
          <Route path="/dealers/import" element={<ImportDealers />} />
          <Route path="/campaigns" element={<Campaigns />} />
        </Routes>
      </Box>
    </Router>
  )
}

export default App
