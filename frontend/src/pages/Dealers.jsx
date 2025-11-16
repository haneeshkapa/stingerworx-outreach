import { useEffect, useState } from 'react'
import {
  Box,
  Container,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Text,
  Spinner,
  Center,
  Button,
  HStack,
  useToast,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Grid,
  GridItem,
} from '@chakra-ui/react'
import { dealersApi } from '../services/api'
import ActivityFeed from '../components/ActivityFeed'

export default function Dealers() {
  const [dealers, setDealers] = useState([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const toast = useToast()

  useEffect(() => {
    fetchDealers()
  }, [])

  const fetchDealers = async () => {
    try {
      const response = await dealersApi.getAll()
      const data = response.data
      setDealers(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error fetching dealers:', error)
      setDealers([])
      toast({
        title: 'Error loading dealers',
        description: error.message || 'Failed to load dealers',
        status: 'error',
        duration: 3000,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async (state) => {
    setImporting(true)
    try {
      await dealersApi.importFromState(state)
      toast({
        title: 'Import started',
        description: `Importing dealers from ${state}...`,
        status: 'info',
        duration: 3000,
      })
      
      setTimeout(() => {
        fetchDealers()
      }, 2000)
    } catch (error) {
      console.error('Error importing:', error)
      toast({
        title: 'Import failed',
        description: error.message,
        status: 'error',
        duration: 3000,
      })
    } finally {
      setImporting(false)
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      discovered: 'gray',
      enriched: 'blue',
      contacted: 'purple',
      responded: 'green',
      interested: 'green',
      not_interested: 'red',
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
    <Container maxW="1600px" py={8}>
      <Grid templateColumns="3fr 2fr" gap={6} mb={6}>
        <GridItem>
          <Heading>Dealer Directory</Heading>
        </GridItem>
        <GridItem>
          <ActivityFeed autoRefresh={true} />
        </GridItem>
      </Grid>
      
      <HStack justify="space-between" mb={6}>
        <Box></Box>
        <Menu>
          <MenuButton as={Button} colorScheme="brand" isLoading={importing}>
            Import Dealers ▾
          </MenuButton>
          <MenuList maxH="400px" overflowY="auto">
            <MenuItem onClick={() => handleImport('AL')}>Alabama</MenuItem>
            <MenuItem onClick={() => handleImport('AK')}>Alaska</MenuItem>
            <MenuItem onClick={() => handleImport('AZ')}>Arizona</MenuItem>
            <MenuItem onClick={() => handleImport('AR')}>Arkansas</MenuItem>
            <MenuItem onClick={() => handleImport('CA')}>California</MenuItem>
            <MenuItem onClick={() => handleImport('CO')}>Colorado</MenuItem>
            <MenuItem onClick={() => handleImport('CT')}>Connecticut</MenuItem>
            <MenuItem onClick={() => handleImport('DE')}>Delaware</MenuItem>
            <MenuItem onClick={() => handleImport('FL')}>Florida</MenuItem>
            <MenuItem onClick={() => handleImport('GA')}>Georgia</MenuItem>
            <MenuItem onClick={() => handleImport('HI')}>Hawaii</MenuItem>
            <MenuItem onClick={() => handleImport('ID')}>Idaho</MenuItem>
            <MenuItem onClick={() => handleImport('IL')}>Illinois</MenuItem>
            <MenuItem onClick={() => handleImport('IN')}>Indiana</MenuItem>
            <MenuItem onClick={() => handleImport('IA')}>Iowa</MenuItem>
            <MenuItem onClick={() => handleImport('KS')}>Kansas</MenuItem>
            <MenuItem onClick={() => handleImport('KY')}>Kentucky</MenuItem>
            <MenuItem onClick={() => handleImport('LA')}>Louisiana</MenuItem>
            <MenuItem onClick={() => handleImport('ME')}>Maine</MenuItem>
            <MenuItem onClick={() => handleImport('MD')}>Maryland</MenuItem>
            <MenuItem onClick={() => handleImport('MA')}>Massachusetts</MenuItem>
            <MenuItem onClick={() => handleImport('MI')}>Michigan</MenuItem>
            <MenuItem onClick={() => handleImport('MN')}>Minnesota</MenuItem>
            <MenuItem onClick={() => handleImport('MS')}>Mississippi</MenuItem>
            <MenuItem onClick={() => handleImport('MO')}>Missouri</MenuItem>
            <MenuItem onClick={() => handleImport('MT')}>Montana</MenuItem>
            <MenuItem onClick={() => handleImport('NE')}>Nebraska</MenuItem>
            <MenuItem onClick={() => handleImport('NV')}>Nevada</MenuItem>
            <MenuItem onClick={() => handleImport('NH')}>New Hampshire</MenuItem>
            <MenuItem onClick={() => handleImport('NJ')}>New Jersey</MenuItem>
            <MenuItem onClick={() => handleImport('NM')}>New Mexico</MenuItem>
            <MenuItem onClick={() => handleImport('NY')}>New York</MenuItem>
            <MenuItem onClick={() => handleImport('NC')}>North Carolina</MenuItem>
            <MenuItem onClick={() => handleImport('ND')}>North Dakota</MenuItem>
            <MenuItem onClick={() => handleImport('OH')}>Ohio</MenuItem>
            <MenuItem onClick={() => handleImport('OK')}>Oklahoma</MenuItem>
            <MenuItem onClick={() => handleImport('OR')}>Oregon</MenuItem>
            <MenuItem onClick={() => handleImport('PA')}>Pennsylvania</MenuItem>
            <MenuItem onClick={() => handleImport('RI')}>Rhode Island</MenuItem>
            <MenuItem onClick={() => handleImport('SC')}>South Carolina</MenuItem>
            <MenuItem onClick={() => handleImport('SD')}>South Dakota</MenuItem>
            <MenuItem onClick={() => handleImport('TN')}>Tennessee</MenuItem>
            <MenuItem onClick={() => handleImport('TX')}>Texas</MenuItem>
            <MenuItem onClick={() => handleImport('UT')}>Utah</MenuItem>
            <MenuItem onClick={() => handleImport('VT')}>Vermont</MenuItem>
            <MenuItem onClick={() => handleImport('VA')}>Virginia</MenuItem>
            <MenuItem onClick={() => handleImport('WA')}>Washington</MenuItem>
            <MenuItem onClick={() => handleImport('WV')}>West Virginia</MenuItem>
            <MenuItem onClick={() => handleImport('WI')}>Wisconsin</MenuItem>
            <MenuItem onClick={() => handleImport('WY')}>Wyoming</MenuItem>
          </MenuList>
        </Menu>
      </HStack>

      {dealers.length === 0 ? (
        <Center h="400px">
          <Box textAlign="center">
            <Text fontSize="lg" color="gray.500" mb={4}>
              No dealers found
            </Text>
            <Text color="gray.400">
              Import dealers from ATF lists or web scraping to get started
            </Text>
          </Box>
        </Center>
      ) : (
        <Box bg="white" borderRadius="lg" shadow="sm" overflow="hidden">
          <Table variant="simple">
            <Thead bg="gray.50">
              <Tr>
                <Th>Business Name</Th>
                <Th>Location</Th>
                <Th>Phone</Th>
                <Th>Website</Th>
                <Th>Status</Th>
              </Tr>
            </Thead>
            <Tbody>
              {dealers.map((dealer) => (
                <Tr key={dealer.id}>
                  <Td fontWeight="medium">{dealer.business_name}</Td>
                  <Td>
                    {dealer.city}, {dealer.state}
                  </Td>
                  <Td>{dealer.phone || '-'}</Td>
                  <Td>
                    {dealer.website ? (
                      <Text color="brand.600" fontSize="sm">
                        {dealer.website}
                      </Text>
                    ) : (
                      '-'
                    )}
                  </Td>
                  <Td>
                    <Badge colorScheme={getStatusColor(dealer.status)}>
                      {dealer.status}
                    </Badge>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}
    </Container>
  )
}
