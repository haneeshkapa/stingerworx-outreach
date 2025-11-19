import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@chakra-ui/react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import DealerPipeline from './pages/DealerPipeline'
import ImportDealers from './pages/ImportDealers'
import Campaigns from './pages/Campaigns'
import Logs from './pages/Logs'
import BrowserStream from './pages/BrowserStream'

function App() {
  return (
    <Router>
      <Box minH="100vh" bg="dark.bg">
        <Sidebar />
        <Box ml="260px" p={8} transition="margin 0.2s">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dealers" element={<DealerPipeline />} />
            <Route path="/dealers/import" element={<ImportDealers />} />
            <Route path="/campaigns" element={<Campaigns />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/browser-stream" element={<BrowserStream />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  )
}

export default App
