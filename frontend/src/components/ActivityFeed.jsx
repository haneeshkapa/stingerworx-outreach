import { useEffect, useState } from 'react'
import {
  Box,
  VStack,
  Text,
  Badge,
  Spinner,
  Center,
  HStack,
} from '@chakra-ui/react'
import axios from 'axios'
import { format } from 'date-fns'

const ACTIVITY_ICONS = {
  dealer_search: '🔍',
  website_found: '✅',
  contact_extracted: '📧',
  dealer_saved: '💾',
  error: '❌',
  info: 'ℹ️',
}

const ACTIVITY_COLORS = {
  dealer_search: 'blue',
  website_found: 'green',
  contact_extracted: 'purple',
  dealer_saved: 'teal',
  error: 'red',
  info: 'gray',
}

export default function ActivityFeed({ autoRefresh = true, refreshInterval = 2000 }) {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchActivities = async () => {
    try {
      const response = await axios.get('/api/activity')
      setActivities(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching activity:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchActivities()

    if (autoRefresh) {
      const interval = setInterval(fetchActivities, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  if (loading) {
    return (
      <Center p={8}>
        <Spinner color="brand.500" />
      </Center>
    )
  }

  return (
    <Box
      bg="white"
      borderRadius="lg"
      border="1px"
      borderColor="gray.200"
      maxH="600px"
      overflowY="auto"
    >
      <Box p={4} borderBottom="1px" borderColor="gray.200" bg="gray.50">
        <HStack justify="space-between">
          <Text fontWeight="bold" fontSize="lg">
            Live Activity Feed
          </Text>
          <Badge colorScheme="green" fontSize="xs">
            🟢 LIVE
          </Badge>
        </HStack>
      </Box>

      <VStack align="stretch" spacing={0}>
        {activities.length === 0 ? (
          <Center p={8}>
            <Text color="gray.500">No activity yet. Import dealers to see progress.</Text>
          </Center>
        ) : (
          activities.map((activity) => {
            const icon = ACTIVITY_ICONS[activity.activity_type] || 'ℹ️'
            const color = ACTIVITY_COLORS[activity.activity_type] || 'gray'

            return (
              <Box
                key={activity.id}
                p={3}
                borderBottom="1px"
                borderColor="gray.100"
                _hover={{ bg: 'gray.50' }}
                transition="background 0.2s"
              >
                <HStack align="start" spacing={3}>
                  <Text fontSize="lg">
                    {icon}
                  </Text>
                  <Box flex={1}>
                    <Text fontSize="sm" fontWeight="medium">
                      {activity.message}
                    </Text>
                    {activity.dealer_name && (
                      <Text fontSize="xs" color="gray.600" mt={0.5}>
                        {activity.dealer_name}
                      </Text>
                    )}
                    <Text fontSize="xs" color="gray.400" mt={1}>
                      {format(new Date(activity.created_at), 'h:mm:ss a')}
                    </Text>
                  </Box>
                </HStack>
              </Box>
            )
          })
        )}
      </VStack>
    </Box>
  )
}
