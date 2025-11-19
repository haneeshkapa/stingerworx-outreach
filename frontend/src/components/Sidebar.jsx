import { Box, VStack, Icon, Text, Flex, Tooltip, Divider, Avatar, Badge, IconButton } from '@chakra-ui/react'
import { NavLink } from 'react-router-dom'
import { FiHome, FiUsers, FiUploadCloud, FiSend, FiActivity, FiMonitor, FiSettings, FiCommand, FiCpu } from 'react-icons/fi'
import { motion } from 'framer-motion'
import { useState } from 'react'
import AITerminal from './AITerminal'

const NavItem = ({ icon, label, to, isCollapsed }) => {
    return (
        <Tooltip label={isCollapsed ? label : ''} placement="right" hasArrow bg="dark.card" color="white">
            <NavLink to={to} style={{ width: '100%' }}>
                {({ isActive }) => (
                    <Flex
                        align="center"
                        p={3}
                        mx={2}
                        borderRadius="md"
                        cursor="pointer"
                        role="group"
                        transition="all 0.2s"
                        bg={isActive ? 'rgba(0, 255, 148, 0.1)' : 'transparent'}
                        color={isActive ? 'brand.500' : 'dark.muted'}
                        _hover={{
                            bg: 'dark.hover',
                            color: 'white',
                        }}
                    >
                        <Icon as={icon} boxSize={5} />
                        {!isCollapsed && (
                            <Text ml={3} fontSize="sm" fontWeight="medium">
                                {label}
                            </Text>
                        )}
                        {isActive && !isCollapsed && (
                            <Box ml="auto" w={1.5} h={1.5} borderRadius="full" bg="brand.500" />
                        )}
                    </Flex>
                )}
            </NavLink>
        </Tooltip>
    )
}

const Sidebar = () => {
    const isCollapsed = false // Could be state-controlled later
    const [isAIOpen, setIsAIOpen] = useState(false)

    return (
        <>
            <Box
                w={isCollapsed ? '80px' : '260px'}
                h="100vh"
                bg="dark.card"
                borderRight="1px"
                borderColor="dark.border"
                py={6}
                display="flex"
                flexDirection="column"
                transition="width 0.2s"
                position="fixed"
                left={0}
                top={0}
                zIndex={100}
            >
                {/* Logo Area */}
                <Flex px={6} mb={8} align="center">
                    <Box
                        w={8} h={8}
                        bgGradient="linear(to-br, brand.500, brand.700)"
                        borderRadius="md"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                    >
                        <Text fontWeight="bold" color="black">S</Text>
                    </Box>
                    {!isCollapsed && (
                        <Box ml={3}>
                            <Text fontWeight="bold" fontSize="md" color="white" letterSpacing="tight">
                                STINGERWORX
                            </Text>
                            <Badge colorScheme="brand" variant="outline" fontSize="xs" mt={0.5}>
                                ADMIN
                            </Badge>
                        </Box>
                    )}
                </Flex>

                {/* Navigation */}
                <VStack spacing={1} align="stretch" flex={1}>
                    <Box px={6} mb={2}>
                        <Text fontSize="xs" fontWeight="bold" color="dark.muted" textTransform="uppercase" letterSpacing="wider">
                            Platform
                        </Text>
                    </Box>
                    <NavItem icon={FiHome} label="Dashboard" to="/" isCollapsed={isCollapsed} />
                    <NavItem icon={FiUsers} label="Dealers" to="/dealers" isCollapsed={isCollapsed} />
                    <NavItem icon={FiSend} label="Campaigns" to="/campaigns" isCollapsed={isCollapsed} />

                    <Box px={6} mt={6} mb={2}>
                        <Text fontSize="xs" fontWeight="bold" color="dark.muted" textTransform="uppercase" letterSpacing="wider">
                            Tools
                        </Text>
                    </Box>
                    <NavItem icon={FiUploadCloud} label="Import Data" to="/dealers/import" isCollapsed={isCollapsed} />
                    <NavItem icon={FiMonitor} label="Browser Stream" to="/browser-stream" isCollapsed={isCollapsed} />
                    <NavItem icon={FiActivity} label="System Logs" to="/logs" isCollapsed={isCollapsed} />

                    <Box px={2} mt={4}>
                        <Flex
                            align="center"
                            p={3}
                            mx={2}
                            borderRadius="md"
                            cursor="pointer"
                            bg={isAIOpen ? 'brand.500' : 'rgba(255,255,255,0.05)'}
                            color={isAIOpen ? 'black' : 'brand.400'}
                            onClick={() => setIsAIOpen(!isAIOpen)}
                            _hover={{ bg: isAIOpen ? 'brand.400' : 'rgba(255,255,255,0.1)' }}
                        >
                            <Icon as={FiCpu} boxSize={5} />
                            {!isCollapsed && (
                                <Text ml={3} fontSize="sm" fontWeight="bold">
                                    Ask Env AI
                                </Text>
                            )}
                        </Flex>
                    </Box>
                </VStack>

                {/* Footer / User */}
                <Box px={4} mt="auto">
                    <Divider borderColor="dark.border" mb={4} />
                    <Flex align="center" p={2} borderRadius="md" _hover={{ bg: 'dark.hover' }} cursor="pointer">
                        <Avatar size="sm" name="Admin User" bg="dark.border" color="white" />
                        {!isCollapsed && (
                            <Box ml={3}>
                                <Text fontSize="sm" fontWeight="medium" color="white">Admin User</Text>
                                <Text fontSize="xs" color="dark.muted">admin@stingerworx.com</Text>
                            </Box>
                        )}
                    </Flex>
                </Box>
            </Box>

            <AITerminal isOpen={isAIOpen} onClose={() => setIsAIOpen(false)} />
        </>
    )
}

export default Sidebar
