import { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Badge,
  useToast
} from '@chakra-ui/react'
import { FiRefreshCw, FiPlay, FiPause } from 'react-icons/fi'
import api from '../services/api'

function Logs() {
  const [logs, setLogs] = useState('')
  const [logInfo, setLogInfo] = useState(null)
  const [isAutoRefresh, setIsAutoRefresh] = useState(true)
  const [loading, setLoading] = useState(false)
  const toast = useToast()

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/logs?lines=1000')
      setLogs(response.data.logs)
      setLogInfo({
        file: response.data.file,
        totalLines: response.data.total_lines,
        showingLines: response.data.showing_lines
      })
    } catch (error) {
      console.error('Failed to fetch logs:', error)
      toast({
        title: 'Error loading logs',
        description: error.message,
        status: 'error',
        duration: 3000,
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()

    if (isAutoRefresh) {
      const interval = setInterval(fetchLogs, 3000)
      return () => clearInterval(interval)
    }
  }, [isAutoRefresh])

  const handleRefresh = () => {
    fetchLogs()
  }

  const toggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh)
  }

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        <HStack justify="space-between">
          <Box>
            <Heading size="lg">Live Workflow Logs</Heading>
            <Text color="gray.600" fontSize="sm" mt={1}>
              Real-time monitoring of backend processes and Crawl4AI activity
            </Text>
          </Box>
          <HStack spacing={3}>
            <Badge colorScheme={isAutoRefresh ? 'green' : 'gray'}>
              {isAutoRefresh ? 'Auto-refreshing' : 'Paused'}
            </Badge>
            <Button
              size="sm"
              leftIcon={isAutoRefresh ? <FiPause /> : <FiPlay />}
              onClick={toggleAutoRefresh}
              variant="outline"
            >
              {isAutoRefresh ? 'Pause' : 'Resume'}
            </Button>
            <Button
              size="sm"
              leftIcon={<FiRefreshCw />}
              onClick={handleRefresh}
              isLoading={loading}
              colorScheme="blue"
            >
              Refresh
            </Button>
          </HStack>
        </HStack>

        {logInfo && (
          <HStack spacing={4} fontSize="sm" color="gray.600">
            <Text>📁 {logInfo.file?.split('/').pop()}</Text>
            <Text>📊 Showing {logInfo.showingLines} of {logInfo.totalLines} lines</Text>
          </HStack>
        )}

        <Box
          bg="gray.900"
          color="green.300"
          p={6}
          borderRadius="lg"
          fontFamily="monospace"
          fontSize="sm"
          overflowX="auto"
          maxH="70vh"
          overflowY="auto"
          boxShadow="lg"
          position="relative"
        >
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {logs || 'Loading logs...'}
          </pre>
          
          {loading && (
            <Box
              position="absolute"
              top={2}
              right={2}
              bg="blue.500"
              color="white"
              px={3}
              py={1}
              borderRadius="md"
              fontSize="xs"
              fontFamily="sans-serif"
            >
              Refreshing...
            </Box>
          )}
        </Box>
      </VStack>
    </Container>
  )
}

export default Logs
