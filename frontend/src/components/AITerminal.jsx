import { Box, Flex, Text, Input, IconButton, VStack, Icon, Spinner } from '@chakra-ui/react'
import { useState, useRef, useEffect } from 'react'
import { FiSend, FiCpu, FiX, FiTerminal } from 'react-icons/fi'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'

const MotionBox = motion.create(Box)

const AITerminal = ({ isOpen, onClose }) => {
    const [messages, setMessages] = useState([
        { role: 'system', content: 'Env AI v1.0 initialized. Connected to system context.' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const messagesEndRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, isOpen])

    const handleSend = async () => {
        if (!input.trim()) return

        const userMsg = { role: 'user', content: input }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setLoading(true)

        try {
            const res = await axios.post('http://localhost:8001/api/ai/chat', {
                message: userMsg.content
            })

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: res.data.response
            }])
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'error',
                content: `Error: ${error.response?.data?.detail || error.message}`
            }])
        } finally {
            setLoading(false)
        }
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <MotionBox
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 20 }}
                    position="fixed"
                    bottom="20px"
                    right="20px"
                    w="400px"
                    h="600px"
                    bg="rgba(10, 10, 10, 0.95)"
                    backdropFilter="blur(10px)"
                    border="1px solid"
                    borderColor="brand.500"
                    borderRadius="lg"
                    boxShadow="0 0 20px rgba(0, 255, 148, 0.1)"
                    zIndex={1000}
                    display="flex"
                    flexDirection="column"
                    overflow="hidden"
                >
                    {/* Header */}
                    <Flex
                        p={3}
                        borderBottom="1px solid"
                        borderColor="dark.border"
                        align="center"
                        bg="rgba(0, 255, 148, 0.05)"
                    >
                        <Icon as={FiCpu} color="brand.500" mr={2} />
                        <Text fontFamily="mono" fontWeight="bold" color="brand.500" fontSize="sm">
                            ENV_AI_ASSISTANT
                        </Text>
                        <IconButton
                            icon={<FiX />}
                            size="xs"
                            variant="ghost"
                            color="dark.muted"
                            ml="auto"
                            onClick={onClose}
                            _hover={{ color: 'white', bg: 'whiteAlpha.200' }}
                        />
                    </Flex>

                    {/* Messages */}
                    <VStack
                        flex={1}
                        overflowY="auto"
                        p={4}
                        spacing={4}
                        align="stretch"
                        css={{
                            '&::-webkit-scrollbar': { width: '4px' },
                            '&::-webkit-scrollbar-track': { background: 'transparent' },
                            '&::-webkit-scrollbar-thumb': { background: '#333', borderRadius: '2px' },
                        }}
                    >
                        {messages.map((msg, i) => (
                            <Box
                                key={i}
                                alignSelf={msg.role === 'user' ? 'flex-end' : 'flex-start'}
                                maxW="85%"
                            >
                                {msg.role !== 'user' && (
                                    <Text fontSize="xs" color="dark.muted" mb={1} fontFamily="mono">
                                        {msg.role === 'system' ? 'SYSTEM' : msg.role === 'error' ? 'ERROR' : 'ENV_AI'}
                                    </Text>
                                )}
                                <Box
                                    bg={msg.role === 'user' ? 'brand.500' : msg.role === 'error' ? 'red.900' : 'whiteAlpha.100'}
                                    color={msg.role === 'user' ? 'black' : msg.role === 'error' ? 'red.200' : 'white'}
                                    px={3}
                                    py={2}
                                    borderRadius="md"
                                    borderTopLeftRadius={msg.role !== 'user' ? 0 : 'md'}
                                    borderTopRightRadius={msg.role === 'user' ? 0 : 'md'}
                                    fontSize="sm"
                                >
                                    <Text whiteSpace="pre-wrap">{msg.content}</Text>
                                </Box>
                            </Box>
                        ))}
                        {loading && (
                            <Flex align="center" color="dark.muted" fontSize="xs" fontFamily="mono">
                                <Spinner size="xs" mr={2} color="brand.500" />
                                PROCESSING_CONTEXT...
                            </Flex>
                        )}
                        <div ref={messagesEndRef} />
                    </VStack>

                    {/* Input */}
                    <Flex p={3} borderTop="1px solid" borderColor="dark.border" bg="black">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask about stats, logs, or dealers..."
                            variant="unstyled"
                            color="white"
                            fontFamily="mono"
                            fontSize="sm"
                            px={2}
                        />
                        <IconButton
                            icon={<FiSend />}
                            size="sm"
                            colorScheme="brand"
                            variant="ghost"
                            onClick={handleSend}
                            isDisabled={!input.trim() || loading}
                        />
                    </Flex>
                </MotionBox>
            )}
        </AnimatePresence>
    )
}

export default AITerminal
