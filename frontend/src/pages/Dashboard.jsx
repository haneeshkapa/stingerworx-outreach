import { useEffect, useState } from 'react'
import {
  Box,
  Container,
  Heading,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Card,
  CardBody,
  Text,
  Spinner,
  Center,
} from '@chakra-ui/react'
import { statsApi } from '../services/api'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await statsApi.get()
      setStats(response.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setLoading(false)
    }
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
      <Heading mb={6}>Dashboard</Heading>
      
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Total Dealers</StatLabel>
              <StatNumber color="brand.600">{stats?.total_dealers || 0}</StatNumber>
              <StatHelpText>In database</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Contacted</StatLabel>
              <StatNumber color="green.600">{stats?.contacted_dealers || 0}</StatNumber>
              <StatHelpText>Dealers reached</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Interested Leads</StatLabel>
              <StatNumber color="purple.600">{stats?.interested_leads || 0}</StatNumber>
              <StatHelpText>Positive responses</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>Pending Approvals</StatLabel>
              <StatNumber color="orange.600">{stats?.pending_approvals || 0}</StatNumber>
              <StatHelpText>Awaiting review</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <Card>
        <CardBody>
          <Heading size="md" mb={4}>Welcome to Stingerworx Dealer Outreach System</Heading>
          <Text color="gray.600">
            This AI-powered platform helps you discover and connect with Class 3 SOT dealers across the United States.
            Navigate to the Dealers page to view your prospect list, or check Campaigns to manage outreach efforts.
          </Text>
        </CardBody>
      </Card>
    </Container>
  )
}
