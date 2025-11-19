import { Box, Grid, Text, Flex, Icon, Badge, SimpleGrid, Card, CardBody } from '@chakra-ui/react'
import { useEffect, useState } from 'react'
import axios from 'axios'
import { FiUsers, FiMessageSquare, FiCheckCircle, FiActivity, FiTarget, FiClock } from 'react-icons/fi'
import { motion } from 'framer-motion'

const StatCard = ({ label, value, icon, trend, color = 'brand.500' }) => (
  <Card bg="dark.card" borderColor="dark.border" borderWidth="1px" borderRadius="lg" overflow="hidden">
    <CardBody p={5}>
      <Flex justify="space-between" align="start">
        <Box>
          <Text fontSize="xs" color="dark.muted" fontWeight="bold" textTransform="uppercase" letterSpacing="wider" mb={1}>
            {label}
          </Text>
          <Text fontSize="3xl" fontWeight="bold" color="white" fontFamily="mono">
            {value}
          </Text>
        </Box>
        <Box p={2} bg={`${color}20`} borderRadius="md" color={color}>
          <Icon as={icon} boxSize={5} />
        </Box>
      </Flex>
      {trend && (
        <Flex align="center" mt={3}>
          <Badge colorScheme="green" variant="solid" fontSize="xs" borderRadius="sm">
            {trend}
          </Badge>
          <Text fontSize="xs" color="dark.muted" ml={2}>vs last week</Text>
        </Flex>
      )}
    </CardBody>
  </Card>
)

const TerminalFeed = ({ logs }) => (
  <Box
    bg="#0D0D0D"
    borderRadius="lg"
    border="1px solid"
    borderColor="dark.border"
    overflow="hidden"
    h="400px"
    display="flex"
    flexDirection="column"
  >
    <Flex bg="dark.card" px={4} py={2} borderBottom="1px" borderColor="dark.border" align="center">
      <Icon as={FiActivity} color="brand.500" mr={2} />
      <Text fontSize="xs" fontFamily="mono" color="dark.muted">LIVE_ACTIVITY_FEED</Text>
      <Flex ml="auto" gap={2}>
        <Box w={2} h={2} borderRadius="full" bg="red.500" />
        <Box w={2} h={2} borderRadius="full" bg="yellow.500" />
        <Box w={2} h={2} borderRadius="full" bg="green.500" />
      </Flex>
    </Flex>
    <Box p={4} overflowY="auto" flex={1} fontFamily="mono" fontSize="xs">
      {logs.map((log, i) => (
        <Flex key={i} mb={2} align="start">
          <Text color="dark.muted" mr={3} minW="140px">
            {new Date(log.created_at).toISOString().split('T')[1].split('.')[0]}
          </Text>
          <Text color={log.activity_type === 'error' ? 'red.400' : 'brand.400'} mr={2}>
            [{log.activity_type.toUpperCase()}]
          </Text>
          <Text color="white">
            {log.message}
          </Text>
        </Flex>
      ))}
      {logs.length === 0 && (
        <Text color="dark.muted">Waiting for system activity...</Text>
      )}
    </Box>
  </Box>
)

const Dashboard = () => {
  const [stats, setStats] = useState(null)
  const [activity, setActivity] = useState([])

  const fetchData = async () => {
    try {
      const [statsRes, activityRes] = await Promise.all([
        axios.get('http://localhost:8001/api/stats'),
        axios.get('http://localhost:8001/api/activity?limit=20')
      ])
      setStats(statsRes.data)
      setActivity(activityRes.data)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  if (!stats) return <Box p={8}><Text color="dark.muted">Loading system metrics...</Text></Box>

  return (
    <Box maxW="1600px" mx="auto">
      <Flex mb={8} justify="space-between" align="center">
        <Box>
          <Text fontSize="2xl" fontWeight="bold" color="white" letterSpacing="tight">
            System Overview
          </Text>
          <Text color="dark.muted" fontSize="sm">
            Real-time metrics and outreach performance
          </Text>
        </Box>
        <Badge colorScheme="brand" variant="outline" px={3} py={1}>
          LIVE
        </Badge>
      </Flex>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <StatCard
          label="Total Dealers"
          value={stats.total_dealers}
          icon={FiUsers}
          color="#0070F3"
        />
        <StatCard
          label="Class 3 Verified"
          value={stats.class3_verified}
          icon={FiCheckCircle}
          color="#7928CA"
        />
        <StatCard
          label="Outreach Sent"
          value={stats.contacted_dealers}
          icon={FiMessageSquare}
          color="#F5A623"
        />
        <StatCard
          label="Interested Leads"
          value={stats.interested_leads}
          icon={FiTarget}
          color="#00FF94"
        />
      </SimpleGrid>

      <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap={6}>
        <TerminalFeed logs={activity} />

        <Card bg="dark.card" borderColor="dark.border" borderWidth="1px" borderRadius="lg">
          <CardBody>
            <Flex align="center" mb={6}>
              <Icon as={FiClock} color="brand.500" mr={2} />
              <Text fontSize="sm" fontWeight="bold" color="white">PENDING ACTIONS</Text>
            </Flex>

            <Flex justify="space-between" align="center" mb={4} p={3} bg="rgba(255,255,255,0.03)" borderRadius="md">
              <Box>
                <Text color="white" fontSize="sm" fontWeight="medium">Approval Queue</Text>
                <Text color="dark.muted" fontSize="xs">Messages waiting for review</Text>
              </Box>
              <Badge colorScheme="yellow" fontSize="md" px={2}>
                {stats.pending_approvals}
              </Badge>
            </Flex>

            <Flex justify="space-between" align="center" mb={4} p={3} bg="rgba(255,255,255,0.03)" borderRadius="md">
              <Box>
                <Text color="white" fontSize="sm" fontWeight="medium">Enrichment Queue</Text>
                <Text color="dark.muted" fontSize="xs">Dealers waiting for AI scan</Text>
              </Box>
              <Badge colorScheme="blue" fontSize="md" px={2}>
                {stats.discovered_count}
              </Badge>
            </Flex>
          </CardBody>
        </Card>
      </Grid>
    </Box>
  )
}

export default Dashboard
