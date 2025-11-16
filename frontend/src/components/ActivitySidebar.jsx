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
} from '@chakra-ui/react'
import { FaCheckCircle, FaExclamationTriangle, FaInfoCircle, FaSearch } from 'react-icons/fa'
import { activityApi } from '../services/api'

export default function ActivitySidebar() {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchActivities()
    const interval = setInterval(fetchActivities, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchActivities = async () => {
    try {
      const response = await activityApi.getAll()
      setActivities(response.data.slice(0, 20))
    } catch (error) {
      console.error('Error fetching activities:', error)
    } finally {
      setLoading(false)
    }
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

  if (loading) {
    return (
      <Center h="200px">
        <Spinner size="sm" />
      </Center>
    )
  }

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
        <Text fontWeight="bold" fontSize="sm" color="gray.700">
          Real-Time Activity
        </Text>
        <Divider />
        
        {activities.length === 0 ? (
          <Text fontSize="sm" color="gray.500" textAlign="center" py={8}>
            No recent activity
          </Text>
        ) : (
          activities.map((activity) => {
            const { icon: ActivityIcon, color } = getActivityIcon(activity.activity_type)
            return (
              <Box key={activity.id} pb={2} borderBottom="1px" borderColor="gray.100">
                <HStack spacing={2} align="start">
                  <Icon as={ActivityIcon} color={color} mt={0.5} />
                  <VStack align="stretch" spacing={0} flex={1}>
                    <Text fontSize="xs" fontWeight="medium">
                      {activity.dealer_name || 'System'}
                    </Text>
                    <Text fontSize="xs" color="gray.600">
                      {activity.message}
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                      {new Date(activity.created_at).toLocaleTimeString()}
                    </Text>
                  </VStack>
                </HStack>
              </Box>
            )
          })
        )}
      </VStack>
    </Box>
  )
}
