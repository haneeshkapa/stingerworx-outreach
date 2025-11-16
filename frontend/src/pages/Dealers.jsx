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
} from '@chakra-ui/react'
import { dealersApi } from '../services/api'

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
    <Container maxW="1400px" py={8}>
      <HStack justify="space-between" mb={6}>
        <Heading>Dealer Directory</Heading>
        <Menu>
          <MenuButton as={Button} colorScheme="brand" isLoading={importing}>
            Import Dealers ▾
          </MenuButton>
          <MenuList>
            <MenuItem onClick={() => handleImport('TX')}>Texas</MenuItem>
            <MenuItem onClick={() => handleImport('FL')}>Florida</MenuItem>
            <MenuItem onClick={() => handleImport('GA')}>Georgia</MenuItem>
            <MenuItem onClick={() => handleImport('AZ')}>Arizona</MenuItem>
            <MenuItem onClick={() => handleImport('NC')}>North Carolina</MenuItem>
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
