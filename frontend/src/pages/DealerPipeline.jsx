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
  Tooltip,
  Wrap,
  WrapItem,
  Link,
  IconButton,
  useDisclosure,
} from '@chakra-ui/react'
import { FaSearch, FaExternalLinkAlt, FaEnvelope, FaPhone, FaWpforms, FaInfoCircle } from 'react-icons/fa'
import { 
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Divider,
  Table,
  Tbody,
  Tr,
  Td,
  Code,
} from '@chakra-ui/react'
import { dealersApi, statsApi } from '../services/api'
import { useNavigate } from 'react-router-dom'
import ActivitySidebar from '../components/ActivitySidebar'

export default function DealerPipeline() {
  const [dealers, setDealers] = useState([])
  const [filteredDealers, setFilteredDealers] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [stateFilter, setStateFilter] = useState('')
  const [apiStats, setApiStats] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchDealers()
    fetchStats()
    const interval = setInterval(() => {
      fetchDealers()
      fetchStats()
    }, 5000)
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

  const fetchStats = async () => {
    try {
      const response = await statsApi.get()
      setApiStats(response.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
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
  const uniqueStates = apiStats?.state_breakdown 
    ? Object.keys(apiStats.state_breakdown).sort() 
    : [...new Set(dealers.map(d => d.state))].sort()

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
                      <StatNumber>{apiStats?.total_dealers || stats.total}</StatNumber>
                    </Stat>
                  </CardBody>
                </Card>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Discovered</StatLabel>
                      <StatNumber>{apiStats?.discovered_count || stats.discovered}</StatNumber>
                      <StatHelpText>Pending AI analysis</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Enriched</StatLabel>
                      <StatNumber>{apiStats?.enriched_count || stats.enriched}</StatNumber>
                      <StatHelpText>Website found</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Class 3 Verified</StatLabel>
                      <StatNumber color="green.600">{apiStats?.class3_verified || stats.hasClass3}</StatNumber>
                      <StatHelpText>AI confirmed</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
                <Card>
                  <CardBody>
                    <Stat size="sm">
                      <StatLabel>Contacted</StatLabel>
                      <StatNumber>{apiStats?.contacted_dealers || stats.contacted}</StatNumber>
                      <StatHelpText>Outreach sent</StatHelpText>
                    </Stat>
                  </CardBody>
                </Card>
              </SimpleGrid>

              <Card>
                <CardBody>
                  <HStack justify="space-between" mb={3}>
                    <Heading size="sm">Imported States</Heading>
                    <Badge colorScheme="blue">{uniqueStates.length} states</Badge>
                  </HStack>
                  <Wrap spacing={2}>
                    {uniqueStates.map(state => {
                      const stateCount = apiStats?.state_breakdown?.[state] || dealers.filter(d => d.state === state).length
                      const class3Count = dealers.filter(d => d.state === state && d.sot_class === 'Class 3 SOT').length
                      return (
                        <WrapItem key={state}>
                          <Tooltip label={`${stateCount} dealers, ${class3Count} Class 3 verified`}>
                            <Badge 
                              colorScheme={class3Count > 0 ? 'green' : 'gray'}
                              fontSize="sm"
                              px={3}
                              py={1}
                              cursor="pointer"
                              onClick={() => setStateFilter(state)}
                            >
                              {state} ({stateCount})
                            </Badge>
                          </Tooltip>
                        </WrapItem>
                      )
                    })}
                  </Wrap>
                </CardBody>
              </Card>

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
  const [selectedDealer, setSelectedDealer] = useState(null)
  
  if (dealers.length === 0) {
    return (
      <Center h="300px">
        <Text color="gray.500">No dealers in this stage</Text>
      </Center>
    )
  }

  const getConfidence = (dealer) => {
    try {
      const extraData = typeof dealer.extra_data === 'string' 
        ? JSON.parse(dealer.extra_data) 
        : dealer.extra_data
      const rawConfidence = extraData?.class3_confidence
      if (rawConfidence === null || rawConfidence === undefined) return null
      const numConfidence = Number(rawConfidence)
      return Number.isNaN(numConfidence) ? null : numConfidence
    } catch {
      return null
    }
  }

  return (
    <>
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
        {dealers.slice(0, 100).map((dealer) => {
          const confidence = getConfidence(dealer)
          
          return (
            <Card 
              key={dealer.id} 
              size="sm"
              cursor="pointer"
              _hover={{ shadow: 'md', borderColor: 'brand.300' }}
              onClick={() => setSelectedDealer(dealer)}
            >
              <CardBody>
                <VStack align="stretch" spacing={3}>
                  <HStack justify="space-between" align="start">
                    <VStack align="start" spacing={1} flex={1}>
                      <Text fontWeight="bold" fontSize="md">
                        {dealer.business_name}
                      </Text>
                      <Text fontSize="sm" color="gray.600">
                        📍 {dealer.city}, {dealer.state}
                      </Text>
                    </VStack>
                    <Tooltip label="Click for details">
                      <IconButton
                        icon={<FaInfoCircle />}
                        size="xs"
                        variant="ghost"
                        colorScheme="gray"
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedDealer(dealer)
                        }}
                      />
                    </Tooltip>
                  </HStack>

                  <Wrap spacing={2}>
                    {getStatusBadge(dealer)}
                    
                    {dealer.sot_class && dealer.sot_class !== 'Unknown' && (
                      <WrapItem>
                        <Tooltip label={`AI Confidence: ${confidence !== null ? confidence.toFixed(0) + '%' : 'N/A'}`}>
                          <Badge 
                            colorScheme={dealer.sot_class === 'Class 3 SOT' ? 'green' : 'orange'}
                            display="flex"
                            alignItems="center"
                            gap={1}
                          >
                            {dealer.sot_class === 'Class 3 SOT' ? '✓' : '✗'} Class 3
                            {confidence !== null && ` ${confidence.toFixed(0)}%`}
                          </Badge>
                        </Tooltip>
                      </WrapItem>
                    )}
                    
                    {dealer.email && (
                      <WrapItem>
                        <Tooltip label={dealer.email}>
                          <Badge colorScheme="blue" display="flex" alignItems="center" gap={1}>
                            <FaEnvelope /> Email
                          </Badge>
                        </Tooltip>
                      </WrapItem>
                    )}
                    
                    {dealer.phone && (
                      <WrapItem>
                        <Tooltip label={dealer.phone}>
                          <Badge colorScheme="purple" display="flex" alignItems="center" gap={1}>
                            <FaPhone /> Phone
                          </Badge>
                        </Tooltip>
                      </WrapItem>
                    )}
                    
                    {dealer.contact_form_url && (
                      <WrapItem>
                        <Link href={dealer.contact_form_url} isExternal onClick={(e) => e.stopPropagation()}>
                          <Badge colorScheme="teal" display="flex" alignItems="center" gap={1} cursor="pointer">
                            <FaWpforms /> Contact Page
                          </Badge>
                        </Link>
                      </WrapItem>
                    )}
                  </Wrap>
                  
                  {dealer.website && (
                    <HStack spacing={2} fontSize="sm">
                      <FaExternalLinkAlt color="var(--chakra-colors-gray-500)" size={12} />
                      <Link
                        color="brand.500"
                        href={dealer.website}
                        isExternal
                        onClick={(e) => e.stopPropagation()}
                        _hover={{ textDecoration: 'underline' }}
                        noOfLines={1}
                      >
                        {dealer.website.replace('https://', '').replace('http://', '')}
                      </Link>
                    </HStack>
                  )}
                </VStack>
              </CardBody>
            </Card>
          )
        })}
      </SimpleGrid>

      <DealerDetailModal dealer={selectedDealer} onClose={() => setSelectedDealer(null)} />
    </>
  )
}

function DealerDetailModal({ dealer, onClose }) {
  if (!dealer) return null

  const getExtraData = () => {
    try {
      return typeof dealer.extra_data === 'string' 
        ? JSON.parse(dealer.extra_data) 
        : dealer.extra_data || {}
    } catch {
      return {}
    }
  }

  const extraData = getExtraData()
  const class3Evidence = extraData.class3_evidence || 'No evidence data available'
  
  const getConfidenceValue = () => {
    const rawConfidence = extraData.class3_confidence
    if (rawConfidence === null || rawConfidence === undefined) return null
    const numConfidence = Number(rawConfidence)
    return Number.isNaN(numConfidence) ? null : numConfidence
  }
  
  const confidence = getConfidenceValue()

  return (
    <Modal isOpen={true} onClose={onClose} size="xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <VStack align="start" spacing={1}>
            <Text>{dealer.business_name}</Text>
            <Text fontSize="sm" fontWeight="normal" color="gray.600">
              {dealer.city}, {dealer.state}
            </Text>
          </VStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack align="stretch" spacing={4}>
            <Box>
              <Text fontWeight="bold" mb={2}>Contact Information</Text>
              <Table size="sm" variant="simple">
                <Tbody>
                  {dealer.website && (
                    <Tr>
                      <Td fontWeight="medium" w="140px">Website</Td>
                      <Td>
                        <Link href={dealer.website} isExternal color="brand.500">
                          {dealer.website}
                        </Link>
                      </Td>
                    </Tr>
                  )}
                  {dealer.email && (
                    <Tr>
                      <Td fontWeight="medium">Email</Td>
                      <Td>{dealer.email}</Td>
                    </Tr>
                  )}
                  {dealer.phone && (
                    <Tr>
                      <Td fontWeight="medium">Phone</Td>
                      <Td>{dealer.phone}</Td>
                    </Tr>
                  )}
                  {dealer.contact_form_url && (
                    <Tr>
                      <Td fontWeight="medium">Contact Form</Td>
                      <Td>
                        <Link href={dealer.contact_form_url} isExternal color="brand.500">
                          {dealer.contact_form_url}
                        </Link>
                      </Td>
                    </Tr>
                  )}
                  <Tr>
                    <Td fontWeight="medium">License</Td>
                    <Td>
                      {dealer.license_number || 'N/A'}
                      {dealer.license_type && ` (${dealer.license_type})`}
                    </Td>
                  </Tr>
                </Tbody>
              </Table>
            </Box>

            <Divider />

            <Box>
              <HStack justify="space-between" mb={2}>
                <Text fontWeight="bold">Class 3 SOT Status</Text>
                <Badge 
                  colorScheme={dealer.sot_class === 'Class 3 SOT' ? 'green' : dealer.sot_class === 'No Class 3' ? 'orange' : 'gray'}
                  fontSize="md"
                >
                  {dealer.sot_class || 'Unknown'}
                </Badge>
              </HStack>
              
              {confidence !== null && (
                <Text fontSize="sm" color="gray.600" mb={3}>
                  AI Confidence: <strong>{confidence.toFixed(0)}%</strong>
                </Text>
              )}

              <Box bg="gray.50" p={3} borderRadius="md" maxH="300px" overflowY="auto">
                <Text fontWeight="medium" fontSize="sm" mb={2} color="gray.700">
                  AI Analysis Evidence:
                </Text>
                <Text fontSize="sm" whiteSpace="pre-wrap" color="gray.700">
                  {class3Evidence}
                </Text>
              </Box>
            </Box>

            {extraData && Object.keys(extraData).length > 0 && (
              <>
                <Divider />
                <Box>
                  <Text fontWeight="bold" mb={2}>Additional Data</Text>
                  <Box bg="gray.50" p={3} borderRadius="md" maxH="200px" overflowY="auto">
                    <Code fontSize="xs" display="block" whiteSpace="pre-wrap">
                      {JSON.stringify(extraData, null, 2)}
                    </Code>
                  </Box>
                </Box>
              </>
            )}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  )
}
