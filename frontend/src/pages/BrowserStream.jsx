import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Input,
  Badge,
  useToast,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription
} from '@chakra-ui/react'
import { FiPlay, FiPause, FiSearch, FiX } from 'react-icons/fi'
import api from '../services/api'

function BrowserStream() {
  const [sessionId, setSessionId] = useState(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [connectionState, setConnectionState] = useState('new')
  
  const videoRef = useRef(null)
  const peerConnectionRef = useRef(null)
  const toast = useToast()

  const startStream = async () => {
    try {
      setIsStreaming(true)
      toast({
        title: 'Starting browser stream...',
        status: 'info',
        duration: 2000,
      })

      // Create RTCPeerConnection
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' }
        ]
      })

      peerConnectionRef.current = pc

      // Debug ICE connection
      pc.oniceconnectionstatechange = () => {
        console.log('❄️ ICE connection state:', pc.iceConnectionState)
      }

      pc.onicegatheringstatechange = () => {
        console.log('📡 ICE gathering state:', pc.iceGatheringState)
      }

      pc.onicecandidate = (event) => {
        if (event.candidate) {
          console.log('🧊 ICE candidate:', event.candidate.type, event.candidate.candidate)
        } else {
          console.log('✅ ICE gathering complete')
        }
      }

      // Handle connection state changes
      pc.onconnectionstatechange = () => {
        console.log('🔌 Connection state:', pc.connectionState)
        setConnectionState(pc.connectionState)
        
        if (pc.connectionState === 'connected') {
          toast({
            title: '✅ Stream connected!',
            description: 'Browser automation is now live',
            status: 'success',
            duration: 3000,
          })
        } else if (pc.connectionState === 'failed') {
          toast({
            title: 'Connection failed',
            description: 'Please try again',
            status: 'error',
            duration: 5000,
          })
        }
      }

      // Handle incoming video track
      pc.ontrack = (event) => {
        console.log('Received video track')
        if (videoRef.current) {
          videoRef.current.srcObject = event.streams[0]
        }
      }

      // CRITICAL: Add transceiver to receive video (fixes aiortc "None is not in list" error)
      pc.addTransceiver('video', { direction: 'recvonly' })

      // Create offer
      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)

      // Wait for ICE gathering to complete
      await new Promise((resolve) => {
        if (pc.iceGatheringState === 'complete') {
          resolve()
        } else {
          const checkState = () => {
            if (pc.iceGatheringState === 'complete') {
              pc.removeEventListener('icegatheringstatechange', checkState)
              resolve()
            }
          }
          pc.addEventListener('icegatheringstatechange', checkState)
        }
      })

      // Send offer to server
      const response = await api.post('/api/webrtc/offer', {
        sdp: pc.localDescription.sdp,
        type: pc.localDescription.type
      })

      // Set remote description (answer from server)
      await pc.setRemoteDescription(new RTCSessionDescription({
        sdp: response.data.sdp,
        type: response.data.type
      }))

      setSessionId(response.data.session_id)
      
    } catch (error) {
      console.error('Stream error:', error)
      toast({
        title: 'Stream error',
        description: error.message,
        status: 'error',
        duration: 5000,
      })
      setIsStreaming(false)
    }
  }

  const stopStream = async () => {
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close()
      peerConnectionRef.current = null
    }

    if (sessionId) {
      try {
        await api.delete(`/api/webrtc/session/${sessionId}`)
      } catch (error) {
        console.error('Error closing session:', error)
      }
    }

    setIsStreaming(false)
    setSessionId(null)
    setConnectionState('new')

    toast({
      title: 'Stream stopped',
      status: 'info',
      duration: 2000,
    })
  }

  const handleSearch = async () => {
    if (!sessionId || !searchQuery) return

    try {
      await api.post(`/api/webrtc/search/${sessionId}`, { query: searchQuery })
      toast({
        title: '🔍 Searching...',
        description: `Looking for "${searchQuery}"`,
        status: 'info',
        duration: 2000,
      })
    } catch (error) {
      toast({
        title: 'Search error',
        description: error.message,
        status: 'error',
        duration: 3000,
      })
    }
  }

  useEffect(() => {
    return () => {
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close()
      }
    }
  }, [])

  const getConnectionColor = () => {
    switch (connectionState) {
      case 'connected': return 'green'
      case 'connecting': return 'yellow'
      case 'failed': return 'red'
      case 'closed': return 'gray'
      default: return 'gray'
    }
  }

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg">Live Browser Streaming (WebRTC)</Heading>
          <Text color="gray.600" fontSize="sm" mt={1}>
            Watch browser automation in real-time via WebRTC video stream
          </Text>
        </Box>

        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <Box flex="1">
            <AlertTitle>Real-Time Browser Automation</AlertTitle>
            <AlertDescription>
              Click "Start Stream" to launch a live browser session. You can search Google and watch the browser navigate in real-time!
            </AlertDescription>
          </Box>
        </Alert>

        <HStack spacing={4}>
          {!isStreaming ? (
            <Button
              colorScheme="green"
              leftIcon={<FiPlay />}
              onClick={startStream}
              size="lg"
            >
              Start Stream
            </Button>
          ) : (
            <Button
              colorScheme="red"
              leftIcon={<FiX />}
              onClick={stopStream}
              size="lg"
            >
              Stop Stream
            </Button>
          )}

          <Badge colorScheme={getConnectionColor()} fontSize="md" p={2}>
            {connectionState.toUpperCase()}
          </Badge>

          {sessionId && (
            <Text fontSize="sm" color="gray.500">
              Session: {sessionId.substring(0, 8)}...
            </Text>
          )}
        </HStack>

        {isStreaming && (
          <HStack>
            <Input
              placeholder="Enter search query..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button
              colorScheme="blue"
              leftIcon={<FiSearch />}
              onClick={handleSearch}
              isDisabled={!sessionId}
            >
              Search
            </Button>
          </HStack>
        )}

        <Box
          bg="black"
          borderRadius="lg"
          overflow="hidden"
          boxShadow="2xl"
          position="relative"
          minH="500px"
        >
          <video
            ref={videoRef}
            autoPlay
            playsInline
            style={{
              width: '100%',
              height: 'auto',
              display: 'block'
            }}
          />
          {!isStreaming && (
            <Box
              position="absolute"
              top="50%"
              left="50%"
              transform="translate(-50%, -50%)"
              textAlign="center"
              color="white"
            >
              <Text fontSize="xl" fontWeight="bold">
                Click "Start Stream" to begin
              </Text>
              <Text fontSize="sm" mt={2} color="gray.400">
                Live browser automation powered by WebRTC
              </Text>
            </Box>
          )}
        </Box>

        <Alert status="success" borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>How it works:</AlertTitle>
            <AlertDescription>
              • WebRTC streams browser viewport at 10 FPS<br />
              • Use search box to navigate Google in real-time<br />
              • Watch Playwright automation happen live!
            </AlertDescription>
          </Box>
        </Alert>
      </VStack>
    </Container>
  )
}

export default BrowserStream
