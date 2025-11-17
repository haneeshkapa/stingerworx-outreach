import { useEffect, useState } from 'react'
import {
  Box,
  VStack,
  Text,
  Badge,
  Divider,
  Spinner,
  Center,
  HStack,
  Icon,
  Collapse,
  Button,
} from '@chakra-ui/react'
import { FaCheckCircle, FaExclamationTriangle, FaInfoCircle, FaSearch, FaChevronDown, FaChevronRight } from 'react-icons/fa'
import { activityApi } from '../services/api'

export default function ActivitySidebar() {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedDealers, setExpandedDealers] = useState({})

  useEffect(() => {
    fetchActivities()
    const interval = setInterval(fetchActivities, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchActivities = async () => {
    try {
      const response = await activityApi.getAll()
      const filteredActivities = filterIrrelevantActivities(response.data)
      setActivities(filteredActivities.slice(0, 50))
    } catch (error) {
      console.error('Error fetching activities:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterIrrelevantActivities = (activities) => {
    const irrelevantPatterns = [
      'wikipedia.org',
      'disambiguation',
      '/wiki/',
      'youtube.com',
      'facebook.com',
      'twitter.com',
      'yelp.com',
      'yellowpages.com'
    ]

    return activities.filter(activity => {
      const message = activity.message?.toLowerCase() || ''
      return !irrelevantPatterns.some(pattern => message.includes(pattern))
    })
  }

  const toggleDealer = (dealerName) => {
    setExpandedDealers(prev => ({
      ...prev,
      [dealerName]: !prev[dealerName]
    }))
  }

  const getActivityIcon = (type) => {
    switch (type) {
      case 'DEALER_SAVED':
        return { icon: FaCheckCircle, color: 'green.500' }
      case 'WEBSITE_FOUND':
        return { icon: FaCheckCircle, color: 'blue.500' }
      case 'DEALER_SEARCH':
        return { icon: FaSearch, color: 'purple.500' }
      case 'ERROR':
        return { icon: FaExclamationTriangle, color: 'red.500' }
      default:
        return { icon: FaInfoCircle, color: 'gray.500' }
    }
  }

  const groupActivitiesByDealer = () => {
    const grouped = {}
    activities.forEach(activity => {
      const dealerName = activity.dealer_name || 'System'
      if (!grouped[dealerName]) {
        grouped[dealerName] = []
      }
      grouped[dealerName].push(activity)
    })
    return grouped
  }

  if (loading) {
    return (
      <Center h="200px">
        <Spinner size="sm" />
      </Center>
    )
  }

  const groupedActivities = groupActivitiesByDealer()
  const dealerNames = Object.keys(groupedActivities).sort((a, b) => {
    const latestA = Math.max(...groupedActivities[a].map(act => new Date(act.created_at).getTime()))
    const latestB = Math.max(...groupedActivities[b].map(act => new Date(act.created_at).getTime()))
    return latestB - latestA
  })

  return (
    <Box
      position="sticky"
      top="20px"
      h="calc(100vh - 120px)"
      overflowY="auto"
      bg="white"
      borderRadius="lg"
      shadow="sm"
      p={4}
    >
      <VStack align="stretch" spacing={3}>
        <HStack justify="space-between">
          <Text fontWeight="bold" fontSize="sm" color="gray.700">
            Real-Time Activity
          </Text>
          <Badge colorScheme="gray" fontSize="xs">
            {activities.length}
          </Badge>
        </HStack>
        <Divider />
        
        {activities.length === 0 ? (
          <Text fontSize="sm" color="gray.500" textAlign="center" py={8}>
            No recent activity
          </Text>
        ) : (
          <VStack align="stretch" spacing={2}>
            {dealerNames.slice(0, 15).map((dealerName) => {
              const dealerActivities = groupedActivities[dealerName]
              const isExpanded = expandedDealers[dealerName] !== false
              const latestActivity = dealerActivities[0]
              const { icon: ActivityIcon, color } = getActivityIcon(latestActivity.activity_type)

              return (
                <Box
                  key={dealerName}
                  borderRadius="md"
                  border="1px"
                  borderColor="gray.200"
                  overflow="hidden"
                >
                  <Button
                    variant="ghost"
                    w="100%"
                    h="auto"
                    p={2}
                    justifyContent="start"
                    onClick={() => toggleDealer(dealerName)}
                    _hover={{ bg: 'gray.50' }}
                  >
                    <HStack spacing={2} w="100%" align="start">
                      <Icon
                        as={isExpanded ? FaChevronDown : FaChevronRight}
                        boxSize={3}
                        color="gray.400"
                        mt={0.5}
                      />
                      <Icon as={ActivityIcon} color={color} boxSize={3} mt={0.5} />
                      <VStack align="start" spacing={0} flex={1}>
                        <Text fontSize="xs" fontWeight="bold" textAlign="left">
                          {dealerName}
                        </Text>
                        <HStack spacing={2}>
                          <Badge colorScheme="gray" fontSize="xs">
                            {dealerActivities.length} events
                          </Badge>
                          <Text fontSize="xs" color="gray.400">
                            {new Date(latestActivity.created_at).toLocaleTimeString()}
                          </Text>
                        </HStack>
                      </VStack>
                    </HStack>
                  </Button>

                  <Collapse in={isExpanded}>
                    <VStack align="stretch" spacing={1} p={2} pt={0} bg="gray.50">
                      {dealerActivities.map((activity, idx) => {
                        const { icon: ActivityIcon, color } = getActivityIcon(activity.activity_type)
                        return (
                          <HStack
                            key={activity.id}
                            spacing={2}
                            p={2}
                            bg="white"
                            borderRadius="sm"
                            align="start"
                          >
                            <Icon as={ActivityIcon} color={color} boxSize={3} mt={0.5} />
                            <VStack align="stretch" spacing={0} flex={1}>
                              <Text fontSize="xs" color="gray.700" noOfLines={3}>
                                {activity.message}
                              </Text>
                              <Text fontSize="xs" color="gray.400">
                                {new Date(activity.created_at).toLocaleTimeString()}
                              </Text>
                            </VStack>
                          </HStack>
                        )
                      })}
                    </VStack>
                  </Collapse>
                </Box>
              )
            })}
          </VStack>
        )}
      </VStack>
    </Box>
  )
}
