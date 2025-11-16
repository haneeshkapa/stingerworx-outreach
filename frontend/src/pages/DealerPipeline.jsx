import { useEffect, useState } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  Spinner,
  Center,
  Button,
  HStack,
  VStack,
  Badge,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  SimpleGrid,
  Card,
  CardBody,
  Input,
  Select,
  Grid,
  GridItem,
  InputGroup,
  InputLeftElement,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react'
import { FaSearch, FaExternalLinkAlt } from 'react-icons/fa'
import { dealersApi } from '../services/api'
import { useNavigate } from 'react-router-dom'
import ActivitySidebar from '../components/ActivitySidebar'

export default function DealerPipeline() {
  const [dealers, setDealers] = useState([])
  const [filteredDealers, setFilteredDealers] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [stateFilter, setStateFilter] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchDealers()
    const interval = setInterval(fetchDealers, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    applyFilters()
  }, [dealers, searchTerm, stateFilter])

  const fetchDealers = async () => {
    try {
      const response = await dealersApi.getAll()
      const data = response.data
      setDealers(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error fetching dealers:', error)
      setDealers([])
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = () => {
    let filtered = dealers

    if (searchTerm) {
      filtered = filtered.filter(d =>
        d.business_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.city?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    if (stateFilter) {
      filtered = filtered.filter(d => d.state === stateFilter)
    }

    setFilteredDealers(filtered)
  }

  const getStats = () => {
    const total = dealers.length
    const discovered = dealers.filter(d => d.status === 'DISCOVERED').length
    const enriched = dealers.filter(d => d.status === 'ENRICHED').length
    const contacted = dealers.filter(d => d.status === 'CONTACTED').length
    const hasClass3 = dealers.filter(d => d.sot_class === 'Class 3 SOT').length

    return { total, discovered, enriched, contacted, hasClass3 }
  }

  const filterByStatus = (status) => {
    return filteredDealers.filter(d => d.status === status)
  }

  const getReadyToContact = () => {
    return filteredDealers.filter(d => d.status === 'ENRICHED' && d.sot_class === 'Class 3 SOT')
  }

  const getStatusBadge = (dealer) => {
    if (dealer.status === 'ENRICHED' && dealer.sot_class === 'Class 3 SOT') {
      return <Badge colorScheme="green">✓ Class 3 Verified</Badge>
    }
    if (dealer.status === 'ENRICHED' && dealer.sot_class === 'No Class 3') {
      return <Badge colorScheme="orange">✗ No Class 3</Badge>
    }
    if (dealer.status === 'ENRICHED') {
      return <Badge colorScheme="blue">Enriched</Badge>
    }
    if (dealer.status === 'CONTACTED') {
      return <Badge colorScheme="purple">Contacted</Badge>
    }
    return <Badge colorScheme="gray">Discovered</Badge>
  }

  const stats = getStats()
  const uniqueStates = [...new Set(dealers.map(d => d.state))].sort()

  if (loading) {
    return (
      <Center h="80vh">
        <Spinner size="xl" color="brand.500" />
      </Center>
    )
  }

  return (
    <Box bg="gray.50" minH="100vh">
      <Container maxW="1600px" py={8}>
        <Grid templateColumns={{ base: '1fr', lg: '1fr 300px' }} gap={6}>
          <GridItem>
            <VStack align="stretch" spacing={6}>
              <HStack justify="space-between">
                <Box>
                  <Heading size="lg" mb={2}>Dealer Pipeline</Heading>
                  <Text color="gray.600" fontSize="sm">
                    Track dealers through discovery, enrichment, and outreach stages
                  </Text>
                </Box>
                <Button colorScheme="brand" onClick={() => navigate('/dealers/import')}>
                  + Import Dealers
                </Button>
              </HStack>

              <SimpleGrid columns={{ base: 2, md: 5 }} spacing={4}>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Total Dealers</StatLabel>
                      <StatNumber>{stats.total}</StatNumber>
                    </Stat>
                  </CardBody>
                </Card>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Discovered</StatLabel>
                      <StatNumber>{stats.discovered}</StatNumber>
                      <StatHelpText>Pending AI analysis</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Enriched</StatLabel>
                      <StatNumber>{stats.enriched}</StatNumber>
                      <StatHelpText>Website found</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Class 3 Verified</StatLabel>
                      <StatNumber color="green.600">{stats.hasClass3}</StatNumber>
                      <StatHelpText>AI confirmed</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Contacted</StatLabel>
                      <StatNumber>{stats.contacted}</StatNumber>
                      <StatHelpText>Outreach sent</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
              </SimpleGrid>

              <HStack spacing={4}>
                <InputGroup flex={1}>
                  <InputLeftElement>
                    <FaSearch color="gray" />
                  </InputLeftElement>
                  <Input
                    placeholder="Search dealers by name or city..."
                    bg="white"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </InputGroup>
                <Select
                  placeholder="All States"
                  bg="white"
                  w="200px"
                  value={stateFilter}
                  onChange={(e) => setStateFilter(e.target.value)}
                >
                  {uniqueStates.map(state => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </Select>
              </HStack>

              <Tabs colorScheme="brand" variant="enclosed">
                <TabList>
                  <Tab>All ({filteredDealers.length})</Tab>
                  <Tab>Discovered ({filterByStatus('DISCOVERED').length})</Tab>
                  <Tab>Enriched ({filterByStatus('ENRICHED').length})</Tab>
                  <Tab>Ready to Contact ({getReadyToContact().length})</Tab>
                  <Tab>Contacted ({filterByStatus('CONTACTED').length})</Tab>
                </TabList>

                <TabPanels>
                  <TabPanel>
                    <DealerGrid dealers={filteredDealers} getStatusBadge={getStatusBadge} />
                  </TabPanel>
                  <TabPanel>
                    <DealerGrid dealers={filterByStatus('DISCOVERED')} getStatusBadge={getStatusBadge} />
                  </TabPanel>
                  <TabPanel>
                    <DealerGrid dealers={filterByStatus('ENRICHED')} getStatusBadge={getStatusBadge} />
                  </TabPanel>
                  <TabPanel>
                    <DealerGrid 
                      dealers={getReadyToContact()} 
                      getStatusBadge={getStatusBadge} 
                    />
                  </TabPanel>
                  <TabPanel>
                    <DealerGrid dealers={filterByStatus('CONTACTED')} getStatusBadge={getStatusBadge} />
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </VStack>
          </GridItem>

          <GridItem display={{ base: 'none', lg: 'block' }}>
            <ActivitySidebar />
          </GridItem>
        </Grid>
      </Container>
    </Box>
  )
}

function DealerGrid({ dealers, getStatusBadge }) {
  if (dealers.length === 0) {
    return (
      <Center h="300px">
        <Text color="gray.500">No dealers in this stage</Text>
      </Center>
    )
  }

  return (
    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
      {dealers.slice(0, 100).map((dealer) => (
        <Card key={dealer.id} size="sm">
          <CardBody>
            <VStack align="stretch" spacing={2}>
              <HStack justify="space-between">
                <Text fontWeight="bold" fontSize="md">
                  {dealer.business_name}
                </Text>
                {getStatusBadge(dealer)}
              </HStack>
              
              <Text fontSize="sm" color="gray.600">
                📍 {dealer.city}, {dealer.state}
              </Text>
              
              {dealer.phone && (
                <Text fontSize="sm" color="gray.600">
                  📞 {dealer.phone}
                </Text>
              )}
              
              {dealer.website && (
                <HStack>
                  <FaExternalLinkAlt color="var(--chakra-colors-brand-500)" />
                  <Text
                    fontSize="sm"
                    color="brand.500"
                    as="a"
                    href={dealer.website}
                    target="_blank"
                    _hover={{ textDecoration: 'underline' }}
                  >
                    {dealer.website.replace('https://', '').replace('http://', '')}
                  </Text>
                </HStack>
              )}

              {dealer.sot_class && (
                <Text fontSize="xs" color="gray.500">
                  {dealer.sot_class}
                </Text>
              )}
            </VStack>
          </CardBody>
        </Card>
      ))}
    </SimpleGrid>
  )
}
