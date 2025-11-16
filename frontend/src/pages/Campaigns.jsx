import { useEffect, useState } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  HStack,
  VStack,
  Card,
  CardBody,
  Badge,
  Center,
  Spinner,
  useToast,
} from '@chakra-ui/react'
import { outreachApi } from '../services/api'

export default function Campaigns() {
  const [outreach, setOutreach] = useState([])
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  useEffect(() => {
    fetchOutreach()
  }, [])

  const fetchOutreach = async () => {
    try {
      const response = await outreachApi.getAll()
      const data = response.data
      setOutreach(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error fetching outreach:', error)
      setOutreach([])
      toast({
        title: 'Error loading campaigns',
        description: error.message || 'Failed to load campaigns',
        status: 'error',
        duration: 3000,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (id) => {
    try {
      await outreachApi.approve(id)
      toast({
        title: 'Campaign approved',
        description: 'Outreach message has been sent',
        status: 'success',
        duration: 3000,
      })
      fetchOutreach()
    } catch (error) {
      console.error('Error approving:', error)
      toast({
        title: 'Approval failed',
        description: error.message,
        status: 'error',
        duration: 3000,
      })
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      pending: 'orange',
      approved: 'blue',
      sent: 'green',
      failed: 'red',
      responded: 'purple',
    }
    return colors[status] || 'gray'
  }

  if (loading) {
    return (
      <Center h="80vh">
        <Spinner size="xl" color="brand.500" />
      </Center>
    )
  }

  return (
    <Container maxW="1400px" py={8}>
      <HStack justify="space-between" mb={6}>
        <Heading>Outreach Campaigns</Heading>
        <Button colorScheme="brand">Create Campaign</Button>
      </HStack>

      {outreach.length === 0 ? (
        <Center h="400px">
          <Box textAlign="center">
            <Text fontSize="lg" color="gray.500" mb={4}>
              No campaigns yet
            </Text>
            <Text color="gray.400">
              Create your first outreach campaign to start connecting with dealers
            </Text>
          </Box>
        </Center>
      ) : (
        <VStack spacing={4} align="stretch">
          {outreach.map((attempt) => (
            <Card key={attempt.id}>
              <CardBody>
                <HStack justify="space-between">
                  <VStack align="start" spacing={1} flex="1">
                    <Text fontWeight="bold">{attempt.subject || 'Outreach Message'}</Text>
                    <Text fontSize="sm" color="gray.600">
                      Method: {attempt.method} • Dealer ID: {attempt.dealer_id}
                    </Text>
                  </VStack>
                  <HStack>
                    <Badge colorScheme={getStatusColor(attempt.status)} fontSize="sm">
                      {attempt.status}
                    </Badge>
                    {attempt.status === 'pending' && (
                      <Button size="sm" colorScheme="green" onClick={() => handleApprove(attempt.id)}>
                        Approve & Send
                      </Button>
                    )}
                  </HStack>
                </HStack>
              </CardBody>
            </Card>
          ))}
        </VStack>
      )}
    </Container>
  )
}
