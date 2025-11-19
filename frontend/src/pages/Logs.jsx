import { Box, Text, Flex, Icon, Badge, Code, IconButton, Tooltip } from '@chakra-ui/react'
import { useEffect, useState, useRef } from 'react'
import axios from 'axios'
import { FiTerminal, FiPause, FiPlay, FiTrash2, FiDownload, FiMaximize2 } from 'react-icons/fi'

const LogLine = ({ line, index }) => {
  // Basic syntax highlighting
  let color = 'gray.300'
  if (line.includes('ERROR') || line.includes('CRITICAL')) color = 'red.400'
  if (line.includes('WARNING')) color = 'yellow.400'
  if (line.includes('INFO')) color = 'blue.300'
  if (line.includes('SUCCESS') || line.includes('Completed')) color = 'green.400'

  const timestamp = line.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)
  const content = timestamp ? line.replace(timestamp[0], '').trim() : line

  return (
    <Flex fontFamily="mono" fontSize="sm" lineHeight="1.6" _hover={{ bg: 'rgba(255,255,255,0.05)' }} px={2}>
      <Text color="dark.muted" minW="40px" userSelect="none" textAlign="right" mr={4} fontSize="xs">
        {index + 1}
      </Text>
      {timestamp && (
        <Text color="dark.muted" mr={3} minW="150px" fontSize="xs">
          {timestamp[0]}
        </Text>
      )}
      <Text color={color} whiteSpace="pre-wrap" wordBreak="break-all">
        {content}
      </Text>
    </Flex>
  )
}

const Logs = () => {
  const [logs, setLogs] = useState('')
  const [isPaused, setIsPaused] = useState(false)
  const bottomRef = useRef(null)
  const containerRef = useRef(null)

  const fetchLogs = async () => {
    if (isPaused) return
    try {
      const res = await axios.get('http://localhost:8001/api/logs?lines=1000')
      if (res.data.logs) {
        setLogs(res.data.logs)
      }
    } catch (error) {
      console.error('Error fetching logs:', error)
    }
  }

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 2000)
    return () => clearInterval(interval)
  }, [isPaused])

  useEffect(() => {
    if (!isPaused && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, isPaused])

  const handleDownload = () => {
    const blob = new Blob([logs], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `system-logs-${new Date().toISOString()}.log`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const logLines = logs.split('\n').filter(line => line.trim())

  return (
    <Box h="calc(100vh - 100px)" maxW="1600px" mx="auto" display="flex" flexDirection="column">
      <Flex mb={4} justify="space-between" align="center">
        <Box>
          <Text fontSize="2xl" fontWeight="bold" color="white" letterSpacing="tight">
            System Logs
          </Text>
          <Text color="dark.muted" fontSize="sm">
            Live backend process output
          </Text>
        </Box>
        <Flex gap={2}>
          <Tooltip label={isPaused ? "Resume Auto-scroll" : "Pause Auto-scroll"}>
            <IconButton
              icon={isPaused ? <FiPlay /> : <FiPause />}
              onClick={() => setIsPaused(!isPaused)}
              variant="ghost"
              colorScheme={isPaused ? "yellow" : "gray"}
            />
          </Tooltip>
          <Tooltip label="Download Logs">
            <IconButton icon={<FiDownload />} onClick={handleDownload} variant="ghost" />
          </Tooltip>
          <Tooltip label="Clear View (Local)">
            <IconButton icon={<FiTrash2 />} onClick={() => setLogs('')} variant="ghost" colorScheme="red" />
          </Tooltip>
        </Flex>
      </Flex>

      <Box
        flex={1}
        bg="#0D0D0D"
        borderRadius="lg"
        border="1px solid"
        borderColor="dark.border"
        overflow="hidden"
        display="flex"
        flexDirection="column"
        boxShadow="2xl"
      >
        {/* Terminal Header */}
        <Flex bg="dark.card" px={4} py={2} borderBottom="1px" borderColor="dark.border" align="center">
          <Icon as={FiTerminal} color="brand.500" mr={2} />
          <Text fontSize="xs" fontFamily="mono" color="dark.muted">root@stingerworx-backend:~/logs</Text>
          <Flex ml="auto" gap={2}>
            <Box w={2} h={2} borderRadius="full" bg="red.500" />
            <Box w={2} h={2} borderRadius="full" bg="yellow.500" />
            <Box w={2} h={2} borderRadius="full" bg="green.500" />
          </Flex>
        </Flex>

        {/* Terminal Content */}
        <Box
          ref={containerRef}
          p={4}
          overflowY="auto"
          flex={1}
          fontFamily="mono"
          css={{
            '&::-webkit-scrollbar': { width: '8px' },
            '&::-webkit-scrollbar-track': { background: '#0D0D0D' },
            '&::-webkit-scrollbar-thumb': { background: '#333', borderRadius: '4px' },
          }}
        >
          {logLines.map((line, i) => (
            <LogLine key={i} line={line} index={i} />
          ))}
          <div ref={bottomRef} />

          {logLines.length === 0 && (
            <Text color="dark.muted" textAlign="center" mt={10}>
              Waiting for log stream...
            </Text>
          )}
        </Box>
      </Box>
    </Box>
  )
}

export default Logs
